# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Standard dependencies
import time

# Classes and functions for managing the lighting controller
from controller_helper import LightingController

# Classes and functions for controlling the conceptual model
from model_helper import *

# Create a LightingController object,
# which initializes the controller and all of its sensors
lc = LightingController( led_brightness=0.5, run_distance_calibration=False )


# KLUDGE: Show a static test pattern until true LED processing is in place
# Get the LED RGB values for the test pattern
led_colors = lc.led_test_pattern('Range', 'Direct Sunlight' )

# Display the test pattern on the LED Strip
lc.draw_model_leds( led_colors)


# MAIN PROCESSING LOOP
# Perform an infinite loop of processing, and during each iteration:
# 1. Increment an iteration counter
#
# 2. When the iteration counter reaches a target value, reset the iteration counter to 0,
#    process any command that has been requested by the user pressing keys, display any reports, etc.
#
# 3. Update the current distance measurements, which hopefully will
#    help locate a person's location in the model. 
#
# 4. Update the proximity sensors to determine if a person is near the entrance or exit.
#
# 5. Update the LED based upon whatever scenario is currently running,
#    the current distance measurements, and proximity information, and timing.
#    Note: The LEDs will have their own loop of changes that adjust periodically
#          depending upon how much time as elapsed since the LED update function
#          been called.  So the LED changes may be programmed to run quickly or
#          slowly as desired for each scenario and condition.
#
# 6. Wait a short period of time and then restart the loop.

# Time to wait on each loop: 1 millisecond
LOOP_SLEEP_TIME = 1e-3

# Time between LED updates (sec)
LED_UPDATE_TIME_SEC = 0.01
last_led_update_time = time.time()
led_timestep = 0

# Iterations between reports (about every 1 seconds)
REPORT_UPDATE_TIME_SEC = 0.5
last_report_update_time = time.time()

# Distance and Proximity
dist = None
is_nearby = {}

# Keypad
retained_pressed_keys = None

# Main Loop
while True:

    # ****************************************************************
    # Update LEDs based upon the current Lighting Scenario
    # ****************************************************************

    # Update LEDs periodically (but not too often, or light patterns may not be visible)
    this_led_time = time.time()
    if this_led_time - last_led_update_time > LED_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_led_update_time = this_led_time

        # Reset the LED timestep counter when it reaches over 24hrs (86,400 secs) of run time
        # NOTE: LED timestep counter is used to move LED pattern sequencies
        if led_timestep > 1e6:
            led_timestep = 0

        # Increment the LED update timestep
        led_timestep += 1

        # Update LED patterns
        lc.update_led_pattern(timestep=led_timestep, distance=dist, proximity=is_nearby )

    # ****************************************************************
    # Save any pressed keys and retain them for later processing
    # ****************************************************************

    # Accept and retain key presses, for use during the next report
    pressed_keys = lc.get_all_pressed_keys()
    if pressed_keys:
        retained_pressed_keys = pressed_keys

    # Generate reports and check for key presses periodically
    # Update LEDs periodically (but not too often, or light patterns may not be visible)
    this_report_update_time = time.time()
    if this_report_update_time - last_report_update_time > REPORT_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_report_update_time = this_report_update_time

        # If a keys were pressed during the main loop, then display them.
        if retained_pressed_keys:
            print("Pressed Keys: ", retained_pressed_keys)

            # If 1234 are all pressed, then exit this program.
            if retained_pressed_keys == [1,2,3,4]:
                logging.info("All Keys Pressed: Ending Lighting Controller Program -- Goodbye!")

                # Turn off the LED Strip
                lc.init_model_scenario('Off')

                # Exit this program
                exit()

            # If *only* 3 and 4 are pressed, then perform the diagnostic function
            elif retained_pressed_keys == [3,4]:
                logging.info("Keys 3 and 4 Pressed: Launching LED Diagnostics")

                # Turn off the LED Strip
                lc.init_model_scenario('Diagnostics')


            # If *only* 2 and 4 are pressed, then perform the diagnostic function
            elif retained_pressed_keys == [2,4]:
                logging.info("Keys 2 and 4 Pressed: Launching Distance Calibration")

                # Turn off the LED Strip
                lc.init_model_scenario('Off')

                # Launch Distance Calibration
                lc.baseline_distance, lc.calibrated_positions = lc._calibrate_distance_sensors()

            # If 3 was pressed, set model scenario to "Energy"
            elif 3 in retained_pressed_keys:
                logging.info("Key 3 Pressed: Setting model to scenario 'Energy'")

                # Change to 'Energy' scenario
                lc.init_model_scenario('Energy')

            # If 2 was pressed, set model scenario to "Standard"
            elif 2 in retained_pressed_keys:
                logging.info("Key 2 Pressed: Setting model to scenario 'Standard'")

                # Change to 'Standard' scenario
                lc.init_model_scenario('Standard')

            # If 1 was pressed, set model scenario to "Idle"
            elif 1 in retained_pressed_keys:
                logging.info("Key 1 Pressed: Setting model to scenario 'Idle'")

                # Change to 'Idle' scenario
                lc.init_model_scenario('Idle')

            # Clear out the retained pressed keys for next time
            retained_pressed_keys = None

        # ****************************************************************
        # Update distance measurements
        # ****************************************************************

        # Check the distance
        dist = lc.get_distance()
        try:
            logging.info(f"Left Distance: {dist[0]}, Right Distance: {dist[1]}")
        except:
            pass

        # ****************************************************************
        # Update proximity indicators
        # ****************************************************************

        # Check if an object is in proximity
        is_nearby = lc.is_object_nearby()
        try:
            logging.info(f"Object Near Entrance: {is_nearby['Entrance']}, Object Near Exit: {is_nearby['Exit']}")
        except:
            pass


    # ****************************************************************
    # Pause processing for a short time
    # ****************************************************************

    # Wait a bit, then the infinite loop will restart
    time.sleep(LOOP_SLEEP_TIME)
