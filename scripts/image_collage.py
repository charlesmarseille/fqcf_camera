#!/usr/bin/env python3
import os
import glob
from datetime import datetime
from flask import Flask, send_from_directory, render_template_string, request
import fnmatch

# Configuration
PI_IDS = list(range(7))
IMAGE_EXT = ".jpg"
IMAGE_ROOT = "/mnt/ssd/backup"
IMAGE_PATTERN = "pi{pi_id}_*_*.jpg"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FQCF Tunnel Camera App</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <style>
        body { background: #222; color: #fff; font-family: sans-serif; }
        .tabs { display: flex; border-bottom: 2px solid #444; margin-bottom: 10px; }
        .tab { padding: 10px 20px; cursor: pointer; background: #333; border: none; color: #fff; }
        .tab.active { background: #555; border-bottom: 2px solid #fff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .collage { display: flex; flex-direction: row; justify-content: center; align-items: center; margin-top: 20px; }
        .side { display: flex; flex-direction: column; gap: 10px; }
        .center { margin: 0 40px; }
        img { max-width: 200px; max-height: 150px; border: 2px solid #fff; background: #111; }
        .label { text-align: center; font-size: 1.1em; margin-bottom: 4px; }
        .image-id-list { max-height: 300px; overflow-y: auto; background: #222; border: 1px solid #444; margin-bottom: 10px; }
        .image-id-item { padding: 6px 12px; cursor: pointer; }
        .image-id-item.selected { background: #444; color: #fff; font-weight: bold; }
        .image-id-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .image-id-table th { background: #333; padding: 8px 4px; border: 1px solid #444; text-align: center; position: sticky; top: 0; }
        .image-id-table td { padding: 6px 4px; border: 1px solid #444; text-align: center; }
        .image-id-table tr { cursor: pointer; }
        .image-id-table tr.selected { background: #444; font-weight: bold; }
        .image-id-table tr:hover { background: #333; }
        .calendar-container { margin-bottom: 10px; }
        .calendar-form { display: flex; gap: 8px; align-items: center; }
        .calendar-form input { padding: 6px; }
    </style>
</head>
<body>
    <div class="tabs">
        <button class="tab" hx-get="/tab/collage" hx-target="#tab-contents" hx-swap="innerHTML" hx-push-url="true">Collage</button>
        <button class="tab" hx-get="/tab/about" hx-target="#tab-contents" hx-swap="innerHTML" hx-push-url="true">About</button>
        <button id="live-view-btn" class="tab" hx-get="/toggle_live_view" hx-target="#tab-contents" hx-swap="innerHTML" style="margin-left: auto; background: #444;">Live View</button>
    </div>
    <div id="tab-contents">
        {{ collage_tab_content|safe }}
    </div>
    <script>
        document.querySelectorAll('.tab')[0].classList.add('active');
    </script>
</body>
</html>
"""

COLLAGE_TAB_TEMPLATE = """
<div class="tab-content active">
    <div class="calendar-container">
        <form class="calendar-form" 
              hx-get="/image_ids" 
              hx-target="#image-id-list" 
              hx-swap="innerHTML"
              hx-indicator="#image-id-list-indicator">
            <label>Start:</label>
            <input type="text" name="start" placeholder="YYYYMMDD" value="{{start or default_date or ''}}" pattern="\\d{8}" maxlength="8" size="8" required>
            <label>End:</label>
            <input type="text" name="end" placeholder="YYYYMMDD" value="{{end or default_date or ''}}" pattern="\\d{8}" maxlength="8" size="8" required>
            <label>Entries:</label>
            <input type="number" name="limit" placeholder="100" value="{{limit or '100'}}" min="1" max="1000" size="4">
            <button type="submit">Filter</button>
        </form>
    </div>
    <div style="text-align:center;">
        <div id="image-id-list-indicator" class="htmx-indicator" style="display:none; margin: 10px 0;">
            <svg width="40" height="40" viewBox="0 0 40 40" style="animation: spin 1s linear infinite;">
                <circle cx="20" cy="20" r="16" stroke="#0f0" stroke-width="4" fill="none" stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="60"/>
            </svg>
        </div>
    </div>
    <div id="image-id-list" class="image-id-list" 
         hx-get="/image_ids{% if start and end %}?start={{start}}&end={{end}}{% endif %}{% if limit %}&limit={{limit}}{% endif %}" 
         hx-trigger="load" hx-swap="innerHTML"></div>
    <div id="collage-container" hx-get="/collage{% if selected_image_id %}?image_id={{selected_image_id}}{% endif %}" hx-trigger="load" hx-swap="innerHTML"></div>
    <style>
        @keyframes spin {
            100% { transform: rotate(360deg); }
        }
        .htmx-indicator {
            display: none;
        }
        .htmx-request .htmx-indicator,
        .htmx-indicator.htmx-request {
            display: inline-block !important;
        }
    </style>
    <script>
        // Highlight selected row on click
        document.addEventListener('click', function(e) {
            let tr = e.target.closest('tr');
            if (tr && tr.parentElement && tr.parentElement.parentElement && tr.parentElement.parentElement.classList.contains('image-id-table')) {
                document.querySelectorAll('.image-id-table tr.selected').forEach(function(row) {
                    row.classList.remove('selected');
                });
                tr.classList.add('selected');
            }
        });
    </script>
</div>
"""

ABOUT_TAB_TEMPLATE = """
<div class="tab-content active">
    <h2>About</h2>
    <p>Pi Collage Viewer for image selection and comparison.</p>
</div>
"""

LIVE_VIEW_TAB_TEMPLATE = """
<div class="tab-content active">
    <div style="margin-bottom: 10px;">
        <button hx-get="/tab/collage" hx-target="#tab-contents" hx-swap="innerHTML" style="padding: 8px 16px; background: #666; color: #fff; border: none; cursor: pointer;">Exit Live View</button>
        <span style="margin-left: 10px; color: #0f0; font-weight: bold;">● LIVE - Updates every 5 seconds</span>
    </div>
    <div style="text-align: center; margin-bottom: 10px;">
        <span style="color: #fff; font-size: 1.2em;">Current Image ID: </span>
        <span id="live-image-id" style="color: #0f0; font-weight: bold; font-size: 1.2em;" 
              hx-get="/live_current_image_id" 
              hx-trigger="load, every 5s" 
              hx-swap="innerHTML"></span>
    </div>
    <div id="live-collage-container" 
         hx-get="/live_collage" 
         hx-trigger="load, every 5s" 
         hx-swap="innerHTML"></div>
</div>
"""

COLLAGE_TEMPLATE = """
<div class="collage" style="flex-direction: row; gap: 0; margin-top: 10px;">
    {% for i in [1,2,3,0,4,5,6] %}
    <div class="side" style="flex-direction: column; align-items: center; margin: 0 2px; padding: 0;">
        <div class="label" style="margin-bottom: 2px;">Pi {{i}}</div>
        {% if images[i] %}
        <img src="/image_file/{{images[i]}}" alt="Pi {{i}}" style="transform: rotate(-90deg); margin: 0; border-width: 1px; cursor: pointer;"
             onclick="window.open('/image_fullscreen/{{images[i]}}', '_blank')">
        {% else %}
        <div style="width:200px;height:150px;background:#333;color:#888;display:flex;align-items:center;justify-content:center;margin:0;">No image</div>
        {% endif %}
    </div>
    {% endfor %}
</div>
"""

IMAGE_ID_ITEM_TEMPLATE = """
<table class="image-id-table">
    <thead>
        <tr>
            <th>Image ID</th>
            <th>DateTime (Pi0)</th>
            <th>Pi1</th>
            <th>Pi2</th>
            <th>Pi3</th>
            <th>Pi4</th>
            <th>Pi5</th>
            <th>Pi6</th>
        </tr>
    </thead>
    <tbody>
        {% for item in image_data %}
        <tr class="{% if item.image_id == selected_image_id %}selected{% endif %}"
            hx-get="/collage?image_id={{item.image_id}}"
            hx-target="#collage-container"
            hx-swap="innerHTML"
            hx-vals='{"selected_image_id":"{{item.image_id}}"}'
            hx-push-url="true">
            <td>{{item.image_id}}</td>
            <td>{{item.datetime}}</td>
            <td>{{item.offsets[1] or '-'}}</td>
            <td>{{item.offsets[2] or '-'}}</td>
            <td>{{item.offsets[3] or '-'}}</td>
            <td>{{item.offsets[4] or '-'}}</td>
            <td>{{item.offsets[5] or '-'}}</td>
            <td>{{item.offsets[6] or '-'}}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
"""

def get_image_files(pi_id, start_date=None, end_date=None):
    """
    Fast version: uses os.scandir and string checks instead of glob and repeated splits.
    Uses list comprehension for speed.
    """
    dir_path = os.path.join(IMAGE_ROOT, str(pi_id))
    if not os.path.isdir(dir_path):
        return []
    prefix = f"pi{pi_id}_"
    suffix = IMAGE_EXT

    try:
        with os.scandir(dir_path) as it:
            files = [
                (
                    parts[1],  # image_id
                    parts[2],  # date_str
                    entry.name
                )
                for entry in it
                if entry.is_file()
                and entry.name.startswith(prefix)
                and entry.name.endswith(suffix)
                and (len((parts := entry.name.split('_'))) >= 4)
                and (
                    not (start_date and end_date)
                    or (start_date <= parts[2] <= end_date)
                )
            ]
        return files
    except FileNotFoundError:
        return []

def parse_filename_datetime(filename):
    """Parse datetime from filename format: pi0_123_20241225_123045678.jpg"""
    try:
        parts = filename.split('_')
        if len(parts) < 4:
            return None
        date_part = parts[2]  # 20241225
        time_part = parts[3].split('.')[0]  # 123045678
        
        # Parse date: YYYYMMDD
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        
        # Parse time: HHMMSSMMM (hour, minute, second, millisecond)
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        millisecond = int(time_part[6:9]) if len(time_part) > 6 else 0
        
        return datetime(year, month, day, hour, minute, second, millisecond * 1000)
    except (ValueError, IndexError):
        return None

def get_image_data_with_offsets(start_date=None, end_date=None, limit=None):
    """Get image data with datetime and offsets for each Pi"""
    image_ids = get_all_image_ids(start_date, end_date)
    image_data = []
    
    # Sort image_ids in reverse order and apply limit early for performance
    sorted_image_ids = sorted(image_ids, reverse=True)
    if limit:
        sorted_image_ids = sorted_image_ids[:limit]
    
    for image_id in sorted_image_ids:
        # Get Pi0 datetime as reference
        pi0_files = get_image_files(0, start_date, end_date)
        pi0_datetime = None
        pi0_filename = None
        
        for img_id, date_str, filename in pi0_files:
            if img_id == image_id:
                pi0_filename = filename
                pi0_datetime = parse_filename_datetime(filename)
                break
        
        if not pi0_datetime:
            continue
            
        # Format datetime for display
        datetime_str = pi0_datetime.strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]  # Remove last 3 digits of microseconds
        
        # Calculate offsets for other Pis
        offsets = {}
        for pi_id in range(1, 7):
            pi_files = get_image_files(pi_id, start_date, end_date)
            pi_datetime = None
            
            for img_id, date_str, filename in pi_files:
                if img_id == image_id:
                    pi_datetime = parse_filename_datetime(filename)
                    break
            
            if pi_datetime and pi0_datetime:
                offset_ms = int((pi_datetime - pi0_datetime).total_seconds() * 1000)
                offsets[pi_id] = f"{offset_ms:+d}ms"
            else:
                offsets[pi_id] = None
        
        image_data.append({
            'image_id': image_id,
            'datetime': datetime_str,
            'offsets': offsets
        })
    
    return image_data

def get_latest_pi0_date():
    """Get the date from the latest Pi0 image filename"""
    try:
        pi0_files = get_image_files(0)  # Get all Pi0 files
        if not pi0_files:
            return None
        
        # Sort by image_id to get the latest
        pi0_files.sort(key=lambda x: x[0], reverse=True)  # Sort by image_id (index 0)
        latest_file = pi0_files[0]
        date_str = latest_file[1]  # date_str is at index 1
        return date_str
    except:
        return None

def get_all_image_ids(start_date=None, end_date=None):
    image_ids = set()
    for pi_id in PI_IDS:
        files = get_image_files(pi_id, start_date, end_date)
        for image_id, date_str, basename in files:
            image_ids.add(image_id)
    return sorted(image_ids)

def get_images_for_image_id(image_id):
    images = {}
    for pi_id in PI_IDS:
        pattern = os.path.join(IMAGE_ROOT, str(pi_id), f"pi{pi_id}_{image_id}_*{IMAGE_EXT}")
        files = glob.glob(pattern)
        if files:
            files.sort(reverse=True)
            images[pi_id] = f"{pi_id}/{os.path.basename(files[0])}"
        else:
            images[pi_id] = None
    return images

@app.route('/')
def index():
    # Default: show collage tab
    start = request.args.get('start')
    end = request.args.get('end')
    limit = request.args.get('limit', '100')
    selected_image_id = request.args.get('image_id')
    default_date = get_latest_pi0_date()
    
    collage_tab_content = render_template_string(
        COLLAGE_TAB_TEMPLATE,
        start=start,
        end=end,
        limit=limit,
        selected_image_id=selected_image_id,
        default_date=default_date
    )
    return render_template_string(
        HTML_TEMPLATE,
        start=start,
        end=end,
        limit=limit,
        selected_image_id=selected_image_id,
        collage_tab_content=collage_tab_content
    )

@app.route('/tab/collage')
def tab_collage():
    start = request.args.get('start')
    end = request.args.get('end')
    limit = request.args.get('limit', '100')
    selected_image_id = request.args.get('image_id')
    default_date = get_latest_pi0_date()
    
    return render_template_string(
        COLLAGE_TAB_TEMPLATE,
        start=start,
        end=end,
        limit=limit,
        selected_image_id=selected_image_id,
        default_date=default_date
    )

@app.route('/tab/about')
def tab_about():
    return render_template_string(ABOUT_TAB_TEMPLATE)

@app.route('/toggle_live_view')
def toggle_live_view():
    return render_template_string(LIVE_VIEW_TAB_TEMPLATE)

@app.route('/live_image_ids')
def live_image_ids():
    image_data = get_image_data_with_offsets()
    selected_image_id = image_data[4]['image_id'] if len(image_data) >= 5 else (image_data[0]['image_id'] if image_data else None)  # 5th latest image ID
    return render_template_string(IMAGE_ID_ITEM_TEMPLATE, image_data=image_data, selected_image_id=selected_image_id)

@app.route('/live_current_image_id')
def live_current_image_id():
    image_data = get_image_data_with_offsets()
    image_id = image_data[4]['image_id'] if len(image_data) >= 5 else (image_data[0]['image_id'] if image_data else "No images")
    return str(image_id)

@app.route('/live_collage')
def live_collage():
    image_data = get_image_data_with_offsets()
    image_id = image_data[4]['image_id'] if len(image_data) >= 5 else (image_data[0]['image_id'] if image_data else None)  # Use 5th latest image ID
    images = get_images_for_image_id(image_id) if image_id else {i: None for i in PI_IDS}
    return render_template_string(COLLAGE_TEMPLATE, images=images)

@app.route('/image_ids')
def image_ids():
    start = request.args.get('start')
    end = request.args.get('end')
    limit = request.args.get('limit')
    selected_image_id = request.args.get('selected_image_id')
    
    # Convert limit to integer if provided
    limit_int = None
    if limit:
        try:
            limit_int = int(limit)
        except ValueError:
            limit_int = 100  # Default fallback
    
    image_data = get_image_data_with_offsets(start, end, limit_int)
    return render_template_string(IMAGE_ID_ITEM_TEMPLATE, image_data=image_data, selected_image_id=selected_image_id)

@app.route('/collage')
def collage():
    image_id = request.args.get('image_id')
    if not image_id:
        ids = get_all_image_ids()
        image_id = ids[-1] if ids else None
    images = get_images_for_image_id(image_id) if image_id else {i: None for i in PI_IDS}
    return render_template_string(COLLAGE_TEMPLATE, images=images)

@app.route('/image_file/<path:filename>')
def image_file(filename):
    pi_id = filename.split('/')[0]
    return send_from_directory(os.path.join(IMAGE_ROOT, pi_id), filename.split('/', 1)[1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)