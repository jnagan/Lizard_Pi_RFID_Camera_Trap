import smbus2
import bme280
import csv
import os
from datetime import datetime
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent
# BME280 sensor address (default address)
address = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)

# Read sensor data
data = bme280.sample(bus, address, calibration_params)

def variables():
    # Create timestamps for this specific event
    now = datetime.now()
    datestamp = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H:%M:%S")
    temperature_celsius = data.temperature
    pressure = data.pressure
    humidity = data.humidity
    
    print(temperature_celsius, " ", pressure, " ", humidity)
    
    file_exists = os.path.isfile(CSV_PATH)
                    
    # Ensure CSV target directory exists
    csv_dir = os.path.dirname(CSV_PATH)
    if csv_dir and not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
        headers = ["Date", "Time", "Lat", "Lon", "TemperatureCelsius", "Pressure", "Humidity"]
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow({
            "Date": datestamp,
            "Time": timestamp,
            "Lat": "GPS Coords (Change Later)",
            "Lon": "Change Later",
            "TemperatureCelsius": temperature_celsius,
            "Pressure": pressure,
            "Humidity": humidity
        })
    print("Data successfully saved to CSV.")
    
variables()
