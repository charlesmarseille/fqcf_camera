import socket
import time
import subprocess
import datetime
import os
import select
import shutil

# Configuration
MASTER_IP = "192.168.0.47"
PORT = 5000
MAX_SLAVES = 7
CAPTURE_COMMAND = ["libcamera-still", "-o", "a.jpg", "-n", "--width", "1296", "--height", "972", "--immediate"]
STORAGE_PATH = "/tmp/pi/usb_ssd"  # CHANGE THIS TO YOUR USB SSD PATH

def create_storage_folders():
    now = datetime.datetime.now()
    year_folder = os.path.join(STORAGE_PATH, str(now.year))
    month_folder = os.path.join(year_folder, str(now.month).zfill(2))
    day_folder = os.path.join(month_folder, str(now.day).zfill(2))
    os.makedirs(day_folder, exist_ok=True)
    return day_folder

def capture_image(rpi_number):
    try:
        result = subprocess.run(CAPTURE_COMMAND, capture_output=True, check=True)
        print(f"Image captured by RPI {rpi_number}")
        return result.stdout
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

        user_input = input("Press Enter to trigger capture or type 'exit' to quit: ")
        if user_input.lower() == "exit":
            break

        storage_folder = create_storage_folders()
        rpi_number = os.environ.get("RPI_NUMBER") or "master"
        capture_image(rpi_number)

        responses_received = set()

        for rpi_num, client_socket in connections.items():
            try:
                client_socket.sendall(b"CAPTURE")
            except (ConnectionResetError, BrokenPipeError):
                print(f"RPI {rpi_num} disconnected before capture.")
                del connections[rpi_num]
                continue

            try:
                image_data_len_bytes = client_socket.recv(8)
                image_data_len = int.from_bytes(image_data_len_bytes, byteorder='big')
                image_data = b''
                while len(image_data) < image_data_len:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    image_data += chunk
                if image_data:
                    filename = os.path.join(storage_folder, f"rpi{rpi_num}_{datetime.datetime.now().strftime('%H%M%S')}.jpg")
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

        while len(responses_received) < len(connections):
            print(f"Waiting for responses... Received {len(responses_received)}/{len(connections)}")
            time.sleep(1)

        print("All responses received. Proceeding to next capture.")

    server_socket.close()
    for client_socket in connections.values():
        client_socket.close()

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
            break
        except ConnectionRefusedError:
            print("Master not available, retrying in 1 second...")
            time.sleep(1)

    print(f"Connected to master as RPI {rpi_number}. Waiting for trigger...")

    while True:
        try:
            data = client_socket.recv(1024)
            if data == b"CAPTURE":
                print("Capture trigger received.")
                image_data = capture_image(rpi_number)
                if image_data:
                    image_data_len = len(image_data)
                    image_data_len_bytes = image_data_len.to_bytes(8, byteorder='big')
                    client_socket.sendall(image_data_len_bytes)
                    client_socket.sendall(image_data)
                    print(f"Image from RPI {rpi_number} sent.")
                else:
                    print(f"Failed to capture image on RPI {rpi_number}")
                    client_socket.sendall(int(0).to_bytes(8, byteorder='big'))
        except (ConnectionResetError, ConnectionAbortedError):
            print("Master disconnected.")
            break
    client_socket.close()

if __name__ == "__main__":
    if os.environ.get("MASTER") == "true":
        master_server()
    else:
        slave_client()