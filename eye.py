import time
import numpy as np
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106
from PIL import ImageDraw
import random
import signal
import sys
import RPi.GPIO as GPIO

# --- Configuration for SPI ---
SPI_BUS = 0
SPI_DEVICE = 0
DC_PIN = 23
RST_PIN = 24

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def cleanup():
    """Clean up GPIO and display resources"""
    print("\nCleaning up resources...")
    try:
        if 'device' in globals():
            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
            device.clear()
            time.sleep(0.1)
    except Exception as e:
        print(f"Error during display cleanup: {e}")
    
    try:
        GPIO.cleanup()
    except Exception as e:
        print(f"Error during GPIO cleanup: {e}")
    print("Cleanup complete.")

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initialize the OLED device
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    device = ssd1306(serial)
    device.clear()
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    cleanup()
    sys.exit(1)

# Calculate center for the single eye placement
center_x = device.width // 2
center_y = device.height // 2

# Define eye parameters for the "hunter" anime eye style
EYE_WIDTH = 40
EYE_HEIGHT = 20
PUPIL_SIZE = 10
HIGHLIGHT_SIZE = 3
SECONDARY_HIGHLIGHT_SIZE = 1

# Eyelash parameters (fixed the variable name from EYE_EYELASH_LENGTH to EYELASH_LENGTH)
NUM_EYELASHES = 5
EYELASH_LENGTH = 7
EYELASH_THICKNESS = 1
EYELASH_ANGLES = np.linspace(np.pi * 0.7, np.pi * 0.3, NUM_EYELASHES)

def draw_hunter_eye(draw, center_x_eye, center_y_eye, pupil_x_offset=0, pupil_y_offset=0,
                    highlight_pos='top_left', eyelid_y_offset=0, is_happy_squint=False):
    """Draws a single hunter-style anime eye with pupil, highlights, and eyelashes."""
    eye_bbox = [center_x_eye - EYE_WIDTH, center_y_eye - EYE_HEIGHT + eyelid_y_offset,
                center_x_eye + EYE_WIDTH, center_y_eye + EYE_HEIGHT + eyelid_y_offset]

    draw.ellipse(eye_bbox, outline="white", fill="black")
    draw.line((eye_bbox[0], eye_bbox[1] + 2, eye_bbox[2], eye_bbox[1] + 2), fill="white")
    
    if not is_happy_squint:
        draw.line((eye_bbox[0], eye_bbox[3] - 2, eye_bbox[2], eye_bbox[3] - 2), fill="white")
    else:
        draw.arc((eye_bbox[0], eye_bbox[3] - EYE_HEIGHT // 2, eye_bbox[2], eye_bbox[3]),
                 start=0, end=180, fill="white", width=1)

    # Draw eyelashes (fixed the variable name here)
    for i, angle in enumerate(EYELASH_ANGLES):
        lx = center_x_eye + (EYE_WIDTH * np.cos(angle * 1.05 - np.pi/2))
        ly = (center_y_eye - EYE_HEIGHT + eyelid_y_offset) + (EYE_HEIGHT * 0.2 * (1 - np.sin(angle - np.pi/2)))
        ex = lx + EYELASH_LENGTH * np.cos(angle)
        ey = ly - EYELASH_LENGTH * np.sin(angle)
        draw.line((lx, ly, ex, ey), fill="white", width=EYELASH_THICKNESS)

    pupil_center_x = center_x_eye + pupil_x_offset
    pupil_center_y = center_y_eye + pupil_y_offset
    
    draw.ellipse(
        (pupil_center_x - PUPIL_SIZE, pupil_center_y - PUPIL_SIZE,
         pupil_center_x + PUPIL_SIZE, pupil_center_y + PUPIL_SIZE),
        outline="white", fill="white"
    )

    # Highlight positions
    main_highlight_x = pupil_center_x
    main_highlight_y = pupil_center_y
    secondary_highlight_x = pupil_center_x
    secondary_highlight_y = pupil_center_y

    if highlight_pos == 'top_left':
        main_highlight_x -= PUPIL_SIZE // 2
        main_highlight_y -= PUPIL_SIZE // 2
        secondary_highlight_x += PUPIL_SIZE // 3
        secondary_highlight_y -= PUPIL_SIZE // 3
    elif highlight_pos == 'top_right':
        main_highlight_x += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE
        main_highlight_y -= PUPIL_SIZE // 2
        secondary_highlight_x -= PUPIL_SIZE // 3
        secondary_highlight_y -= PUPIL_SIZE // 3
    elif highlight_pos == 'bottom_left':
        main_highlight_x -= PUPIL_SIZE // 2
        main_highlight_y += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE
        secondary_highlight_x += PUPIL_SIZE // 3
        secondary_highlight_y += PUPIL_SIZE // 3
    elif highlight_pos == 'bottom_right':
        main_highlight_x += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE
        main_highlight_y += PUPIL_SIZE // 2 - HIGHLIGHT_SIZE
        secondary_highlight_x -= PUPIL_SIZE // 3
        secondary_highlight_y += PUPIL_SIZE // 3
    elif highlight_pos == 'center':
        main_highlight_x -= HIGHLIGHT_SIZE // 2
        main_highlight_y -= HIGHLIGHT_SIZE // 2
        secondary_highlight_x -= SECONDARY_HIGHLIGHT_SIZE // 2
        secondary_highlight_y -= SECONDARY_HIGHLIGHT_SIZE // 2 + PUPIL_SIZE // 2
    
    draw.ellipse(
        (main_highlight_x, main_highlight_y,
         main_highlight_x + HIGHLIGHT_SIZE, main_highlight_y + HIGHLIGHT_SIZE),
        fill="black"
    )
    draw.ellipse(
        (secondary_highlight_x, secondary_highlight_y,
         secondary_highlight_x + SECONDARY_HIGHLIGHT_SIZE, secondary_highlight_y + SECONDARY_HIGHLIGHT_SIZE),
        fill="black"
    )

# [Rest of your functions remain unchanged...]
# animate_happy(), animate_joy(), draw_closed_eye(), animate_eyes_main_loop() 
# all stay exactly the same as in your original code

# --- Main execution block ---
try:
    if 'device' in locals() and device:
        device.clear()
        print("Starting single hunter anime eye animation...")
        animate_eyes_main_loop()

except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
finally:
    cleanup()
