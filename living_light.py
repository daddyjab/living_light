# Setup logging
from decimal import DivisionByZero
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
# Revised: No loop sleep time neeed since both LED updates and Reports
#          now have time-based (not iteration based) thresholds
LOOP_SLEEP_TIME = 0

# Time between LED updates (sec): 0.01 sec = 10 milliseconds
LED_UPDATE_TIME_SEC = 0.01
last_led_update_time = time.time()
led_timestep = 0

# Iterations between reports (sec): 0.5 sec = 500 milliseconds
REPORT_UPDATE_TIME_SEC = 0.5
last_report_update_time = time.time()

# Distance and Proximity
dist = None
is_nearby = {}

# Keypad
retained_pressed_keys = None

# Loop metrics
elapsed_time = None
prev_time = None
this_time = None
loop_elapsed_time = { 'last': 0, 'min': 9999999, 'max': -1, 'sum':0, 'count':0 }

# Main Loop
while True:


    # ****************************************************************
    # Loop Metrics
    # ****************************************************************
    prev_time = this_time
    this_time = time.time()
    if prev_time is not None:
        elapsed_time = this_time - prev_time
        loop_elapsed_time['min'] = min( loop_elapsed_time['min'], elapsed_time)
        loop_elapsed_time['max'] = max( loop_elapsed_time['max'], elapsed_time)
        loop_elapsed_time['sum'] = sum( loop_elapsed_time['sum'], elapsed_time)
        loop_elapsed_time['count'] += 1

    # ****************************************************************
    # Update LEDs based upon the current Lighting Scenario
    # ****************************************************************
    if this_time - last_led_update_time > LED_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_led_update_time = this_time

        # Reset the LED timestep counter when it reaches over 24hrs (86,400 secs) of run time
        # NOTE: LED timestep counter is used to move LED pattern sequencies
        if led_timestep > 1e6:
            led_timestep = 0

        # Increment the LED update timestep
        led_timestep += 1

        # Update LED patterns
        lc.update_led_pattern(timestep=led_timestep, distance=dist, proximity=is_nearby )

    # ****************************************************************
    # Save any pressed keys and retain them for later use durin
    # Report processing
    # ****************************************************************
    pressed_keys = lc.get_all_pressed_keys()
    if pressed_keys:
        retained_pressed_keys = pressed_keys

    # ****************************************************************
    # Generate reports and check for key presses periodically
    # Update LEDs periodically (but not too often, or light patterns may not be visible)
    # ****************************************************************
    if this_time - last_report_update_time > REPORT_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_report_update_time = this_time

        # If a keys were pressed during the main loop, then display them.
        if retained_pressed_keys:
            logging.info("**** Pressed Keys: ", retained_pressed_keys)

            # **************************************************************
            # Keypad selection to exit this program
            # **************************************************************

            # If 1234 are all pressed, then exit this program.
            if retained_pressed_keys == [1,2,3,4]:
                logging.info("**** All Keys Pressed (1+2+3+4): Ending Lighting Controller Program -- Goodbye!")

                # Turn off the LED Strip
                lc.init_model_scenario('Off')

                # Exit this program
                exit()

            # **************************************************************
            # Keypad selections for diagnostic modes
            # **************************************************************

            # If *only* 3 and 4 are pressed, then perform a diagnostic function: Highlight every 10th LED
            elif retained_pressed_keys == [3,4]:
                logging.info("**** Keys 3 and 4 Pressed: Highlighting every 10th LED on the full LED Strip")

                # Turn off the LED Strip
                lc.highlight_every_tenth_led()
                _ = input("=> Press ENTER to continue. ")


            # If *only* 2 and 4 are pressed, then perform the diagnostic function: Brightness Range
            elif retained_pressed_keys == [2,4]:
                logging.info("**** Keys 2 and 4 Pressed: Showing the full range of brightness using configured LEDs")

                # Change scenario
                lc.init_model_scenario('Brightness Range')


            # If *only* 1 and 4 are pressed, then perform the diagnostic function: Calibrate Distance
            elif retained_pressed_keys == [1,4]:
                logging.info("**** Keys 1 and 4 Pressed: Launching Distance Calibration Procedure")

                # Change scenario
                lc.init_model_scenario('Calibrate Distance')

                # Launch Distance Calibration
                lc.baseline_distance, lc.calibrated_positions = lc._calibrate_distance_sensors()
            
                # Calculate distance normalizing polynomials, such that distance is normalized
                # the calibrated positions for Entrance to Exit are normalized to 1.0 to 0.0
                lc.normalizing_polys = lc._calc_normalizing_polys()

                # Change scenario
                lc.init_model_scenario('Off')


            # **************************************************************
            # Keypad selections for normal operating scenarios
            # **************************************************************

            # If 3 was pressed, set model scenario to "Energy"
            elif 3 in retained_pressed_keys:
                logging.info("**** Key 3 Pressed: Setting model to scenario 'Energy'")

                # Change to 'Energy' scenario
                lc.init_model_scenario('Energy')

            # If 2 was pressed, set model scenario to "Standard"
            elif 2 in retained_pressed_keys:
                logging.info("**** Key 2 Pressed: Setting model to scenario 'Standard'")

                # Change to 'Standard' scenario
                lc.init_model_scenario('Standard')

            # If 1 was pressed, set model scenario to "Idle"
            elif 1 in retained_pressed_keys:
                logging.info("**** Key 1 Pressed: Setting model to scenario 'Idle'")

                # Change to 'Idle' scenario
                lc.init_model_scenario('Idle')

            # Clear out the retained pressed keys for next time
            retained_pressed_keys = None


        # ****************************************************************
        # Update distance measurements
        # ****************************************************************
        
        # Get the current distance (in centimeters)
        dist = lc.get_distance()

        try:
            # Normalize the distance
            n_dist = lc.normalize_distance( dist )
            logging.info(f"Left Distance: {dist[0]} [Normalized: {n_dist[0]}], Right Distance: {dist[1]} [Normalized: {n_dist[1]}]")

        except TypeError:
            pass

        # ****************************************************************
        # Update proximity indicators
        # ****************************************************************
        is_nearby = lc.is_object_nearby()

        try:
            logging.info(f"Object Near Entrance: {is_nearby['Entrance']}, Object Near Exit: {is_nearby['Exit']}")

        except (KeyError, TypeError):
            pass


        # ****************************************************************
        # DEBUG: Display loop metrics
        # ****************************************************************
        try:
            loop_avg = loop_elapsed_time['sum'] / ( loop_elapsed_time['count'] )

        except DivisionByZero:
            loop_avg = 0.0

        logging.info(f"Loop Elapsed Time: Avg: {1000.0*loop_avg:.3f} ms, Min: {1000.0*loop_elapsed_time['min']:.3f} ms, Max: {1000.0*loop_elapsed_time['max']:.3f} ms, Loops: {loop_elapsed_time['count']} iterations")


    # ****************************************************************
    # Pause processing for a short time
    # ****************************************************************

    # Wait a bit, then the infinite loop will restart
    time.sleep(LOOP_SLEEP_TIME)
