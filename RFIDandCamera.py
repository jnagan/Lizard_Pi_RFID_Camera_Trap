import serial
import time
import subprocess
import os  # Added to handle directory creation
from datetime import datetime

# Configuration
SERIAL_PORT = '/dev/ttyAMA0'
BAUD_RATE = 9600
START_BYTE = 0x02
FRAME_LEN = 11
SAVE_DIRECTORY = "lizard_pics"  # Name of your folder

def take_photo(iso_number):
    """Captures a photo and saves it to the specific folder."""
    # Ensure the directory exists before saving
    if not os.path.exists(SAVE_DIRECTORY):
        os.makedirs(SAVE_DIRECTORY)
        print(f"Created directory: {SAVE_DIRECTORY}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"RFID_{iso_number}_{timestamp}.jpg"
    
    # Combine the folder name and the filename
    filepath = os.path.join(SAVE_DIRECTORY, filename)
    
    print(f"Capturing image: {filepath}...")
    try:
        # rpicam-still command with the full filepath
        subprocess.run(["rpicam-still", "-o", filepath, "-t", "500", "--nopreview"], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Image saved to {SAVE_DIRECTORY}.")
    except Exception as e:
        print(f"Camera Error: {e}")

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"--- System Ready: Scanning for RFID ---")
        print(f"--- Photos will be saved in: {SAVE_DIRECTORY} ---")
        ser.reset_input_buffer()
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    buffer = bytearray()

    try:
        while True:
            if ser.in_waiting > 0:
                buffer.extend(ser.read(ser.in_waiting))

            while buffer and buffer[0] != START_BYTE:
                buffer.pop(0)

            if len(buffer) >= FRAME_LEN:
                raw_payload = buffer[1:FRAME_LEN]
                
                try:
                    try:
                        hex_str = raw_payload.decode('ascii').strip()
                    except UnicodeDecodeError:
                        hex_str = raw_payload.hex().upper()

                    #card_id_dec = int(hex_str, 16) - this is for the non-inverted string
                    card_id_dec = int(hex_str[::-1], 16)
                    final_tag = f"{card_id_dec:012d}"

                    print(f"\nSCAN DETECTED: {final_tag}")
                    
                    take_photo(final_tag)

                except Exception as e:
                    print(f"Processing error: {e}")
                
                del buffer[:FRAME_LEN]
                time.sleep(1) 
                ser.reset_input_buffer()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
