# Setup logging
import logging

# Standard dependencies
import time, csv, os

# Device related dependencies
import digitalio
import board
import neopixel
import adafruit_matrixkeypad
import RPi.GPIO as GPIO

# Classes and functions for controlling the conceptual model
from model_helper import *

class LightingController(Model):
    """
    Class providing initialization and usage of the
    Raspberry Pi-based lighting controller for Imani Brown.
    * Raspberry Pi 3 Model B - https://www.raspberrypi.com/products/raspberry-pi-4-model-b/
    * Alitove WS2812B LED Strip 16.4ft (5m) Individually Addressable RGB - https://www.alitove.net/WS2812B
	* OSEPP Ultrasonic Sensor Module [HC-SR04] - http://www.piddlerintheroot.com/hc-sr04/
	* OSEPP Infrared (IR) Detector [IR-DET01] - https://www.osepp.com/electronic-modules/sensor-modules/64-ir-detector
	* Adafruit Membrane 1x4 Keypad - http://adafru.it/1332

    Child class of the Model class, which represents the conceptual model
    of the LED configurations and provides methods for LED brightness/color settings
    """

    def __init__(self, led_brightness=0.5, run_distance_calibration=False ):

        # Run the constructor for the superclass
        super(LightingController, self).__init__()

        # Initialize the controller        
        logging.info("Initialization starting...")
        
        # Initialize the LED Strip
        self.led_strip = None
        logging.info("Initializing the LED Strip")
        self.pixels = self._init_led_strip(brightness=led_brightness)

        # Initialize the Distance Sensors
        self.GPIO_ULTRASONIC = None
        self.CALIBRATION_FILEN = None
        self.baseline_distance = None
        self.calibrated_positions = None        
        logging.info("Initializing the Distance Sensors")
        self._init_distance_sensors(run_distance_calib=run_distance_calibration)

        # Initialize the Proximity Sensors
        self.GPIO_INFRARED = None
        logging.info("Initializing the Proximity Sensors")
        self._init_proximity_sensors()

        # Initialize the Keypad
        self.keypad = None
        logging.info("Initializing the Keypad")
        self._init_keypad()

        # Ready to go
        logging.info("Initialization completed.")


    # *************************************************
    # LED Strip Methods
    # *************************************************

    def _init_led_strip(self, brightness=0.5):
        """
        Initialize the WS2812B LED Strip
        References:
        * https://docs.circuitpython.org/projects/neopixel
        """

        # Initialize the LED strip
        self.led_strip = neopixel.NeoPixel(pin=board.D18, n=300, brightness=brightness)

        # Turn off all LEDs, just in case some were left off
        self.all_leds_off()

        return self.led_strip


    def all_leds_off(self):
        """
        Turn all LEDs off
        """
        self.led_strip.fill( (0,0,0) )


    # Overload this function to replace the simulated LED inteface
    # with the real hardware LED interface
    def draw_model_leds(self, led_colors:dict=None ):
        """
        Set LEDs the physical LED Strip based upon the configurations
        of the model and the color for each LED
        """

        # The input array of colors led_colors must have the
        # same dimensions as the model configuration that provides
        # a mapping to the LED Strip IDs
        assert np.array(led_colors).shape == np.array( self.MODEL_CONFIG[c]['led_ids'] ).shape, "ERROR: led_colors shape must match self.MODEL_CONFIG[c]['led_ids'] shape"

        # Loop through each component of the Model (each side and the top)
        for c in self.MODEL_CONFIG:

            # Use the config info to determine which LED to set
            # for each element of input array led_colors
            for col in range(self.MODEL_CONFIG[c]['leds']['cols']):
                for row in range(self.MODEL_CONFIG[c]['leds']['rows']):

                    # Map input coordinates of a LED to a physical LED index for this component
                    led_id = self.MODEL_CONFIG[c]['led_ids'][row][col]

                    # Set the LED using the specified color
                    # @TODO: Create the function to map a RGB string values to tuples
                    self.led_strip[led_id] = rgb_string_to_tuple( led_colors[c][col][row] )




    # *************************************************
    # Distance (Ultrasonic) Sensor Methods
    # *************************************************

    def _init_distance_sensors( self, run_distance_calib=False ):

        # Set then General Purpose I/O (GPIO) mode:
        # * GPIO.BCM: Specified number refers to logical ports on Raspberry Pi (e.g., GPIO17, GPIO27)
        # * GPIO.BOARD: Specified number refer to physical pins on Raspberry Pi
        GPIO.setmode(GPIO.BCM)

        # Configure the Raspberry Pi GPIO ports used by the Ultrasonic sensors
        self.GPIO_ULTRASONIC = {
            'Right': { 'trigger': 17, 'echo': 27 },
            'Left': { 'trigger': 16, 'echo': 25 }
        }

        # Set the trigger port to output and echo port to input
        for unit in self.GPIO_ULTRASONIC:
            GPIO.setup( self.GPIO_ULTRASONIC[unit]['trigger'], GPIO.OUT)
            GPIO.setup( self.GPIO_ULTRASONIC[unit]['echo'], GPIO.IN)

        # Set the file name of the calibration file
        self.CALIBRATION_FILEN = 'calibration_params.csv'

        # Baseline distance (i.e., no person present)
        self.baseline_distance = None

        # Calibrated positions
        self.calibrated_positions = None

        # Run calibration procedure if requested or if no calibration file exists,
        # which includes saving the results to the calibration file
        if run_distance_calib or ( os.path.exists( self.CALIBRATION_FILEN ) == False ):
            self.baseline_distance, self.calibrated_positions = self._calibrate_distance_sensors()

        # Load calibration parameters if the parameters are not already set
        # and if the calibration file exists
        if (self.calibrated_positions is None) and os.path.exists( self.CALIBRATION_FILEN ):
            self.baseline_distance, self.calibrated_positions = self._load_calibration_parameters()


    def get_distance(self):
        """
        Measure and return the distance for both distance sensors
        and return it as a tuple 
        """

        def _one_sensor_distance( unit=None ):
            """
            Measure the distance for one ultrasonic sensor

            Reference:
            * The OSEPP HC-SR04 ultrasonic sensor module 
            * https://www.osepp.com/electronic-modules/sensor-modules/62-osepp-ultrasonic-sensor-module
            * https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi
            """

            # Speed of sound in centimeters/sec
            SPEED_SOUND_CM = 34300.0

            # Send a trigger pulse to the ultrasonic sensor.
            # Note: A 10 microsecond pulse is required to trigger the sensor.
            GPIO.output(self.GPIO_ULTRASONIC[unit]['trigger'], True)
            time.sleep(10e-6)
            GPIO.output(self.GPIO_ULTRASONIC[unit]['trigger'], False)

            # Prepare to time the echo
            # Note: The sensors sets the 'echo' signal to 1 for the full
            #       for a duration that matches the time between when the trigger
            #       was sent and the echo first received
            start_time = time.time()
            stop_time = time.time()

            # Save Start Time
            while GPIO.input(self.GPIO_ULTRASONIC[unit]['echo']) == 0:
                start_time = time.time()
                
                
            # Save Stop Time
            while GPIO.input(self.GPIO_ULTRASONIC[unit]['echo']) == 1:
                stop_time = time.time()
                
            # Elapsed time
            time_elapsed = stop_time - start_time
            
            # Calculate distance using the time (secs) and speed of sound (cm/sec),
            # then divide by 2 since the sound had to take a round trip to be measured
            distance = (time_elapsed * SPEED_SOUND_CM) / 2.0
            
            return distance

        # Measure the distance on each sensor
        dist = {}
        for unit in self.GPIO_ULTRASONIC:
            # Get the distaince for this unit
            dist[unit] = _one_sensor_distance( unit )

            # Pause for a short period (1 microsecond) before the next measurement,
            # just in case there are reverberations of sound that need to dissipate
            time.sleep(1e-6)

        # Populate the results in a tuple
        return ( dist['Left'], dist['Right'] )


    def _calibrate_distance_sensors( self ):
        """
        Run a semiautomated calibration procedure to
        measure distances with a model person place at
        specific points in the model:
        1. Nothing at the entrance or exit
        2. Person at Entrance (Right, Center, Left)
        3. Person Midway (Right, Center, Left)
        4. Person at Exit (Right, Center, Left)

        Distances are represented by a pair of values:
        (Right Sensor distance [cm], Left Sensor distance [cm])

        Save the calibration parameters to a file.
        """

        # Distance measured by the sensors when no one is present
        baseline_distance = (None, None)

        # Depth (Entrance, Midway, Exit), Side (Right, Center, Left)
        calibrated_positions = {
            'Entrance': { 'Right': (None, None), 'Center': (None, None), 'Left': (None, None) },
            'Midway': { 'Right': (None, None), 'Center': (None, None), 'Left': (None, None) },
            'Exit': { 'Right': (None, None), 'Center': (None, None), 'Left': (None, None) },
        }

        # Obtain distance measurements for calibrated positions
        logging.info("Distance Calibration procedure starting.")

        # Get baseline distance measurement (i.e., no objects nearby)
        logging.info("Step 1 of 10: Baseline distance.")
        _ = input("==> Remove all objects/obstacles from near the model, then press ENTER. ")
        logging.info("Baseline distance measurement starting.")
        baseline_distance = self.get_distance(self)
        logging.info("Baseline distance measurement completed.")

        # Get measurements for the calibrated positions
        logging.info("Calibrated positions distance measurements starting.")
        step = 2
        for depth in ['Entrance', 'Midway', 'Exit']:
            for side in ['Right', 'Center', 'Left']:
                logging.info("Step {step} of 10: '{depth}' and '{side}'")
                _ = input("==> Place the person at '{depth}' and '{side}', then press ENTER. ")
                calibrated_positions[depth][side] = self.get_distance()
                step += 1

        logging.info("Calibrated positions distance measurements completed.")

        # if ok with the user, save the calibration parameters to a file
        response = input("==> Is it OK to save the calibration parameters? [y] / n ")
        if response.lower() != 'n':
            self._save_calibration_parameters( baseline_distance, calibrated_positions )

        logging.info("Distance Calibration completed.")

        # Return the calibration parameters
        return baseline_distance, calibrated_positions


    def _save_calibration_parameters( self, baseline_dist=None, calib_pos=None):
        """
        Save the baseline distance and calibrated positions data to a file
        """
        
        logging.info(f"Saving baseline distance and calibrated parameters: {self.CALIBRATION_FILEN}")
        with open(self.CALIBRATION_FILEN, mode='w') as c_file:
            c_writer = csv.writer( c_file, delimiter=',')

            # Save baseline distance values
            c_writer.writerow( baseline_dist )

            # Save calibrated positions values
            for depth in ['Entrance', 'Midway', 'Exit']:
                for side in ['Right', 'Center', 'Left']:
                    c_writer.writerow( calib_pos[depth][side] )

        logging.info(f"Save completed.")


    def _load_calibration_parameters( self ):
        """
        Load the baseline distance and calibrated positions data from a file
        """
        
        logging.info(f"Loading baseline distance and calibrated parameters: {self.CALIBRATION_FILEN}")
        with open(self.CALIBRATION_FILEN, mode='r') as c_file:
            c_reader = csv.reader( c_file, delimiter=',')

            # Load baseline distance values
            baseline_dist = next(c_reader)

            # Save calibrated positions values
            calib_pos = {}
            for depth in ['Entrance', 'Midway', 'Exit']:
                calib_pos[depth] = {}
                for side in ['Right', 'Center', 'Left']:
                    calib_pos[depth][side] = next(c_reader)

        logging.info(f"Load completed.")

        return baseline_dist, calib_pos



    # *************************************************
    # Proximity (Infrared) Sensor Methods
    # *************************************************

    def _init_proximity_sensors(self):

        # Set then General Purpose I/O (GPIO) mode:
        # * GPIO.BCM: Specified number refers to logical ports on Raspberry Pi (e.g., GPIO22, GPIO12)
        # * GPIO.BOARD: Specified number refer to physical pins on Raspberry Pi
        GPIO.setmode(GPIO.BCM)

        # Infrared sensor configuration
        self.GPIO_INFRARED = {
            'Entrance': { 'signal': 22 },
            'Exit': { 'signal': 12 }
        }

        for unit in self.GPIO_INFRARED:
            GPIO.setup( self.GPIO_INFRARED[unit]['signal'], GPIO.IN)


    def is_object_nearby(self):
        """
        Function to check for proximity using Infrared Sensors
        signal: 0 = An object is nearby, 1 = No object is nearby        
        """

        # Check for proximity on each sensor
        is_nearby = {}
        for unit in self.GPIO_INFRARED:
            # Check proximity for this unit
            is_nearby[unit] = ( GPIO.input(self.GPIO_INFRARED[unit]['signal']) == 0 )

        # Return the dictionary of proximity results
        return is_nearby



    # *************************************************
    # Keypad Methods
    # *************************************************

    def _init_keypad(self):
        
        # Setup keypad configuration amd store the keypad as a property of this object
        keypad_rows = [ digitalio.DigitalInOut(x) for x in (board.D5,) ]
        keypad_cols = [ digitalio.DigitalInOut(x) for x in (board.D26, board.D6, board.D24, board.D23) ]
        keypad_keys = ( (1,2,3,4), )
        self.keypad = adafruit_matrixkeypad.Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

    def get_all_pressed_keys(self):
        return self.keypad.pressed_keys

    def get_max_pressed_key(self):
        try:
            return max( self.keypad.pressed_keys )

        except ValueError:
            return None
