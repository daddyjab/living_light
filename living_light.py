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

# Turn all LEDs off, just in case some had been left in a bad state before.
lc.all_leds_off()

# Set the lighting scenario to a normal scenario
lc.init_model_scenario('Idle')


# MAIN PROCESSING LOOP
# Perform an infinite loop of processing, and during each iteration:
#
# 1. Update the LED based upon whatever scenario is currently running,
#    the current distance measurements, and proximity information, and timing.
#    Note: LEDs updates will be spaced in time to ensure the LED brightness
#          changes do not occur too quickly.
#
# 2. After a set period of time has elapsed, process any command that has been
#    requested by the user pressing keys, display any reports, etc.
#
# 3. Update the current distance measurements, which hopefully will
#    help locate a person's location in the model. 
#
# 4. Update the proximity sensors to determine if a person is near the entrance or exit.
#
# 5. Optionally wait a short period of time and then restart the loop.

# Time to wait on each loop: 1 millisecond
# Revised: No loop sleep time need since both LED updates and Reports
#          now have time-based (not iteration based) thresholds
LOOP_SLEEP_TIME = 0

# Time between LED updates (sec): 0.01 sec = 10 milliseconds
# @TODO: Metrics show current loop time
#        * Average: 2.26 sec, Min: 0.29 sec, Max: 2.94 sec
#        * This is too slow! Need to consider ways to speed up LED pattern update processing :(
LED_UPDATE_TIME_SEC = 0.01
last_led_update_time = time.time()
led_timestep = 0

# Iterations between reports (sec): 0.5 sec = 500 milliseconds
REPORT_UPDATE_TIME_SEC = 0.5
last_report_update_time = time.time()

# Distance and Proximity
dist = ( None,None )
is_nearby = { 'Entrance':False, 'Exit':False }

# Keypad
retained_pressed_keys = None

# Loop metrics
elapsed_time = None
prev_time = None
this_time = None
loop_elapsed_time = { 'min': None, 'max': None, 'sum':0, 'count':0 }
led_update_elapsed_time = { 'min': None, 'max': None, 'sum':0, 'count':0 }

# Main Loop
while True:


    # ****************************************************************
    # Loop Metrics
    # ****************************************************************
    prev_time = this_time
    this_time = time.time()
    if prev_time is not None:
        elapsed_time = this_time - prev_time
        loop_elapsed_time['min'] = elapsed_time if loop_elapsed_time['min'] is None else min( loop_elapsed_time['min'], elapsed_time)
        loop_elapsed_time['max'] = elapsed_time if loop_elapsed_time['max'] is None else max( loop_elapsed_time['max'], elapsed_time)
        loop_elapsed_time['sum'] += elapsed_time
        loop_elapsed_time['count'] += 1

    # ****************************************************************
    # Update LEDs based upon the current Lighting Scenario
    # ****************************************************************
    if this_time - last_led_update_time > LED_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_led_update_time = this_time

        # Reset the LED timestep counter when it reaches over 24hrs (86,400 secs) of run time
        # NOTE: LED timestep counter is used to move LED pattern sequencies
        if led_timestep > 100000:
            led_timestep = 0

        # Increment the LED update timestep
        led_timestep += 1

        # Update LED patterns
        lc.update_led_pattern(proximity=is_nearby, distance=dist, timestep=led_timestep )

        # Track the time that was required to update the LEDs
        led_update_complete_time = time.time()
        led_elapsed_time = led_update_complete_time - last_led_update_time
        led_update_elapsed_time['min'] = led_elapsed_time if led_update_elapsed_time['min'] is None else min( led_update_elapsed_time['min'], led_elapsed_time)
        led_update_elapsed_time['max'] = led_elapsed_time if led_update_elapsed_time['max'] is None else max( led_update_elapsed_time['max'], led_elapsed_time)
        led_update_elapsed_time['sum'] += led_elapsed_time
        led_update_elapsed_time['count'] += 1        


    # ****************************************************************
    # Save any pressed keys and retain them for later use during
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
            logging.info(f"**** Pressed Keys: {retained_pressed_keys}")

            # **************************************************************
            # Keypad selection to exit this program
            # **************************************************************

            # If 1234 are all pressed, then exit this program.
            if retained_pressed_keys == [1,2,3,4]:
                logging.info("**** All Keys Pressed (1+2+3+4): Ending Lighting Controller Program -- Goodbye!")

                # Turn off the LED Strip
                lc.all_leds_off()

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
                logging.info("**** Keys 2 and 4 Pressed: Select a Normal or Diagnostic Lighting Scenario by Name")

                pat_choice = 'x'
                while pat_choice != '':
                    normal_choices_text = ", ".join( sorted( [ c for c in lc.MODEL_SCENARIO_CONFIG.keys() if 'diag_' not in c ] ) )
                    diag_choices_text = ", ".join( sorted( [ c for c in lc.MODEL_SCENARIO_CONFIG.keys() if 'diag_' in c ] ) )
                    print("\nNormal Scenario Choices: " + normal_choices_text)
                    print("Diagnostic Scenario Choices: " + diag_choices_text)
                    pat_choice = input("=> Input a Scenario and press ENTER (or ENTER only to exit): ")
                    if pat_choice in lc.MODEL_SCENARIO_CONFIG:
        
                        # Change the scenario and return to the main loop
                        # so that the LED patterns will run
                        logging.info(f"Starting Light Scenario: {pat_choice}")
                        lc.init_model_scenario(pat_choice)
                        break


            # If *only* 1 and 4 are pressed, then perform the diagnostic function: Calibrate Distance
            elif retained_pressed_keys == [1,4]:
                logging.info("**** Keys 1 and 4 Pressed: Launching Distance Calibration Procedure")

                # Change lighting scenario to high brightness during calibration
                lc.init_model_scenario('diagcalibratedistance')

                # Launch Distance Calibration
                lc.baseline_distance, lc.calibrated_positions = lc._calibrate_distance_sensors()
            
                # Calculate distance normalizing polynomials, such that distance is normalized
                # the calibrated positions for Entrance to Exit are normalized to 1.0 to 0.0
                lc.normalizing_polys = lc._calc_normalizing_polys()

                # Change lighting scenario back to a normal scenario
                lc.init_model_scenario('Idle')


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
        loop_avg = loop_elapsed_time['sum'] / ( loop_elapsed_time['count'] ) if loop_elapsed_time['count'] > 0 else 0.0
        logging.info(f"Loop Elapsed Time: Avg: {1000.0*loop_avg:.3f} ms, Min: {1000.0*loop_elapsed_time['min']:.3f} ms, Max: {1000.0*loop_elapsed_time['max']:.3f} ms, Loops: {loop_elapsed_time['count']} iterations")

        led_avg = led_update_elapsed_time['sum'] / ( led_update_elapsed_time['count'] ) if led_update_elapsed_time['count'] > 0 else 0.0
        logging.info(f"LED Update Elapsed Time: Avg: {1000.0*led_avg:.3f} ms, Min: {1000.0*led_update_elapsed_time['min']:.3f} ms, Max: {1000.0*led_update_elapsed_time['max']:.3f} ms, Updates: {loop_elapsed_time['count']} iterations")


    # ****************************************************************
    # Pause processing for a short time
    # ****************************************************************

    # Wait a bit, then the infinite loop will restart
    time.sleep(LOOP_SLEEP_TIME)
