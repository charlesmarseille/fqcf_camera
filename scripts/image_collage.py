#!/usr/bin/env python3
import os
import glob
from datetime import datetime
from flask import Flask, send_from_directory, render_template_string, request

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
    <title>Pi Collage Viewer</title>
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
        .calendar-container { margin-bottom: 10px; }
        .calendar-form { display: flex; gap: 8px; align-items: center; }
        .calendar-form input { padding: 6px; }
    </style>
</head>
<body>
    <div class="tabs">
        <button class="tab" hx-get="/tab/collage" hx-target="#tab-contents" hx-swap="innerHTML" hx-push-url="true">Collage</button>
        <button class="tab" hx-get="/tab/about" hx-target="#tab-contents" hx-swap="innerHTML" hx-push-url="true">About</button>
    </div>
    <div id="tab-contents">
        {{ collage_tab_content|safe }}
    </div>
    <script>
        // Activate first tab on load (no JS for tab switching, handled by htmx)
        document.querySelectorAll('.tab')[0].classList.add('active');
    </script>
</body>
</html>
"""

COLLAGE_TAB_TEMPLATE = """
<div class="tab-content active">
    <div class="calendar-container">
        <form class="calendar-form" hx-get="/image_ids" hx-target="#image-id-list" hx-swap="innerHTML">
            <label>Start:</label>
            <input type="text" name="start" placeholder="YYYYMMDD" value="{{start or ''}}" pattern="\\d{8}" maxlength="8" size="8" required>
            <label>End:</label>
            <input type="text" name="end" placeholder="YYYYMMDD" value="{{end or ''}}" pattern="\\d{8}" maxlength="8" size="8" required>
            <button type="submit">Filter</button>
        </form>
    </div>
    <div id="image-id-list" class="image-id-list" 
         hx-get="/image_ids{% if start and end %}?start={{start}}&end={{end}}{% endif %}" 
         hx-trigger="load" hx-swap="innerHTML"></div>
    <div id="collage-container" hx-get="/collage{% if selected_image_id %}?image_id={{selected_image_id}}{% endif %}" hx-trigger="load" hx-swap="innerHTML"></div>
</div>
"""

ABOUT_TAB_TEMPLATE = """
<div class="tab-content active">
    <h2>About</h2>
    <p>Pi Collage Viewer for image selection and comparison.</p>
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

# Add this route to serve fullscreen image view
FULLSCREEN_IMAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fullscreen Image</title>
    <style>
        body { margin: 0; background: #111; display: flex; align-items: center; justify-content: center; height: 100vh; }
        img { max-width: 98vw; max-height: 98vh; background: #222; border: 4px solid #fff; transform: rotate(-90deg); }
    </style>
</head>
<body>
    <img src="/image_file/{{ filename }}" alt="Fullscreen Image">
</body>
</html>
"""

@app.route('/image_fullscreen/<path:filename>')
def image_fullscreen(filename):
    return render_template_string(FULLSCREEN_IMAGE_TEMPLATE, filename=filename)

IMAGE_ID_ITEM_TEMPLATE = """
{% for image_id in image_ids %}
<div class="image-id-item {% if image_id == selected_image_id %}selected{% endif %}" 
     hx-get="/collage?image_id={{image_id}}"
     hx-target="#collage-container"
     hx-swap="innerHTML"
     hx-vals='{"selected_image_id":"{{image_id}}"}'
     hx-push-url="true"
     >{{image_id}}</div>
{% endfor %}
"""

def get_image_files(pi_id, start_date=None, end_date=None):
    pattern = os.path.join(IMAGE_ROOT, str(pi_id), f"pi{pi_id}_*_*{IMAGE_EXT}")
    files = glob.glob(pattern)
    result = []
    for f in files:
        basename = os.path.basename(f)
        parts = basename.split('_')
        if len(parts) < 4:
            continue
        image_id = parts[1]
        date_str = parts[2]
        if start_date and end_date:
            if not (start_date <= date_str <= end_date):
                continue
        result.append((image_id, date_str, basename))
    return result

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
    selected_image_id = request.args.get('image_id')
    collage_tab_content = render_template_string(
        COLLAGE_TAB_TEMPLATE,
        start=start,
        end=end,
        selected_image_id=selected_image_id
    )
    return render_template_string(
        HTML_TEMPLATE,
        start=start,
        end=end,
        selected_image_id=selected_image_id,
        collage_tab_content=collage_tab_content
    )

@app.route('/tab/collage')
def tab_collage():
    start = request.args.get('start')
    end = request.args.get('end')
    selected_image_id = request.args.get('image_id')
    return render_template_string(
        COLLAGE_TAB_TEMPLATE,
        start=start,
        end=end,
        selected_image_id=selected_image_id
    )

@app.route('/tab/about')
def tab_about():
    return render_template_string(ABOUT_TAB_TEMPLATE)

@app.route('/image_ids')
def image_ids():
    start = request.args.get('start')
    end = request.args.get('end')
    selected_image_id = request.args.get('selected_image_id')
    if start and end:
        image_ids = get_all_image_ids(start, end)
    else:
        image_ids = get_all_image_ids()
    return render_template_string(IMAGE_ID_ITEM_TEMPLATE, image_ids=image_ids, selected_image_id=selected_image_id)

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