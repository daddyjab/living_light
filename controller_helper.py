# Setup logging
import logging

# Standard dependencies
import time, csv, os

import numpy as np
from numpy.polynomial import Polynomial

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

    def __init__(self, led_brightness=0.1, run_distance_calibration=False ):

        # Run the constructor for the superclass
        super(LightingController, self).__init__()

        # Initialize the controller        
        logging.info("Initialization starting...")
        
        # Initialize the LED Strip
        self.led_strip = None
        logging.info("Initializing the LED Strip")
        self._init_led_strip(brightness=led_brightness)

        # Initialize the Distance Sensors
        self.GPIO_ULTRASONIC = None
        self.CALIBRATION_FILEN = None
        self.baseline_distance = None
        self.calibrated_positions = None        
        self.normalizing_polys = None
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

    def _init_led_strip(self, brightness=0.1):
        """
        Initialize the WS2812B LED Strip
        References:
        * https://docs.circuitpython.org/projects/neopixel
        """

        # Initialize the LED strip
        self.led_strip = neopixel.NeoPixel(pin=board.D18, n=268, auto_write=False, brightness=brightness)

        # Turn off all LEDs, just in case some were left off
        self.all_leds_off()


    def all_leds_off(self):
        """
        Turn all LEDs off
        """
        self.led_strip.fill( (0,0,0) )
        self.led_strip.show()

    def all_leds_on(self):
        """
        Turn all LEDs off
        """
        self.led_strip.fill( (255,255,255) )
        self.led_strip.show()

    def highlight_every_tenth_led(self):
        """
        Make every ten LEDs bright (to facilitate counting, finding a particular LED ID, etc.)
        """

        # Turn all LEDs to partial brightness
        self.led_strip.fill( (32,32,32) )

        # Turn every 10th LED to full brightness
        self.led_strip[::10] = [ (255,255,255) for i in range(len(self.led_strip[::10])) ]        
        self.led_strip.show()


    # Overload this function to replace the simulated LED inteface
    # with the real hardware LED interface
    def draw_model_leds(self):
        """
        Set LEDs the physical LED Strip based upon the configurations
        of the model and the color for each LED
        """

        # Loop through each component of the Model (sides Right and Left)
        for c in self.MODEL_CONFIG:

            # Use numpy iterator to set the LED color values
            with np.nditer( self.led_array[c], flags=['multi_index'], op_flags=['readonly']) as la_iter:
                for led_col in la_iter:

                    # Map input coordinates of a LED to a physical LED index for this component
                    led_id = self.MODEL_CONFIG[c]['led_ids'][ la_iter.multi_index[0] ][ la_iter.multi_index[1] ]

                    # If an actual LED ID is populated, then set the LED using the specified color
                    if led_id:
                        # # Color is specified as RGB tuple
                        # self.led_strip[led_id] = rgb_int_to_tuple( led_col[...] )

                        # Color is specified as integer-encoded RGB value
                        self.led_strip[led_id] = int(led_col[...])

        # Show the revised LED colors on the LED Strip
        self.led_strip.show()




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
            'Right': { 'trigger': 17, 'echo': 27, 'working': True },
            'Left': { 'trigger': 16, 'echo': 25, 'working': True }
        }

        # Set the trigger port to output and echo port to input
        for unit in self.GPIO_ULTRASONIC:
            GPIO.setup( self.GPIO_ULTRASONIC[unit]['trigger'], GPIO.OUT)
            GPIO.setup( self.GPIO_ULTRASONIC[unit]['echo'], GPIO.IN)

        # Model inside dimensions (centimeters)
        self.PHYSICAL_DIMENSIONS = {
            'depth':  30.48,  # 12 inches
            'height': 20.32,  #  8 inches
            'width':  15.28,  #  6 inches
        }

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
            
        # Calculate distance normalizing polynomials, such that distance is normalized
        # the calibrated positions for Entrance to Exit are normalized to 1.0 to 0.0
        self.normalizing_polys = self._calc_normalizing_polys()


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

            # If this sensor has already been determined to be not working
            # then return distance of None
            if self.GPIO_ULTRASONIC[unit]['working'] == False:
                return None

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

            # If a sensor request takes longer than the TIMEOUT_TARGET (5.0 sec),
            # then mark the sensor as being not working
            TIMEOUT_TARGET = 5.0

            # Save Start Time
            timeout_time = time.time()
            while GPIO.input(self.GPIO_ULTRASONIC[unit]['echo']) == 0:
                start_time = time.time()

                # Check if this operation is taking too long
                if start_time - timeout_time > TIMEOUT_TARGET:

                    # Sensor request timed out!
                    # Mark this sensor as not working
                    logging.error(f"Ultrasonic Distance Sensor [unit='{unit}'] is not responding - marking it as not working")
                    self.GPIO_ULTRASONIC[unit]['working'] = False

                    # Return a distance value of None
                    return None
                
                
            # Save Stop Time
            timeout_time = time.time()
            while GPIO.input(self.GPIO_ULTRASONIC[unit]['echo']) == 1:
                stop_time = time.time()

                # Check if this operation is taking too long
                if stop_time - timeout_time > TIMEOUT_TARGET:

                    # Sensor request timed out!
                    # Mark this sensor as not working
                    logging.error(f"Ultrasonic Distance Sensor [unit='{unit}'] is not responding - marking it as not working")
                    self.GPIO_ULTRASONIC[unit]['working'] = False

                    # Return a distance value of None
                    return None


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
            # Revised: No additional delay is needed
            # time.sleep(1e-6)

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
        baseline_distance = self.get_distance()
        logging.info("Baseline distance measurement completed.")

        # Get measurements for the calibrated positions
        logging.info("Calibrated positions distance measurements starting.")
        step = 2
        for depth in ['Entrance', 'Midway', 'Exit']:
            for side in ['Right', 'Center', 'Left']:
                logging.info(f"Step {step} of 10: '{depth}' and '{side}'")
                _ = input(f"==> Place the person at '{depth}' and '{side}', then press ENTER. ")
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
        with open(self.CALIBRATION_FILEN, mode='w', newline='') as c_file:
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
        with open(self.CALIBRATION_FILEN, mode='r', newline='') as c_file:
            c_reader = csv.reader( c_file, delimiter=',')

            # Load baseline distance values
            dist_left, dist_right = next(c_reader)
            try:
                dist_left = float(dist_left)

            except ValueError:
                dist_left = None

            try:
                dist_right = float(dist_right)

            except ValueError:
                dist_right = None

            baseline_dist = dist_left, dist_right

            # Save calibrated positions values
            calib_pos = {}
            for depth in ['Entrance', 'Midway', 'Exit']:
                calib_pos[depth] = {}
                for side in ['Right', 'Center', 'Left']:
                    dist_left, dist_right = next(c_reader)
                    try:
                        dist_left = float(dist_left)

                    except ValueError:
                        dist_left = None

                    try:
                        dist_right = float(dist_right)

                    except ValueError:
                        dist_right = None

                    calib_pos[depth][side] = dist_left, dist_right

        logging.info(f"Load completed.")

        return baseline_dist, calib_pos


    def _calc_normalizing_polys( self ) -> tuple:
        """
        Fit the calibrated positions data to a polynomial (linear) for distance,
        with a separate equations for the Left (0) and Right (1) sensors.
        This will allow distance from Entrance to Midway to Exit to be mapped to a value 1.0 to 0.5 to 0.0 (approximately).
        """

        # Use Calibrated Position measurements that are more in line with each distance sensor:
        # * Left sensor (0):  Use Left and Center calibrated position measurements
        # * Right sensor (1), Use Right and Center calibrated position measurements
        # NOTE: Right sensor no longer available, so only left sensor will be used in calcs
        SIDES_FOR_SENSORS = { 0: [ 'Left', 'Center' ], 1: [ 'Right', 'Center' ] }

        poly = {}
        for sensor in [0]:

            # Build a set of x,y points to be fitted for this sensor
            x_sensor = []
            y_sensor = []

            for side in SIDES_FOR_SENSORS[sensor]:
                # Get the set of x,y points for this side for this sensor
                x = [ self.calibrated_positions[depth][side][sensor] for depth in ['Entrance', 'Midway', 'Exit'] ]
                y = [ 1.0, 0.5, 0.0 ]
                x_sensor.extend(x)
                y_sensor.extend(y)

            # Find the maximum distance measured at the Entrance and use it as the upper value for the input domain
            # domain_max_distance = max( self.calibrated_positions['Entrance']['Center'][0], self.calibrated_positions['Entrance']['Center'][1] )
            domain_max_distance = self.calibrated_positions['Entrance']['Center'][0]

            # Find the coefficients of a linear equation that best fit the x,y for this sensor
            poly[sensor] = Polynomial.fit( x_sensor, y_sensor, deg=1, domain=[0.0, domain_max_distance], window=[0.0, 1.0] )

        return poly
        

    def normalize_distance( self, d:tuple=None ) -> tuple:
        """
        Generate normalized distance by applying the linear equation
        fitted to the calibrated positions measurements
        """
        # Normalized distance for distance sensors Left (0) and Right (1)
        # NOTE: If the sensor is not working, one or both values in the tuple d
        #       may be None
        nd_left, nd_right = (None, None)
        try:
            nd_left = self.normalizing_polys[0].convert().coef[0] + self.normalizing_polys[0].convert().coef[1] * d[0]

        except (TypeError, AttributeError):
            nd_left = None

        # NOTE: Right sensor no longer available, so only left sensor will be used in calcs
        nd_right = None
        # try:
        #     nd_right = self.normalizing_polys[1].convert().coef[0] + self.normalizing_polys[1].convert().coef[1] * d[1]

        # except (TypeError, AttributeError):
        #     nd_right = None

        return (nd_left, nd_right)



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
        #keypad_cols = [ digitalio.DigitalInOut(x) for x in (board.D26, board.D6, board.D24, board.D23) ]
        keypad_cols = [ digitalio.DigitalInOut(x) for x in (board.D13, board.D6, board.D24, board.D23) ]
        keypad_keys = ( (1,2,3,4), )
        self.keypad = adafruit_matrixkeypad.Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

    def get_all_pressed_keys(self):
        return self.keypad.pressed_keys

    def get_max_pressed_key(self):
        try:
            return max( self.keypad.pressed_keys )

        except ValueError:
            return None
