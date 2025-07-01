import os
import datetime
import matplotlib.pyplot as plt

def parse_filename(filename):
    """Parses filename without regex."""
    try:
        parts = filename.split("_")
        pi = int(parts[0][2])  # Extract pi number (0 or 3)
        image_id = int(parts[1])
        date_str = parts[2]
        time_str = parts[3][:6]  # First 6 digits are HHMMSS
        ms_str = parts[3][6:9]   # Last 3 digits are milliseconds
        dt_obj = datetime.datetime.strptime(date_str + time_str + ms_str, "%Y%m%d%H%M%S%f")
        return pi, image_id, dt_obj
    except (ValueError, IndexError):  # Handle parsing errors
        raise ValueError(f"Invalid filename format: {filename}")


def calculate_time_diffs(folder0_path, folder3_path):
    """Calculates time differences between corresponding images in two folders."""

    folder0_files = {f: parse_filename(f) for f in os.listdir(folder0_path) if f.endswith(".jpg")}
    folder3_files = {f: parse_filename(f) for f in os.listdir(folder3_path) if f.endswith(".jpg")}

    time_diffs = []
    image_ids = []

    for file0, (_, id0, dt0) in folder0_files.items():
        for file3, (_, id3, dt3) in folder3_files.items():
            if id0 == id3:  # Match image IDs
                time_diff = abs((dt3 - dt0).total_seconds())  # Absolute difference in seconds
                time_diffs.append(time_diff)
                image_ids.append(id0)
                break  # Found a match, move to the next image0
    return image_ids, time_diffs


def plot_time_diffs(image_ids, time_diffs):
    """Plots the time differences."""
    plt.figure(figsize=(10, 6))  # Adjust figure size for better readability
    plt.bar(image_ids, time_diffs)
    plt.xlabel("Image ID")
    plt.ylabel("Time Difference (seconds)")
    plt.title("Time Difference Between Corresponding Images")
    plt.xticks(image_ids, rotation=45, ha="right") # Rotate x-axis labels if needed
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()


if __name__ == "__main__":
    folder0_path = "0"  # Replace with your folder paths
    folder3_path = "3"

    try:
        image_ids, time_diffs = calculate_time_diffs(folder0_path, folder3_path)
        plot_time_diffs(image_ids, time_diffs)
    except FileNotFoundError:
        print("Error: One or both folders not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
