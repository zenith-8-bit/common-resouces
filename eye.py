import time
import numpy as np # For random functions
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106 # Or just ssd1306 if you know your chip
from PIL import ImageDraw
import random # Used for more varied random choices

# --- Configuration for SPI ---
# SPI uses a bus (0 or 1) and device (0 or 1, for CS0 or CS1)
# Most common setup is bus 0, device 0 (CE0)
SPI_BUS = 0
SPI_DEVICE = 0 # Corresponds to CE0 (GPIO 8)

# GPIO pin numbers for DC and RESET (using BCM numbering)
# Ensure these match your wiring!
DC_PIN = 23    # Connected to GPIO 23 (Physical Pin 16)
RST_PIN = 24  # Connected to GPIO 24 (Physical Pin 18)

# Initialize the OLED device.
# This part is wrapped in a try-except block to gracefully handle cases
# where the hardware might not be connected or configured correctly.
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    # Try ssd1306 first, if it doesn't work, you might need to change to sh1106(serial)
    device = ssd1306(serial)
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    print("Please ensure your wiring is correct and the luma.oled library is installed.")
    print("If you are running this without an actual OLED, you'll need a mock device or to comment out device interaction.")
    # Exit the script if the device cannot be initialized, as further operations would fail.
    exit()

# Calculate center for the single eye placement based on the display resolution
center_x = device.width // 2
center_y = device.height // 2

# Define eye parameters for the "hunter" anime eye style.
# These values are tuned for a 128x64 display and a single eye in the center.
EYE_WIDTH = 40 # Overall horizontal extent of the eye
EYE_HEIGHT = 20 # Overall vertical extent of the eye (flatter than previous)
PUPIL_SIZE = 10 # Radius of the pupil, larger for focus
HIGHLIGHT_SIZE = 3 # Size of the main pupil highlight
SECONDARY_HIGHLIGHT_SIZE = 1 # Size of a smaller, secondary highlight

# Eyelash parameters
NUM_EYELASHES = 5
EYELASH_LENGTH = 7
EYELASH_THICKNESS = 1
# Angles for eyelashes (in radians, relative to straight up/down)
# These define the spread of the lashes across the top of the eye
EYELASH_ANGLES = np.linspace(np.pi * 0.7, np.pi * 0.3, NUM_EYELASHES) # From left to right top curve

def draw_hunter_eye(draw, center_x_eye, center_y_eye, pupil_x_offset=0, pupil_y_offset=0,
                    highlight_pos='top_left', eyelid_y_offset=0, is_happy_squint=False):
    """
    Draws a single hunter-style anime eye with pupil, highlights, and eyelashes.
    The 'hunter' style is achieved with a slightly sharper, more angular outer shape,
    and a focused pupil.
    
    Args:
        draw: The PIL ImageDraw object to draw on.
        center_x_eye (int): X-coordinate of the center of the eye.
        center_y_eye (int): Y-coordinate of the center of the eye.
        pupil_x_offset (int): Horizontal offset for the pupil relative to the eye center.
        pupil_y_offset (int): Vertical offset for the pupil relative to the eye center.
        highlight_pos (str): Position of the main pupil highlight ('top_left', 'top_right', etc.).
        eyelid_y_offset (int): Vertical offset for the upper eyelid to simulate squinting/opening.
        is_happy_squint (bool): If True, draws a slightly different lower lid for happy squint.
    """
    # Define the bounding box for the outer eye shape
    eye_bbox = [center_x_eye - EYE_WIDTH, center_y_eye - EYE_HEIGHT + eyelid_y_offset,
                center_x_eye + EYE_WIDTH, center_y_eye + EYE_HEIGHT + eyelid_y_offset]

    # Draw the outer eye shape using an ellipse, then potentially drawing over it for a sharper look.
    # For OLEDs, filling black inside a white outline creates the cutout effect for the pupil.
    draw.ellipse(eye_bbox, outline="white", fill="black")

    # For a sharper "hunter" look, let's slightly flatten the top and bottom with lines
    # This gives a more angular, less perfectly round feel.
    # Top lid line
    draw.line((eye_bbox[0], eye_bbox[1] + 2, eye_bbox[2], eye_bbox[1] + 2), fill="white")
    # Bottom lid line
    if not is_happy_squint:
        draw.line((eye_bbox[0], eye_bbox[3] - 2, eye_bbox[2], eye_bbox[3] - 2), fill="white")
    else:
        # For a happy squint, make the bottom lid arc slightly upwards
        draw.arc((eye_bbox[0], eye_bbox[3] - EYE_HEIGHT // 2, eye_bbox[2], eye_bbox[3]),
                 start=0, end=180, fill="white", width=1) # A subtle upward curve

    # Draw eyelashes
    for i, angle in enumerate(EYELASH_ANGLES):
        # Calculate start point of the lash on the upper eyelid curve
        # Approximating top eyelid curve for lash placement
        lx = center_x_eye + (EYE_WIDTH * np.cos(angle * 1.05 - np.pi/2)) # Adjust factor for spread
        ly = (center_y_eye - EYE_HEIGHT + eyelid_y_offset) + (EYE_HEIGHT * 0.2 * (1 - np.sin(angle - np.pi/2))) # Adjust vertical position
        
        # Calculate end point of the lash based on angle and length
        ex = lx + EYE_EYELASH_LENGTH * np.cos(angle)
        ey = ly - EYE_EYELASH_LENGTH * np.sin(angle) # Lashes point outwards/upwards
        
        draw.line((lx, ly, ex, ey), fill="white", width=EYELASH_THICKNESS)


    # Calculate the pupil's center based on eye center and its offset
    pupil_center_x = center_x_eye + pupil_x_offset
    pupil_center_y = center_y_eye + pupil_y_offset
    
    # Draw the pupil (white circle/ellipse)
    draw.ellipse(
        (pupil_center_x - PUPIL_SIZE, pupil_center_y - PUPIL_SIZE,
         pupil_center_x + PUPIL_SIZE, pupil_center_y + PUPIL_SIZE),
        outline="white", fill="white"
    )

    # Calculate highlight positions
    main_highlight_x = pupil_center_x
    main_highlight_y = pupil_center_y
    secondary_highlight_x = pupil_center_x
    secondary_highlight_y = pupil_center_y

    # Adjust highlight positions based on 'highlight_pos' for main highlight
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
        secondary_highlight_y -= SECONDARY_HIGHLIGHT_SIZE // 2 + PUPIL_SIZE // 2 # Secondary slightly above
    
    # Draw the main pupil highlight (black on white pupil)
    draw.ellipse(
        (main_highlight_x, main_highlight_y,
         main_highlight_x + HIGHLIGHT_SIZE, main_highlight_y + HIGHLIGHT_SIZE),
        fill="black"
    )
    # Draw a secondary, smaller highlight for more depth
    draw.ellipse(
        (secondary_highlight_x, secondary_highlight_y,
         secondary_highlight_x + SECONDARY_HIGHLIGHT_SIZE, secondary_highlight_y + SECONDARY_HIGHLIGHT_SIZE),
        fill="black"
    )

def draw_closed_eye(draw, center_x_eye, center_y_eye):
    """
    Draws a closed eye as a simple horizontal line with slight curve.
    """
    # A slightly curved line for a more natural closed eye
    draw.arc(
        (center_x_eye - EYE_WIDTH, center_y_eye - EYE_HEIGHT // 4,
         center_x_eye + EYE_WIDTH, center_y_eye + EYE_HEIGHT // 4),
        start=180, end=360, fill="white", width=2 # Half ellipse from 180 to 360 degrees
    )

def animate_happy():
    """
    Animates a happy expression: eye squints slightly, pupil moves up.
    """
    steps = 5 # Number of animation frames
    for i in range(steps):
        with canvas(device) as draw:
            # Gradually increase eyelid_y_offset for squinting, and move pupil up
            eyelid_offset = int(EYE_HEIGHT * 0.08 * (i / steps)) # Gentle squint
            pupil_offset_y = int(-PUPIL_SIZE * 0.4 * (i / steps)) # Pupil moves up
            
            draw_hunter_eye(draw, center_x, center_y,
                            pupil_y_offset=pupil_offset_y,
                            eyelid_y_offset=eyelid_offset,
                            is_happy_squint=True, highlight_pos='top_left')
        time.sleep(0.08) # Small delay for smooth animation

    # Hold the happy expression
    with canvas(device) as draw:
        draw_hunter_eye(draw, center_x, center_y, pupil_y_offset=int(-PUPIL_SIZE * 0.4),
                        eyelid_y_offset=int(EYE_HEIGHT * 0.08), is_happy_squint=True, highlight_pos='top_left')
    time.sleep(np.random.uniform(1.0, 2.0))

    # Reverse animation back to normal
    for i in range(steps - 1, -1, -1):
        with canvas(device) as draw:
            eyelid_offset = int(EYE_HEIGHT * 0.08 * (i / steps))
            pupil_offset_y = int(-PUPIL_SIZE * 0.4 * (i / steps))
            draw_hunter_eye(draw, center_x, center_y,
                            pupil_y_offset=pupil_offset_y,
                            eyelid_y_offset=eyelid_offset,
                            is_happy_squint=True, highlight_pos='top_left')
        time.sleep(0.08)
    time.sleep(0.3) # Pause after returning to normal

def animate_joy():
    """
    Animates a joyful expression: more exaggerated squint, rapid pupil movement, and highlight flicker.
    """
    steps = 7 # More frames for smoother, more energetic animation
    for i in range(steps):
        with canvas(device) as draw:
            # More pronounced squint and pupil movement
            eyelid_offset = int(EYE_HEIGHT * 0.15 * (i / steps))
            pupil_offset_y = int(-PUPIL_SIZE * 0.6 * (i / steps))
            
            # Flicker highlight position for "sparkle" effect
            current_highlight_pos = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right'])
            
            draw_hunter_eye(draw, center_x, center_y,
                            pupil_y_offset=pupil_offset_y,
                            eyelid_y_offset=eyelid_offset,
                            is_happy_squint=True, highlight_pos=current_highlight_pos)
        time.sleep(0.05) # Faster frames for energetic feel

    # Hold the joyful expression with subtle pupil jitter and highlight flicker
    hold_duration = np.random.uniform(1.0, 2.0)
    start_time = time.time()
    while time.time() - start_time < hold_duration:
        with canvas(device) as draw:
            pupil_jitter_x = random.randint(-1, 1) # Small random pupil shifts
            pupil_jitter_y = random.randint(-1, 1)
            current_highlight_pos = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right'])
            
            draw_hunter_eye(draw, center_x, center_y,
                            pupil_y_offset=int(-PUPIL_SIZE * 0.6) + pupil_jitter_y,
                            pupil_x_offset=pupil_jitter_x,
                            eyelid_y_offset=int(EYE_HEIGHT * 0.15),
                            is_happy_squint=True, highlight_pos=current_highlight_pos)
        time.sleep(0.07) # Slightly longer hold frame time

    # Reverse animation back to normal
    for i in range(steps - 1, -1, -1):
        with canvas(device) as draw:
            eyelid_offset = int(EYE_HEIGHT * 0.15 * (i / steps))
            pupil_offset_y = int(-PUPIL_SIZE * 0.6 * (i / steps))
            
            draw_hunter_eye(draw, center_x, center_y,
                            pupil_y_offset=pupil_offset_y,
                            eyelid_y_offset=eyelid_offset,
                            is_happy_squint=True, highlight_pos='top_left') # Highlight returns to default
        time.sleep(0.05)
    time.sleep(0.3) # Pause after returning to normal


def animate_eyes_main_loop():
    """
    Main animation loop that cycles through various eye movements and emotional states
    for a single hunter anime eye.
    """
    # Define a list of all possible eye states/emotions
    eye_states = [
        'normal_straight', 'normal_left', 'normal_right', 'normal_up', 'normal_down',
        'blink', 'happy', 'joy', 'sad', 'surprised', 'wink', 'sleepy'
    ]

    while True:
        state = random.choice(eye_states)
        highlight_choice = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'])

        if state == 'happy':
            animate_happy()
        elif state == 'joy':
            animate_joy()
        elif state == 'blink':
            # Blink animation: open -> closed -> open quickly
            for _ in range(1): # A single blink cycle
                with canvas(device) as draw_blink:
                    draw_closed_eye(draw_blink, center_x, center_y)
                time.sleep(0.1) # Short delay for closed state
                with canvas(device) as draw_open:
                    draw_hunter_eye(draw_open, center_x, center_y, highlight_pos=highlight_choice)
                time.sleep(0.1) # Short delay after opening
            time.sleep(np.random.uniform(0.5, 1.0)) # Pause after the blink sequence
        else:
            with canvas(device) as draw:
                if state == 'normal_straight':
                    draw_hunter_eye(draw, center_x, center_y, highlight_pos=highlight_choice)
                    time.sleep(np.random.uniform(1.0, 3.0))
                elif state == 'normal_left':
                    draw_hunter_eye(draw, center_x, center_y, pupil_x_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                    time.sleep(np.random.uniform(0.5, 1.5))
                elif state == 'normal_right':
                    draw_hunter_eye(draw, center_x, center_y, pupil_x_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                    time.sleep(np.random.uniform(0.5, 1.5))
                elif state == 'normal_up':
                    draw_hunter_eye(draw, center_x, center_y, pupil_y_offset=-PUPIL_SIZE, highlight_pos=highlight_choice)
                    time.sleep(np.random.uniform(0.5, 1.5))
                elif state == 'normal_down':
                    draw_hunter_eye(draw, center_x, center_y, pupil_y_offset=PUPIL_SIZE, highlight_pos=highlight_choice)
                    time.sleep(np.random.uniform(0.5, 1.5))
                elif state == 'sad':
                    # Sad eye: pupil looks slightly down
                    draw_hunter_eye(draw, center_x, center_y, pupil_y_offset=PUPIL_SIZE // 2, highlight_pos='center')
                    time.sleep(np.random.uniform(1.0, 2.5))
                elif state == 'surprised':
                    # Surprised eye: wider, smaller centered pupil
                    temp_eye_height = EYE_HEIGHT + 10 # Make eye taller
                    temp_pupil_size = PUPIL_SIZE // 2 # Smaller pupil
                    
                    draw.ellipse(
                        (center_x - EYE_WIDTH, center_y - temp_eye_height,
                         center_x + EYE_WIDTH, center_y + temp_eye_height),
                        outline="white", fill="black"
                    )
                    draw.ellipse(
                        (center_x - temp_pupil_size, center_y - temp_pupil_size,
                         center_x + temp_pupil_size, center_y + temp_pupil_size),
                        outline="white", fill="white"
                    )
                    # Add highlight for surprised
                    draw.ellipse(
                        (center_x - HIGHLIGHT_SIZE//2, center_y - HIGHLIGHT_SIZE//2,
                         center_x + HIGHLIGHT_SIZE//2, center_y + HIGHLIGHT_SIZE//2),
                        fill="black"
                    )
                    time.sleep(np.random.uniform(0.7, 1.5))
                    # Return to normal after surprise
                    with canvas(device) as draw_norm:
                        draw_hunter_eye(draw_norm, center_x, center_y, highlight_pos=highlight_choice)
                    time.sleep(0.5)
                elif state == 'wink':
                    # Wink: temporary closed eye
                    draw_closed_eye(draw, center_x, center_y)
                    time.sleep(0.3)
                    # Quickly open again
                    with canvas(device) as draw_open:
                        draw_hunter_eye(draw_open, center_x, center_y, highlight_pos=highlight_choice)
                    time.sleep(0.3)
                elif state == 'sleepy':
                    # Sleepy eye: partially closed, low pupil
                    draw.ellipse(
                        (center_x - EYE_WIDTH, center_y - EYE_HEIGHT // 3,
                         center_x + EYE_WIDTH, center_y + EYE_HEIGHT // 3),
                        outline="white", fill="black"
                    )
                    draw.ellipse(
                        (center_x - PUPIL_SIZE // 2, center_y + PUPIL_SIZE // 2,
                         center_x + PUPIL_SIZE // 2, center_y + PUPIL_SIZE + HIGHLIGHT_SIZE),
                        outline="white", fill="white"
                    )
                    time.sleep(np.random.uniform(1.5, 3.0))


# --- Main execution block ---
try:
    if 'device' in locals() and device:
        device.clear() # Clear the display at the very beginning
        print("Starting single hunter anime eye animation...")
        animate_eyes_main_loop()

except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected. Exiting animation.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
finally:
    # This 'finally' block ensures the display is cleared upon script termination.
    if 'device' in locals() and device:
        device.clear() # Send the clear command to turn off all pixels
        # Add a small delay to give the OLED controller time to process the clear command
        time.sleep(0.5)
        print("Display cleared and resources released.")
    else:
        print("Display device not initialized or already cleaned up. No further action needed.")
