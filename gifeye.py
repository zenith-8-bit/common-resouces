import time
import numpy as np # For random functions and sometimes better randoms
import random # For basic random functions

from luma.core.interface.serial import spi
from luma.core.render import canvas # Still imported but will be used differently
from luma.oled.device import ssd1306, sh1106 # Or just ssd1306 if you know your chip
from PIL import ImageDraw, Image # Import Image for explicit image creation

# --- Configuration for SPI ---
# SPI uses a bus (0 or 1) and device (0 or 1, for CS0 or CS1)
# Most common setup is bus 0, device 0 (CE0)
SPI_BUS = 0
SPI_DEVICE = 0 # Corresponds to CE0 (GPIO 8)

# GPIO pin numbers for DC and RESET (using BCM numbering)
# Ensure these match your wiring!
DC_PIN = 23    # Connected to GPIO 23 (Physical Pin 16)
RST_PIN = 24  # Connected to GPIO 24 (Physical Pin 18)

# --- OLED Device Initialization ---
# Initialize device to None, so we can check if it was successful later
oled_device = None
try:
    serial = spi(port=SPI_BUS, device=SPI_DEVICE, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
    oled_device = ssd1306(serial) # Attempt to initialize SSD1306
    print(f"OLED display initialized: {oled_device.width}x{oled_device.height}")
except Exception as e:
    print(f"Error initializing OLED device: {e}")
    print("Please ensure your wiring is correct and the luma.oled library is installed.")
    print("Exiting as display device could not be initialized.")
    exit() # Exit if device cannot be initialized, as it's critical

# --- Usage of monochrome display colors ---
# In Pillow, '0' is black, '1' is white for 1-bit images.
BGCOLOR = 0 # background and overlays
MAINCOLOR = 1 # drawings

# For mood type switch
DEFAULT = 0
TIRED = 1
ANGRY = 2
HAPPY = 3

# For turning things on or off
ON = 1
OFF = 0

# For switch "predefined positions"
N = 1 # north, top center
NE = 2 # north-east, top right
E = 3 # east, middle right
SE = 4 # south-east, bottom right
S = 5 # south, bottom center
SW = 6 # south-west, bottom left
W = 7 # west, middle left
NW = 8 # north-west, top left
# for middle center set "DEFAULT"

class RoboEyes:
    def __init__(self, display_device):
        """
        Initializes the RoboEyes class with the OLED display device.
        All parameters are mirrored from the C++ version.
        """
        self.device = display_device

        # For general setup - screen size and max. frame rate
        self.screenWidth = self.device.width  # OLED display width, in pixels
        self.screenHeight = self.device.height # OLED display height, in pixels
        self.frameInterval = 20  # default value for 50 frames per second (1000/50 = 20 milliseconds)
        self.fpsTimer = 0  # for timing the frames per second (using time.monotonic_ns for precision)

        # For controlling mood types and expressions
        self.tired = False
        self.angry = False
        self.happy = False
        self.curious = False # if true, draw the outer eye larger when looking left or right
        self.cyclops = False # if true, draw only one eye
        self.eyeL_open = False # left eye opened or closed?
        self.eyeR_open = False # right eye opened or closed?

        # *********************************************************************************************
        # Eyes Geometry
        # *********************************************************************************************

        # EYE LEFT - size and border radius
        self.eyeLwidthDefault = 36
        self.eyeLheightDefault = 36
        self.eyeLwidthCurrent = self.eyeLwidthDefault
        self.eyeLheightCurrent = 1 # start with closed eye, otherwise set to eyeLheightDefault
        self.eyeLwidthNext = self.eyeLwidthDefault
        self.eyeLheightNext = self.eyeLheightDefault
        self.eyeLheightOffset = 0
        # Border Radius
        self.eyeLborderRadiusDefault = 8
        self.eyeLborderRadiusCurrent = self.eyeLborderRadiusDefault
        self.eyeLborderRadiusNext = self.eyeLborderRadiusDefault

        # EYE RIGHT - size and border radius
        self.eyeRwidthDefault = self.eyeLwidthDefault
        self.eyeRheightDefault = self.eyeLheightDefault
        self.eyeRwidthCurrent = self.eyeRwidthDefault
        self.eyeRheightCurrent = 1 # start with closed eye, otherwise set to eyeRheightDefault
        self.eyeRwidthNext = self.eyeRwidthDefault
        self.eyeRheightNext = self.eyeRheightDefault
        self.eyeRheightOffset = 0
        # Border Radius
        self.eyeRborderRadiusDefault = 8
        self.eyeRborderRadiusCurrent = self.eyeRborderRadiusDefault
        self.eyeRborderRadiusNext = self.eyeRborderRadiusDefault

        # EYE LEFT - Coordinates
        # These will be initialized properly in the begin() method after screen dimensions are set
        self.spaceBetweenDefault = 10 # Default space between eyes
        self.eyeLxDefault = ((self.screenWidth) - (self.eyeLwidthDefault + self.spaceBetweenDefault + self.eyeRwidthDefault)) // 2
        self.eyeLyDefault = ((self.screenHeight - self.eyeLheightDefault) // 2)
        self.eyeLx = self.eyeLxDefault
        self.eyeLy = self.eyeLyDefault
        self.eyeLxNext = self.eyeLx
        self.eyeLyNext = self.eyeLy

        # EYE RIGHT - Coordinates
        self.eyeRxDefault = self.eyeLx + self.eyeLwidthCurrent + self.spaceBetweenDefault
        self.eyeRyDefault = self.eyeLy
        self.eyeRx = self.eyeRxDefault
        self.eyeRy = self.eyeRyDefault
        self.eyeRxNext = self.eyeRx
        self.eyeRyNext = self.eyeRy

        # BOTH EYES
        # Eyelid top size
        self.eyelidsHeightMax = self.eyeLheightDefault // 2  # top eyelids max height
        self.eyelidsTiredHeight = 0
        self.eyelidsTiredHeightNext = self.eyelidsTiredHeight
        self.eyelidsAngryHeight = 0
        self.eyelidsAngryHeightNext = self.eyelidsAngryHeight
        # Bottom happy eyelids offset
        self.eyelidsHappyBottomOffsetMax = (self.eyeLheightDefault // 2) + 3
        self.eyelidsHappyBottomOffset = 0
        self.eyelidsHappyBottomOffsetNext = 0
        # Space between eyes
        self.spaceBetweenCurrent = self.spaceBetweenDefault
        self.spaceBetweenNext = 10

        # *********************************************************************************************
        # Macro Animations
        # *********************************************************************************************

        # Animation - horizontal flicker/shiver
        self.hFlicker = False
        self.hFlickerAlternate = False
        self.hFlickerAmplitude = 2

        # Animation - vertical flicker/shiver
        self.vFlicker = False
        self.vFlickerAlternate = False
        self.vFlickerAmplitude = 10

        # Animation - auto blinking
        self.autoblinker = False # activate auto blink animation
        self.blinkInterval = 1 # basic interval between each blink in full seconds
        self.blinkIntervalVariation = 4 # interval variaton range in full seconds, random number inside of given range will be add to the basic blinkInterval, set to 0 for no variation
        self.blinktimer = 0 # for organising eyeblink timing (using time.monotonic_ns)

        # Animation - idle mode: eyes looking in random directions
        self.idle = False
        self.idleInterval = 1 # basic interval between each eye repositioning in full seconds
        self.idleIntervalVariation = 3 # interval variaton range in full seconds, random number inside of given range will be add to the basic idleInterval, set to 0 for no variation
        self.idleAnimationTimer = 0 # for organising eyeblink timing

        # Animation - eyes confused: eyes shaking left and right
        self.confused = False
        self.confusedAnimationTimer = 0
        self.confusedAnimationDuration = 500 # milliseconds
        self.confusedToggle = True

        # Animation - eyes laughing: eyes shaking up and down
        self.laugh = False
        self.laughAnimationTimer = 0
        self.laughAnimationDuration = 500 # milliseconds
        self.laughToggle = True


    # *********************************************************************************************
    # GENERAL METHODS
    # *********************************************************************************************

    def begin(self, width, height, frameRate):
        """
        Startup RoboEyes with defined screen-width, screen-height and max. frame rate.
        """
        self.screenWidth = width
        self.screenHeight = height
        self.device.clear() # clear the display buffer
        self.device.display() # show empty screen
        self.eyeLheightCurrent = 1 # start with closed eyes
        self.eyeRheightCurrent = 1 # start with closed eyes
        self.setFramerate(frameRate) # calculate frame interval based on defined frameRate

        # Re-calculate default eye positions based on new screen dimensions
        self.eyeLxDefault = ((self.screenWidth) - (self.eyeLwidthDefault + self.spaceBetweenDefault + self.eyeRwidthDefault)) // 2
        self.eyeLyDefault = ((self.screenHeight - self.eyeLheightDefault) // 2)
        self.eyeLx = self.eyeLxDefault
        self.eyeLy = self.eyeLyDefault
        self.eyeLxNext = self.eyeLx
        self.eyeLyNext = self.eyeLy
        self.eyeRxDefault = self.eyeLx + self.eyeLwidthCurrent + self.spaceBetweenDefault
        self.eyeRyDefault = self.eyeLy
        self.eyeRx = self.eyeRxDefault
        self.eyeRy = self.eyeRyDefault
        self.eyeRxNext = self.eyeRx
        self.eyeRyNext = self.eyeRy

    def update(self):
        """
        Limit drawing updates to defined max framerate.
        """
        current_time_ms = time.monotonic_ns() // 1_000_000 # Convert nanoseconds to milliseconds
        if current_time_ms - self.fpsTimer >= self.frameInterval:
            self.drawEyes()
            self.fpsTimer = current_time_ms

    # *********************************************************************************************
    # SETTERS METHODS
    # *********************************************************************************************

    def setFramerate(self, fps):
        """Calculate frame interval based on defined frameRate."""
        self.frameInterval = 1000 // fps

    def setWidth(self, leftEye, rightEye):
        self.eyeLwidthNext = leftEye
        self.eyeRwidthNext = rightEye
        self.eyeLwidthDefault = leftEye
        self.eyeRwidthDefault = rightEye

    def setHeight(self, leftEye, rightEye):
        self.eyeLheightNext = leftEye
        self.eyeRheightNext = rightEye
        self.eyeLheightDefault = leftEye
        self.eyeRheightDefault = rightEye

    def setBorderradius(self, leftEye, rightEye):
        """Set border radius for left and right eye."""
        self.eyeLborderRadiusNext = leftEye
        self.eyeRborderRadiusNext = rightEye
        self.eyeLborderRadiusDefault = leftEye
        self.eyeRborderRadiusDefault = rightEye

    def setSpacebetween(self, space):
        """Set space between the eyes, can also be negative."""
        self.spaceBetweenNext = space
        self.spaceBetweenDefault = space

    def setMood(self, mood):
        """Set mood expression."""
        self.tired = False
        self.angry = False
        self.happy = False
        if mood == TIRED:
            self.tired = True
        elif mood == ANGRY:
            self.angry = True
        elif mood == HAPPY:
            self.happy = True

    def setPosition(self, position):
        """Set predefined position."""
        if position == N:
            self.eyeLxNext = self.getScreenConstraint_X() // 2
            self.eyeLyNext = 0
        elif position == NE:
            self.eyeLxNext = self.getScreenConstraint_X()
            self.eyeLyNext = 0
        elif position == E:
            self.eyeLxNext = self.getScreenConstraint_X()
            self.eyeLyNext = self.getScreenConstraint_Y() // 2
        elif position == SE:
            self.eyeLxNext = self.getScreenConstraint_X()
            self.eyeLyNext = self.getScreenConstraint_Y()
        elif position == S:
            self.eyeLxNext = self.getScreenConstraint_X() // 2
            self.eyeLyNext = self.getScreenConstraint_Y()
        elif position == SW:
            self.eyeLxNext = 0
            self.eyeLyNext = self.getScreenConstraint_Y()
        elif position == W:
            self.eyeLxNext = 0
            self.eyeLyNext = self.getScreenConstraint_Y() // 2
        elif position == NW:
            self.eyeLxNext = 0
            self.eyeLyNext = 0
        else: # DEFAULT (middle center)
            self.eyeLxNext = self.getScreenConstraint_X() // 2
            self.eyeLyNext = self.getScreenConstraint_Y() // 2

    def setAutoblinker(self, active, interval=1, variation=0):
        """Set automated eye blinking."""
        self.autoblinker = active
        self.blinkInterval = interval
        self.blinkIntervalVariation = variation
        # Initialize timer if activating
        if active:
            self.blinktimer = time.monotonic_ns() // 1_000_000 + (self.blinkInterval * 1000) + (random.randint(0, self.blinkIntervalVariation) * 1000)

    def setIdleMode(self, active, interval=1, variation=0):
        """Set idle mode - automated eye repositioning."""
        self.idle = active
        self.idleInterval = interval
        self.idleIntervalVariation = variation
        # Initialize timer if activating
        if active:
            self.idleAnimationTimer = time.monotonic_ns() // 1_000_000 + (self.idleInterval * 1000) + (random.randint(0, self.idleIntervalVariation) * 1000)


    def setCuriosity(self, curiousBit):
        """Set curious mode."""
        self.curious = curiousBit

    def setCyclops(self, cyclopsBit):
        """Set cyclops mode - show only one eye."""
        self.cyclops = cyclopsBit

    def setHFlicker(self, flickerBit, amplitude=2):
        """Set horizontal flickering (displacing eyes left/right)."""
        self.hFlicker = flickerBit
        self.hFlickerAmplitude = amplitude

    def setVFlicker(self, flickerBit, amplitude=10):
        """Set vertical flickering (displacing eyes up/down)."""
        self.vFlicker = flickerBit
        self.vFlickerAmplitude = amplitude

    # *********************************************************************************************
    # GETTERS METHODS
    # *********************************************************************************************

    def getScreenConstraint_X(self):
        """Returns the max x position for left eye."""
        return self.screenWidth - self.eyeLwidthCurrent - self.spaceBetweenCurrent - self.eyeRwidthCurrent

    def getScreenConstraint_Y(self):
        """Returns the max y position for left eye."""
        return self.screenHeight - self.eyeLheightDefault

    # *********************************************************************************************
    # BASIC ANIMATION METHODS
    # *********************************************************************************************

    def close(self, left=True, right=True):
        """Close eye(s)."""
        if left:
            self.eyeLheightNext = 1
            self.eyeL_open = False
        if right:
            self.eyeRheightNext = 1
            self.eyeR_open = False

    def open(self, left=True, right=True):
        """Open eye(s)."""
        if left:
            self.eyeL_open = True
            self.eyeLheightNext = self.eyeLheightDefault # Ensure target height is default
        if right:
            self.eyeR_open = True
            self.eyeRheightNext = self.eyeRheightDefault # Ensure target height is default

    def blink(self, left=True, right=True):
        """Trigger eyeblink animation."""
        self.close(left, right)
        # The 'open' will be handled by drawEyes() as eyeL_open/eyeR_open flags are set

    # *********************************************************************************************
    # MACRO ANIMATION METHODS
    # *********************************************************************************************

    def anim_confused(self):
        """Play confused animation - one shot animation of eyes shaking left and right."""
        self.confused = True
        self.confusedToggle = True # Reset toggle for a fresh animation start

    def anim_laugh(self):
        """Play laugh animation - one shot animation of eyes shaking up and down."""
        self.laugh = True
        self.laughToggle = True # Reset toggle for a fresh animation start

    # *********************************************************************************************
    # PRE-CALCULATIONS AND ACTUAL DRAWINGS
    # *********************************************************************************************

    def drawEyes(self):
        """
        Performs pre-calculations for eye sizes and animation tweening,
        applies macro animations, and then draws the eyes on the display.
        """
        # Get current time in milliseconds for timers
        current_time_ms = time.monotonic_ns() // 1_000_000

        #### PRE-CALCULATIONS - EYE SIZES AND VALUES FOR ANIMATION TWEENINGS ####

        # Vertical size offset for larger eyes when looking left or right (curious gaze)
        if self.curious:
            if self.eyeLxNext <= 10: # Looking far left
                self.eyeLheightOffset = 8
            elif self.eyeLxNext >= (self.getScreenConstraint_X() - 10) and self.cyclops: # Looking far right in cyclops mode
                self.eyeLheightOffset = 8
            else:
                self.eyeLheightOffset = 0 # left eye
            
            if self.eyeRxNext >= self.screenWidth - self.eyeRwidthCurrent - 10: # Looking far right
                self.eyeRheightOffset = 8
            else:
                self.eyeRheightOffset = 0 # right eye
        else:
            self.eyeLheightOffset = 0 # reset height offset for left eye
            self.eyeRheightOffset = 0 # reset height offset for right eye

        # Left eye height tweening
        self.eyeLheightCurrent = int((self.eyeLheightCurrent + self.eyeLheightNext + self.eyeLheightOffset) / 2)
        # Vertical centering of eye when closing (adjusting eyeLy)
        self.eyeLy += ((self.eyeLheightDefault - self.eyeLheightCurrent) // 2)
        self.eyeLy -= self.eyeLheightOffset // 2

        # Right eye height tweening
        self.eyeRheightCurrent = int((self.eyeRheightCurrent + self.eyeRheightNext + self.eyeRheightOffset) / 2)
        # Vertical centering of eye when closing (adjusting eyeRy)
        self.eyeRy += (self.eyeRheightDefault - self.eyeRheightCurrent) // 2
        self.eyeRy -= self.eyeRheightOffset // 2

        # Open eyes again after closing them (if eye_open flag is True)
        if self.eyeL_open:
            if self.eyeLheightCurrent <= 1 + self.eyeLheightOffset:
                self.eyeLheightNext = self.eyeLheightDefault
            # This 'else' clause should only execute if the eye is already fully open and the flag needs resetting.
            # However, the blink() method sets eyeL_open=True, and it should become False only when eyeLheightCurrent reaches default.
            # The current logic will keep eyeL_open true, and eyeLheightNext will keep being set to default if current is <= 1.
            # Let's refine this: only set eyeL_open to False once it has *fully* opened.
            # For this simple tweening, it's fine as long as eyeLheightNext is consistently set.

        if self.eyeR_open:
            if self.eyeRheightCurrent <= 1 + self.eyeRheightOffset:
                self.eyeRheightNext = self.eyeRheightDefault
            # See comment above for eyeL_open

        # Left eye width tweening
        self.eyeLwidthCurrent = int((self.eyeLwidthCurrent + self.eyeLwidthNext) / 2)
        # Right eye width tweening
        self.eyeRwidthCurrent = int((self.eyeRwidthCurrent + self.eyeRwidthNext) / 2)

        # Space between eyes tweening
        self.spaceBetweenCurrent = int((self.spaceBetweenCurrent + self.spaceBetweenNext) / 2)

        # Left eye coordinates tweening
        self.eyeLx = int((self.eyeLx + self.eyeLxNext) / 2)
        self.eyeLy = int((self.eyeLy + self.eyeLyNext) / 2)

        # Right eye coordinates (dependent on left eye's position and space between)
        self.eyeRxNext = self.eyeLxNext + self.eyeLwidthCurrent + self.spaceBetweenCurrent
        self.eyeRyNext = self.eyeLyNext # right eye's y position should be the same as for the left eye
        self.eyeRx = int((self.eyeRx + self.eyeRxNext) / 2)
        self.eyeRy = int((self.eyeRy + self.eyeRyNext) / 2)

        # Left eye border radius tweening
        self.eyeLborderRadiusCurrent = int((self.eyeLborderRadiusCurrent + self.eyeLborderRadiusNext) / 2)
        # Right eye border radius tweening
        self.eyeRborderRadiusCurrent = int((self.eyeRborderRadiusCurrent + self.eyeRborderRadiusNext) / 2)

        #### APPLYING MACRO ANIMATIONS ####

        if self.autoblinker:
            if current_time_ms >= self.blinktimer:
                self.blink()
                self.blinktimer = current_time_ms + (self.blinkInterval * 1000) + (random.randint(0, self.blinkIntervalVariation) * 1000)

        # Laughing - eyes shaking up and down
        if self.laugh:
            if self.laughToggle:
                self.setVFlicker(True, 5) # Activate vertical flicker
                self.laughAnimationTimer = current_time_ms
                self.laughToggle = False
            elif current_time_ms >= self.laughAnimationTimer + self.laughAnimationDuration:
                self.setVFlicker(False, 0) # Deactivate vertical flicker
                self.laughToggle = True
                self.laugh = False

        # Confused - eyes shaking left and right
        if self.confused:
            if self.confusedToggle:
                self.setHFlicker(True, 20) # Activate horizontal flicker
                self.confusedAnimationTimer = current_time_ms
                self.confusedToggle = False
            elif current_time_ms >= self.confusedAnimationTimer + self.confusedAnimationDuration:
                self.setHFlicker(False, 0) # Deactivate horizontal flicker
                self.confusedToggle = True
                self.confused = False

        # Idle - eyes moving to random positions on screen
        if self.idle:
            if current_time_ms >= self.idleAnimationTimer:
                self.eyeLxNext = random.randint(0, self.getScreenConstraint_X())
                self.eyeLyNext = random.randint(0, self.getScreenConstraint_Y())
                self.idleAnimationTimer = current_time_ms + (self.idleInterval * 1000) + (random.randint(0, self.idleIntervalVariation) * 1000)

        # Adding offsets for horizontal flickering/shivering
        if self.hFlicker:
            if self.hFlickerAlternate:
                self.eyeLx += self.hFlickerAmplitude
                self.eyeRx += self.hFlickerAmplitude
            else:
                self.eyeLx -= self.hFlickerAmplitude
                self.eyeRx -= self.hFlickerAmplitude
            self.hFlickerAlternate = not self.hFlickerAlternate

        # Adding offsets for vertical flickering/shivering
        if self.vFlicker:
            if self.vFlickerAlternate:
                self.eyeLy += self.vFlickerAmplitude
                self.eyeRy += self.vFlickerAmplitude
            else:
                self.eyeLy -= self.vFlickerAmplitude
                self.eyeRy -= self.vFlickerAmplitude
            self.vFlickerAlternate = not self.vFlickerAlternate

        # Cyclops mode, set second eye's size and space between to 0
        if self.cyclops:
            self.eyeRwidthCurrent = 0
            self.eyeRheightCurrent = 0
            self.spaceBetweenCurrent = 0

        #### ACTUAL DRAWINGS ####

        # Explicitly create an Image and ImageDraw object for drawing.
        # This replaces the 'with canvas(self.device) as draw:' block.
        image = Image.new('1', (self.screenWidth, self.screenHeight)) # Create a blank 1-bit image
        draw = ImageDraw.Draw(image) # Get a drawing object for this image

        # Clear the image buffer with background color (ensures previous frame is wiped)
        draw.rectangle((0, 0, self.screenWidth, self.screenHeight), fill=BGCOLOR)

        # Draw basic eye rectangles
        # Pillow's rounded_rectangle expects (x0, y0, x1, y1)
        # x0,y0 = top-left; x1,y1 = bottom-right
        draw.rounded_rectangle(
            (self.eyeLx, self.eyeLy, self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyeLheightCurrent),
            radius=self.eyeLborderRadiusCurrent,
            fill=MAINCOLOR
        )

        if not self.cyclops:
            draw.rounded_rectangle(
                (self.eyeRx, self.eyeRy, self.eyeRx + self.eyeRwidthCurrent, self.eyeRy + self.eyeRheightCurrent),
                radius=self.eyeRborderRadiusCurrent,
                fill=MAINCOLOR
            )

        # Prepare mood type transitions
        if self.tired:
            self.eyelidsTiredHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsAngryHeightNext = 0
        else:
            self.eyelidsTiredHeightNext = 0

        if self.angry:
            self.eyelidsAngryHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsTiredHeightNext = 0
        else:
            self.eyelidsAngryHeightNext = 0

        if self.happy:
            self.eyelidsHappyBottomOffsetNext = self.eyeLheightCurrent // 2
        else:
            self.eyelidsHappyBottomOffsetNext = 0

        # Draw tired top eyelids (triangles for a pointed look)
        self.eyelidsTiredHeight = int((self.eyelidsTiredHeight + self.eyelidsTiredHeightNext) / 2)
        if self.eyelidsTiredHeight > 0:
            if not self.cyclops:
                # Left eye tired eyelid
                draw.polygon([
                    (self.eyeLx, self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                    (self.eyeLx, self.eyeLy + self.eyelidsTiredHeight)
                ], fill=BGCOLOR)
                # Right eye tired eyelid
                draw.polygon([
                    (self.eyeRx, self.eyeRy),
                    (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy),
                    (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy + self.eyelidsTiredHeight)
                ], fill=BGCOLOR)
            else:
                # Cyclops tired eyelids
                draw.polygon([
                    (self.eyeLx, self.eyeLy),
                    (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                    (self.eyeLx, self.eyeLy + self.eyelidsTiredHeight)
                ], fill=BGCOLOR)
                draw.polygon([
                    (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsTiredHeight)
                ], fill=BGCOLOR)

        # Draw angry top eyelids (triangles for a furrowed brow look)
        self.eyelidsAngryHeight = int((self.eyelidsAngryHeight + self.eyelidsAngryHeightNext) / 2)
        if self.eyelidsAngryHeight > 0:
            if not self.cyclops:
                # Left eye angry eyelid
                draw.polygon([
                    (self.eyeLx, self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsAngryHeight)
                ], fill=BGCOLOR)
                # Right eye angry eyelid
                draw.polygon([
                    (self.eyeRx, self.eyeRy),
                    (self.eyeRx + self.eyeRwidthCurrent, self.eyeRy),
                    (self.eyeRx, self.eyeRy + self.eyelidsAngryHeight)
                ], fill=BGCOLOR)
            else:
                # Cyclops angry eyelids
                draw.polygon([
                    (self.eyeLx, self.eyeLy),
                    (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                    (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy + self.eyelidsAngryHeight)
                ], fill=BGCOLOR)
                draw.polygon([
                    (self.eyeLx + (self.eyeLwidthCurrent // 2), self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy),
                    (self.eyeLx + self.eyeLwidthCurrent, self.eyeLy + self.eyelidsAngryHeight)
                ], fill=BGCOLOR)

        # Draw happy bottom eyelids (rounded rectangles covering lower part)
        self.eyelidsHappyBottomOffset = int((self.eyelidsHappyBottomOffset + self.eyelidsHappyBottomOffsetNext) / 2)
        if self.eyelidsHappyBottomOffset > 0:
            # Left eye happy eyelid
            draw.rounded_rectangle(
                (self.eyeLx - 1, (self.eyeLy + self.eyeLheightCurrent) - self.eyelidsHappyBottomOffset + 1,
                 self.eyeLx + self.eyeLwidthCurrent + 2, self.eyeLy + self.eyeLheightCurrent + self.eyeLheightDefault),
                radius=self.eyeLborderRadiusCurrent,
                fill=BGCOLOR
            )
            if not self.cyclops:
                # Right eye happy eyelid
                draw.rounded_rectangle(
                    (self.eyeRx - 1, (self.eyeRy + self.eyeRheightCurrent) - self.eyelidsHappyBottomOffset + 1,
                     self.eyeRx + self.eyeRwidthCurrent + 2, self.eyeRy + self.eyeRheightCurrent + self.eyeRheightDefault),
                    radius=self.eyeRborderRadiusCurrent,
                    fill=BGCOLOR
                )

        # Finally, display the prepared image on the OLED device
        self.device.display(image)


# --- Main execution block ---
# This block handles the starting of the animation and ensures proper cleanup
# if the script is interrupted or finishes.
if oled_device: # Proceed only if the device was successfully initialized
    try:
        eyes = RoboEyes(oled_device)
        eyes.begin(oled_device.width, oled_device.height, 50) # Initialize with screen size and 50 FPS

        # --- Example Usage / Animation Loop ---
        print("RoboEyes animation starting...")

        # Example sequence:
        eyes.setIdleMode(True, 2, 3) # Eyes move randomly
        eyes.setAutoblinker(True, 1, 4) # Auto blinking
        eyes.setCuriosity(True) # Eyes get larger when looking side to side

        # To demonstrate mood changes:
        mood_timer = time.monotonic_ns() // 1_000_000
        current_mood_idx = 0
        moods = [DEFAULT, HAPPY, ANGRY, TIRED]
        
        while True:
            eyes.update() # This calls drawEyes() and handles FPS

            # Change mood every few seconds
            if (time.monotonic_ns() // 1_000_000) - mood_timer >= 5000: # Change mood every 5 seconds
                current_mood_idx = (current_mood_idx + 1) % len(moods)
                eyes.setMood(moods[current_mood_idx])
                mood_timer = time.monotonic_ns() // 1_000_000
                print(f"Changing mood to: {['DEFAULT', 'HAPPY', 'ANGRY', 'TIRED'][current_mood_idx]}")

            # Trigger one-shot animations occasionally
            if random.random() < 0.01: # 1% chance each frame to trigger confused
                eyes.anim_confused()
                print("Triggered Confused animation!")
            if random.random() < 0.01: # 1% chance each frame to trigger laugh
                eyes.anim_laugh()
                print("Triggered Laugh animation!")
            
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Exiting animation.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # This 'finally' block *always* executes, whether an exception occurred or not.
        if oled_device:
            oled_device.clear() # Send the clear command to turn off all pixels
            time.sleep(0.5) # Add a small delay to give the OLED controller time to process
            print("Display cleared and resources released.")
else:
    print("OLED device not initialized. Cannot run animation.")
