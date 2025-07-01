import socket
import time
import subprocess
import datetime
import os
import select
import shutil
import multiprocessing
from picamera2 import Picamera2


# Configuration
MASTER_IP = "192.168.0.100"
PORT = 5000
MAX_SLAVES = 10
fname="default.jpg"
STORAGE_PATH = "/tmp/pi/usb_ssd"  # CHANGE THIS TO YOUR USB SSD PATH
images_path = "./images/"


def create_storage_folders():
    now = datetime.datetime.now()
    year_folder = os.path.join(STORAGE_PATH, str(now.year))
    month_folder = os.path.join(year_folder, str(now.month).zfill(2))
    day_folder = os.path.join(month_folder, str(now.day).zfill(2))
    os.makedirs(day_folder, exist_ok=True)
    os.makedirs(images_path, exist_ok=True)
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
        filename = os.path.join(images_path, f"rpi0_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg")
        with open(filename, 'wb') as f:
            f.write(capture)
        print(f"Captured {filename}")
        end_time = time.time()
        print(f"|--[INFO]--| Capture time: {end_time-start_time}  \t Image saved to {filename}")
    except Exception as e:
        print(f"|--[ERROR]--| Error capturing image {i}: {e}")
        break


def master_server():
    init_cam()
    storage_folder = create_storage_folders()
    rpi_number = 0      #set as master

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((MASTER_IP, PORT))
    server_socket.listen(MAX_SLAVES)
    server_socket.setblocking(0)

    connections = {}
    print("Master waiting for connections...")

    while True:
        ready_to_read, _, _ = select.select([server_socket], [], [], 1)
        if ready_to_read:
            try:
                client_socket, addr = server_socket.accept()
                try:
                    rpi_number = int(client_socket.recv(1024).decode())
                    connections[rpi_number] = client_socket
                    print(f"Connection from: {addr}, RPI Number: {rpi_number}")
                except ValueError:
                    print(f"Invalid RPI number received from {addr}")
                    client_socket.close()
            except BlockingIOError:
                pass

        connected_rpi_numbers = list(connections.keys())
        num_connected = len(connected_rpi_numbers)
        print(f"Connected RPIs: {connected_rpi_numbers}")
        print(f"Active Pis: {num_connected} / {MAX_SLAVES}")

        # Run capture_image in a separate process
        capture_process = multiprocessing.Process(target=capture_image, args=(rpi_number,))
        capture_process.start()

        responses_received = set()

        for rpi_num, client_socket in connections.items():
            try:
                print('RPI NUM : ', rpi_num)
                client_socket.sendall(b"CAPTURE")
            except (ConnectionResetError, BrokenPipeError):
                print(f"RPI {rpi_num} disconnected before capture.")
                del connections[rpi_num]
                continue

        now = datetime.datetime.now()
        while (len(responses_received) < len(connections) and now < now + datetime.timedelta(seconds=5)):
            print(f"Waiting for responses... Received {len(responses_received)}/{len(connections)}")
            time.sleep(1)

        print("All responses received. Proceeding to next capture.")

if __name__ == "__main__":
    master_server()