import os
from datetime import datetime
import time
import cv2
from picamera2 import Picamera2
from pathlib import Path

# 1. Create a directory to save the snapshots
output_dir = Path(__file__).resolve().parent / "MotionPictures3"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration())
picam2.start()

time.sleep(2) # Camera warm-up time

print("Monitoring for motion... Press Ctrl+C to stop.")

# Cooldown timer variable to prevent flooding your folder with images
last_trigger_time = 0
cooldown_seconds = 3 

while True:
    img1 = picam2.capture_array()
    time.sleep(0.3) # Interval between frame checks
    img2 = picam2.capture_array()

    # Find the difference between two consecutive frames
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    
    # Count pixel changes
    count = cv2.countNonZero(dilated)
    current_time = time.time()
    
    # Trigger if motion threshold is met AND cooldown period has passed
    if count > 5000 and (current_time - last_trigger_time) > cooldown_seconds:
        last_trigger_time = current_time
        
        # Create a unique filename based on the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{output_dir}/Camera1_{timestamp}.jpg"
        
        bgr_frame = cv2.cvtColor(img2, cv2.COLOR_RGB2BGR)
        # Save the frame that caught the motion
        cv2.imwrite(filename, bgr_frame)
        print(f"Motion Detected! Snapshot saved as {filename}")
