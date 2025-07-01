from pyzbar.pyzbar import decode
from PIL import Image

def decode_qr_code(image_path):
    """
    Decodes QR codes from an image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        list: A list of decoded QR code data (strings), or an empty list if no QR codes are found.
        Returns None if there are errors during decoding.
    """
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)

        decoded_data = []
        for obj in decoded_objects:
            decoded_data.append(obj.data.decode('utf-8')) #decode the byte data into string

        return decoded_data

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



# Example usage:
image_file = "pi0_113.jpg" # Replace with your image file name.
decoded_results = decode_qr_code(image_file)

if decoded_results is not None:
    if decoded_results:
        for data in decoded_results:
            print(f"Decoded QR code data: {data}")
    else:
        print("No QR codes found in the image.")


#Example usage with opencv, in case you need to read from a webcam or numpy array.

import cv2
import numpy as np

def decode_qr_code_cv2(image):
    """
    Decodes QR codes from a cv2 image.

    Args:
        image (numpy.ndarray): The image as a numpy array.

    Returns:
        list: A list of decoded QR code data (strings), or an empty list if no QR codes are found.
    """
    try:
        decoded_objects = decode(image)

        decoded_data = []
        for obj in decoded_objects:
            decoded_data.append(obj.data.decode('utf-8'))

        return decoded_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

#Example webcam usage.
def decode_webcam_qr():
    cap = cv2.VideoCapture(0) # 0 represents the default camera

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        decoded_results = decode_qr_code_cv2(frame)

        if decoded_results:
            for data in decoded_results:
                print(f"Decoded QR code data: {data}")

        cv2.imshow('Webcam', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()

#uncomment to run webcam example.
#decode_webcam_qr()