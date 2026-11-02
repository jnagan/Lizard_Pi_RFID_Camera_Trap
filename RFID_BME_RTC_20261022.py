import serial
import time
import subprocess
import os
import csv
from datetime import datetime
from pathlib import Path
import spidev

#---Config---
SERIAL_PORT = '/dev/ttyAMA0'
BAUD_RATE = 9600
START_BYTE = 0x02
FRAME_LEN = 11

home_dir = Path(__file__).resolve().parent
SAVE_DIRECTORY = home_dir / "RFIDReaderPictures"
CSV_PATH = home_dir / "RFIDCameraReaderData.csv"
CSV_FILE = home_dir / "ClimateData.csv"

#---Initialization---
spi = spidev.SpiDev()
spi.open(0, 0) # Opens /dev/spidev0.0
spi.max_speed_hz = 500000
spi.mode = 0b00 # BME280 supports SPI Mode 0 or Mode 3

def bme280_init():
    """Forces the sensor into SPI mode and configures sampling."""
    try:
        # Write 0xB6 to reset register 0xE0 (Write mask: 0xE0 & 0x7F = 0x60)
        spi.xfer2([0x60, 0xB6])
        time.sleep(0.05) 
        
        # Verify device by reading Chip ID register 0xD0 (Read mask: Address | 0x80)
        reply = spi.xfer2([0xD0 | 0x80, 0x00])
        chip_id = reply[1] 
        
        if chip_id == 0x60:
            # Configure Sensor: Humidity oversampling x1
            spi.xfer2([0xF2 & 0x7F, 0x01]) 
            # Configure Sensor: Normal Mode, Temp x1, Pressure x1 oversampling
            spi.xfer2([0xF4 & 0x7F, 0x27]) 
            return True
        else:
            print(f"Error: Sensor returned invalid Chip ID {hex(chip_id)}.")
            return False
    except Exception as e:
        print(f"SPI Initialization failed: {e}")
        return False

def read_calibration_data():
    """Reads all factory calibration parameters required for environmental compensation math logic."""
    # Temperature coefficients (0x88 to 0x8D)
    cal1 = spi.xfer2([0x88 | 0x80] + [0x00]*6)
    dig_T1 = (cal1[2] << 8) | cal1[1]
    dig_T2 = (cal1[4] << 8) | cal1[3]
    if dig_T2 > 32767: dig_T2 -= 65536
    dig_T3 = (cal1[6] << 8) | cal1[5]
    if dig_T3 > 32767: dig_T3 -= 65536

    # Pressure coefficients (0x8E to 0xA1)
    cal2 = spi.xfer2([0x8E | 0x80] + [0x00]*18)
    dig_P1 = (cal2[2] << 8) | cal2[1]
    dig_P2 = (cal2[4] << 8) | cal2[3]
    if dig_P2 > 32767: dig_P2 -= 65536
    dig_P3 = (cal2[6] << 8) | cal2[5]
    if dig_P3 > 32767: dig_P3 -= 65536
    dig_P4 = (cal2[8] << 8) | cal2[7]
    if dig_P4 > 32767: dig_P4 -= 65536
    dig_P5 = (cal2[10] << 8) | cal2[9]
    if dig_P5 > 32767: dig_P5 -= 65536
    dig_P6 = (cal2[12] << 8) | cal2[11]
    if dig_P6 > 32767: dig_P6 -= 65536
    dig_P7 = (cal2[14] << 8) | cal2[13]
    if dig_P7 > 32767: dig_P7 -= 65536
    dig_P8 = (cal2[16] << 8) | cal2[15]
    if dig_P8 > 32767: dig_P8 -= 65536
    dig_P9 = (cal2[18] << 8) | cal2[17]
    if dig_P9 > 32767: dig_P9 -= 65536

    # Humidity coefficients (0xA1, then 0xE1 to 0xE7)
    cal_h1 = spi.xfer2([0xA1 | 0x80, 0x00])
    dig_H1 = cal_h1[1]
    
    cal3 = spi.xfer2([0xE1 | 0x80] + [0x00]*7)
    dig_H2 = (cal3[2] << 8) | cal3[1]
    if dig_H2 > 32767: dig_H2 -= 65536
    dig_H3 = cal3[3]
    dig_H4 = (cal3[4] << 4) | (cal3[5] & 0x0F)
    if dig_H4 > 2047: dig_H4 -= 4096
    dig_H5 = (cal3[6] << 4) | (cal3[5] >> 4)
    if dig_H5 > 2047: dig_H5 -= 4096
    dig_H6 = cal3[7]
    if dig_H6 > 127: dig_H6 -= 256

    # FIX: Return all exact matching variable names correctly
    return (dig_T1, dig_T2, dig_T3, dig_P1, dig_P2, dig_P3, dig_P4, dig_P5, 
            dig_P6, dig_P7, dig_P8, dig_P9, dig_H1, dig_H2, dig_H3, dig_H4, dig_H5, dig_H6)

def read_sensor_data(cal):
    """Performs continuous hardware reads and decodes physical calculations."""
    try:
        (dT1, dT2, dT3, dP1, dP2, dP3, dP4, dP5, dP6, dP7, dP8, dP9, dH1, dH2, dH3, dH4, dH5, dH6) = cal
        
        # Burst read data registers 0xF7 to 0xFC (Pressure, Temp, Humidity)
        data = spi.xfer2([0xF7 | 0x80] + [0x00]*8)
        
        raw_press = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        raw_temp = (data[4] << 12) | (data[5] << 4) | (data[6] >> 4)
        raw_humid = (data[7] << 8) | data[8]
        
        # --- Temperature Math ---
        v1 = ((((raw_temp >> 3) - (dT1 << 1))) * dT2) >> 11
        v2 = (((((raw_temp >> 4) - dT1) * ((raw_temp >> 4) - dT1)) >> 12) * dT3) >> 14
        t_fine = v1 + v2
        temperature = ((t_fine * 5 + 128) >> 8) / 100.0
        
        # --- Pressure Math ---
        v1 = (t_fine >> 1) - 64000
        v2 = (((v1 >> 2) * (v1 >> 2)) >> 11) * dP6
        v2 = v2 + ((v1 * dP5) << 1)
        v2 = (v2 >> 2) + (dP4 << 16)
        v1 = (((dP3 * (((v1 >> 2) * (v1 >> 2)) >> 13)) >> 3) + (((dP2) * v1) >> 1)) >> 18
        v1 = ((32768 + v1) * dP1) >> 15
        
        if v1 == 0:
            pressure = 0
        else:
            p = (((1048576 - raw_press) - (v2 >> 12))) * 3125
            if p < 0x80000000:
                p = (p << 1) // v1
            else:
                p = (p // v1) * 2
            v1 = (dP9 * (((p >> 3) * (p >> 3)) >> 13)) >> 12
            v2 = (((p >> 2)) * dP8) >> 13
            pressure = (p + ((v1 + v2 + dP7) >> 4)) / 100.0

        # --- Humidity Math ---
        h = t_fine - 76800
        h = ((((raw_humid << 14) - (dH4 << 20) - (dH5 * h)) + 16384) >> 15) * \
            (((((((h * dH6) >> 10) * (((h * dH3) >> 11) + 32768)) >> 10) + 2097152) * dH2 + 8192) >> 14)
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * dH1) >> 4)
        h = 0 if h < 0 else h
        h = 41943040 if h > 41943040 else h
        humidity = (h >> 12) / 1024.0

        return round(temperature, 2), round(humidity, 2), round(pressure, 2)
    except Exception:
        return None, None, None

def take_photo(final_tag, timestamp_str):
    """Captures a photo and returns the filename for the CSV."""
    if not os.path.exists(SAVE_DIRECTORY):
        os.makedirs(SAVE_DIRECTORY)

    filename = f"RFID_{final_tag}_{timestamp_str}.jpg"
    filepath = os.path.join(SAVE_DIRECTORY, filename)
    
    print(f"Capturing image: {filepath}...")
    try:
        # Captures the photo (500ms delay for exposure balance)
        subprocess.run(["rpicam-still", "-o", filepath, "-t", "500", "--nopreview"], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return filename
    except Exception as e:
        print(f"Camera Error: {e}")
        return "ERROR_NO_IMAGE.jpg"

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"--- System Ready: Scanning for RFID ---")
        ser.reset_input_buffer()
    except Exception as e:
        print(f"Serial Connection Error: {e}")
        return
    
    buffer = bytearray()

    try:
        while True:
            # Keep checking the serial port for an RFID card
            if ser.in_waiting > 0:
                buffer.extend(ser.read(ser.in_waiting))

            while buffer and buffer[0] != START_BYTE:
                buffer.pop(0)

            # --- THIS BLOCK ONLY RUNS WHEN A VALID RFID TAG IS HOME ---
            if len(buffer) >= FRAME_LEN:
                raw_payload = buffer[1:FRAME_LEN]
                
                try:
                    # 1. Decode RFID Tag
                    try:
                        hex_str = raw_payload.decode('ascii').strip()
                    except UnicodeDecodeError:
                        hex_str = raw_payload.hex().upper()

                    card_id_dec = int(hex_str[::-1], 16)
                    final_tag = f"{card_id_dec:012d}"
                    print(f"\n[TRIGGER] SCAN DETECTED: {final_tag}")
                    
                    # Create timestamps for this specific event
                    now = datetime.now()
                    datestamp = now.strftime("%Y-%m-%d")
                    timestamp = now.strftime("%H:%M:%S")
                    file_timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                    
                    # 2. Trigger Camera
                    filename = take_photo(final_tag, file_timestamp)
                    
                    # 3. Read Environmental Data (ONLY triggered right now!)
                    #temp = None
                    #press = None
                    #humid = None
                    
                    try:
                        if bme280_init():
                            time.sleep(0.1) 
                            cal_params = read_calibration_data()
                            t, h, p = read_sensor_data(cal_params)
                            
                            if t is not None:
                        
                                # 4. Write everything to the CSV exactly ONCE
                                file_exists = os.path.isfile(CSV_PATH)
                    
                                # Ensure CSV target directory exists
                                csv_dir = os.path.dirname(CSV_PATH)
                                if csv_dir and not os.path.exists(csv_dir):
                                    os.makedirs(csv_dir)

                                with open(CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
                                    headers = ["Date", "Time", "Location", "RFIDNumber", "TemperatureCelsius", "Pressure", "Humidity", "PictureID"]
                                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                        
                                    if not file_exists:
                                        writer.writeheader()
                            
                                    writer.writerow({
                                        "Date": datestamp,
                                        "Time": timestamp,
                                        "Location": "GPS Coords (Change Later)",
                                        "RFIDNumber": final_tag,
                                        "TemperatureCelsius": t if t is not None else "N/A",
                                        "Pressure": p if p is not None else "N/A",
                                        "Humidity": h if h is not None else "N/A",
                                        "PictureID": filename
                                    })
                                print("Data successfully saved to CSV.")
                            
                    except Exception as e:
                        print(f"Processing error: {e}")
                
                    # Clear buffer, pause 1 sec to let the lizard move, and clear serial lines
                    del buffer[:FRAME_LEN]
                    time.sleep(1) 
                    ser.reset_input_buffer()
                    
                except Exception as e:
                    print(f"Processing error: {e}")

    except KeyboardInterrupt:
        print("\nShutting down")
        
    finally:
        spi.close()
        ser.close()

if __name__ == "__main__":
    main()