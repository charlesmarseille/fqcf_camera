import socket
import time
import subprocess
import datetime
import os
import select
import shutil
from picamera2 import Picamera2


# Configuration
MASTER_IP = "192.168.0.100"
PORT = 5000
images_path = "./images/"

def create_storage_folders():
    now = datetime.datetime.now()
    year_folder = os.path.join(STORAGE_PATH, str(now.year))
    month_folder = os.path.join(year_folder, str(now.month).zfill(2))
    day_folder = os.path.join(month_folder, str(now.day).zfill(2))
    os.makedirs(day_folder, exist_ok=True)
    return day_folder

def init_cam():
    print('|--[INFO]--| Initializing cam...')
    picam2 = Picamera2()
    print('|--[INFO]--| Configuring cam...')
    config = picam2.create_still_configuration()
    picam2.configure(config)
    print('|--[INFO]--| Starting cam...')
    picam2.start()
    print('|--[INFO]--| sleep 1 for cam warm up...')
    time.sleep(1)  # Give the camera a moment to warm up


def capture_image(rpi_number):
    start_time = time.time()
    print('Starting capture...')
    try:
        capture = picam2.capture_array()
        filename = os.path.join(images_path, f"rpi{rpi_number}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg")
        with open(filename, 'wb') as f:
            f.write(capture)
        print(f"Captured {filename}")
        end_time = time.time()
        print(f"|--[INFO]--| Capture time: {end_time-start_time}  \t Image saved to {filename}")
        return 0
    except Exception as e:
        print(f"|--[ERROR]--| Error capturing image {i}: {e}")
        return e


def slave_client():
    rpi_number = os.environ.get("RPI_NUMBER")
    if rpi_number is None:
        print("Error: RPI_NUMBER environment variable not set on slave.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client_socket.connect((MASTER_IP, PORT))
            client_socket.sendall(str(rpi_number).encode())

            data = client_socket.recv(1024)
            if data == b"CAPTURE":
                print("Capture trigger received.")
                status = capture_image(rpi_number)
                if status==0:
                    print(f"Image from RPI {rpi_number} sent.")
                else:
                    print(f"Failed to capture image on RPI {rpi_number}")
                    client_socket.sendall(e.to_bytes(8, byteorder='big'))

        except ConnectionRefusedError:
            print("Master not available, retrying in 1 second...")
            time.sleep(1)

    print(f"Connected to master as RPI {rpi_number}. Waiting for trigger...")

    while True:


if __name__ == "__main__":
    slave_client()