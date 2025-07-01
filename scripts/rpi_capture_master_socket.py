import socket
import time
import subprocess
import datetime
import os
import select
import shutil
import multiprocessing

# Configuration
MASTER_IP = "192.168.0.47"
PORT = 5000
MAX_SLAVES = 7
fname="default.jpg"
STORAGE_PATH = "/tmp/pi/usb_ssd"  # CHANGE THIS TO YOUR USB SSD PATH
images_path = "./images/"
last_path = "./images/last/"


def create_storage_folders():
    now = datetime.datetime.now()
    year_folder = os.path.join(STORAGE_PATH, str(now.year))
    month_folder = os.path.join(year_folder, str(now.month).zfill(2))
    day_folder = os.path.join(month_folder, str(now.day).zfill(2))
    os.makedirs(day_folder, exist_ok=True)
    os.makedirs(images_path, exist_ok=True)
    os.makedirs(last_path, exist_ok=True)
    return day_folder

def capture_image(rpi_number):
    try:
        fname = os.path.join(last_path, f"rpi0_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg")
        CAPTURE_COMMAND = ["libcamera-still", "-o", f"{fname}", "-n", "--width", "1296", "--height", "972", "--immediate"]
        result = subprocess.run(CAPTURE_COMMAND, capture_output=True, check=True)
        print(f"Image captured by RPI {rpi_number}, saved to {fname}")

    except subprocess.CalledProcessError as e:
        print(f"Error capturing image by RPI {rpi_number}: {e}")
        return None

def master_server():
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

        storage_folder = create_storage_folders()
        rpi_number = 0

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

            try:
                image_time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                image_data_len_bytes = client_socket.recv(8)
                image_data_len = int.from_bytes(image_data_len_bytes, byteorder='big')
                image_data = b''
                while len(image_data) < image_data_len:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    image_data += chunk
                if image_data:
                    filename = os.path.join(last_path, f"rpi{rpi_num}_{image_time}.jpg")
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    print(f"Image from RPI {rpi_num} saved to {filename}")
                    responses_received.add(rpi_num)
                else:
                    print(f"No image data received from RPI {rpi_num}")
                    responses_received.add(rpi_num)

            except (ConnectionResetError, BrokenPipeError):
                print(f"RPI {rpi_num} disconnected during image transfer.")
                del connections[rpi_num]
        now = datetime.datetime.now()
        while (len(responses_received) < len(connections) and now < now + datetime.timedelta(seconds=5)):
            print(f"Waiting for responses... Received {len(responses_received)}/{len(connections)}")
            time.sleep(1)

        print("All responses received. Proceeding to next capture.")

    server_socket.close()
    for client_socket in connections.values():
        client_socket.close()

if __name__ == "__main__":
    master_server()