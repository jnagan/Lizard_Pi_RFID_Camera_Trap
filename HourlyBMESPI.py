import spidev
import time
import csv
import os
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION ---
CSV_FILE = Path(__file__).resolve().parent / "bme280_sensor_data.csv"

# --- SPI INITIALIZATION ---
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

def log_to_csv(temp, humid, press):
    """Appends data rows to local workspace file, splitting date and time."""
    file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
    
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Date", "Time", "Temperature (C)", "Humidity (%)", "Pressure (hPa)"])
            
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        writer.writerow([date_str, time_str, temp, humid, press])
        print(f"Recorded -> Date: {date_str} | Time: {time_str} | Temp: {temp}°C | Humid: {humid}% | Press: {press} hPa")

# --- SINGLE RUN EXECUTION ---
if __name__ == "__main__":
    try:
        if bme280_init():
            time.sleep(0.1) 
            cal_params = read_calibration_data()
            t, h, p = read_sensor_data(cal_params)
            
            if t is not None:
                log_to_csv(t, h, p)
            else:
                print("Error: Could not retrieve clean telemetry data block from the sensor registers.")
    finally:
        spi.close()
        print("SPI connection closed. Script finished.")