# Setup logging
from decimal import DivisionByZero
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Standard dependencies
import time, os

# Classes and functions for managing the lighting controller
from controller_helper import LightingController

# Classes and functions for controlling the conceptual model
from model_helper import *

# Set command constraints if Living Light was being launched in
# Unattended vs. Interactive mode
unattended_mode = True if os.environ.get('LL_UNATTENDED',0) == 1 else False

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

# Distance and Proximity
dist = None
n_dist = None
is_nearby = { 'Entrance':False, 'Exit':False }

# Keypad
retained_pressed_keys = None

# LED update interval and processing metrics
last_led_update_timestamp = time.time()
led_timestep = 0
led_update_interval = { 'min': None, 'max': None, 'sum':0, 'count':0 }
led_update_proc_time = { 'min': None, 'max': None, 'sum':0, 'count':0 }

# Iterations between reports (sec): 0.5 sec = 500 milliseconds
REPORT_UPDATE_TIME_SEC = 0.5
last_report_update_time = time.time()

# Loop metrics
elapsed_time = None
prev_timestamp = None
this_timestamp = None
loop_elapsed_time_metrics = { 'min': None, 'max': None, 'sum':0, 'count':0 }

# Main Loop
while True:


    # ****************************************************************
    # Loop Metrics
    # ****************************************************************
    prev_timestamp = this_timestamp
    this_timestamp = time.time()
    if prev_timestamp is not None:
        elapsed_time = this_timestamp - prev_timestamp
        loop_elapsed_time_metrics['min'] = elapsed_time if loop_elapsed_time_metrics['min'] is None else min( loop_elapsed_time_metrics['min'], elapsed_time)
        loop_elapsed_time_metrics['max'] = elapsed_time if loop_elapsed_time_metrics['max'] is None else max( loop_elapsed_time_metrics['max'], elapsed_time)
        loop_elapsed_time_metrics['sum'] += elapsed_time
        loop_elapsed_time_metrics['count'] += 1

    # ****************************************************************
    # Update LEDs based upon the current Lighting Scenario
    # ****************************************************************
    led_upd_interval_time = this_timestamp - last_led_update_timestamp
    if led_upd_interval_time > lc.LED_TIMESTEP_SEC:
        
        # Track the time between LED updates
        led_update_interval['min'] = led_upd_interval_time if led_update_interval['min'] is None else min( led_update_interval['min'], led_upd_interval_time)
        led_update_interval['max'] = led_upd_interval_time if led_update_interval['max'] is None else max( led_update_interval['max'], led_upd_interval_time)
        led_update_interval['sum'] += led_upd_interval_time
        led_update_interval['count'] += 1        

        # Update the time tracking
        last_led_update_timestamp = this_timestamp

        # Update LED patterns
        lc.update_led_pattern(proximity=is_nearby, distance=n_dist, timestep=led_timestep )

        # Track the time that was required to update the LEDs
        led_update_complete_time = time.time()
        led_elapsed_time = led_update_complete_time - last_led_update_timestamp
        led_update_proc_time['min'] = led_elapsed_time if led_update_proc_time['min'] is None else min( led_update_proc_time['min'], led_elapsed_time)
        led_update_proc_time['max'] = led_elapsed_time if led_update_proc_time['max'] is None else max( led_update_proc_time['max'], led_elapsed_time)
        led_update_proc_time['sum'] += led_elapsed_time
        led_update_proc_time['count'] += 1        

        # Reset the LED timestep counter when it reaches over 24hrs (86,400 secs) of run time
        # NOTE: LED timestep counter is used to move LED pattern sequencies
        if led_timestep > 100000:
            led_timestep = 0

        # Increment the LED update timestep
        led_timestep += 1


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
    if this_timestamp - last_report_update_time > REPORT_UPDATE_TIME_SEC:
        
        # Update the time tracking
        last_report_update_time = this_timestamp

        # Report Header
        logging.info(f"\n**** Scenario '{lc.scenario}': Color Profile '{lc.MODEL_SCENARIO_CONFIG[lc.scenario]['color_profile']}', Pattern '{lc.MODEL_SCENARIO_CONFIG[lc.scenario]['led_pattern']}'")

        # If a keys were pressed during the main loop, then display them.
        if retained_pressed_keys:
            logging.info(f"**** Pressed Keys: {retained_pressed_keys}")

            # **************************************************************
            # Keypad selection to exit this program
            # **************************************************************

            # If we're in interactive mode and 1234 are all pressed, then exit this program.
            if ~unattended_mode and retained_pressed_keys == [1,2,3,4]:
                logging.info("**** All Keys Pressed (1+2+3+4): Ending Lighting Controller Program -- Goodbye!")

                # Turn off the LED Strip
                lc.all_leds_off()

                # Exit this program
                exit()

            # **************************************************************
            # Keypad selections for diagnostic modes
            # **************************************************************

            # If we're in interactive mode and *only* 3 and 4 are pressed, then perform a diagnostic function: Highlight every 10th LED
            elif ~unattended_mode and retained_pressed_keys == [3,4]:
                logging.info("**** Keys 3 and 4 Pressed: Highlighting every 10th LED on the full LED Strip")

                # Turn off the LED Strip
                lc.highlight_every_tenth_led()
                _ = input("=> Press ENTER to continue. ")


            # If we're in interactive mode and *only* 2 and 4 are pressed, then perform the diagnostic function: Brightness Range
            elif ~unattended_mode and retained_pressed_keys == [2,4]:
                logging.info("**** Keys 2 and 4 Pressed: Select a Normal or Diagnostic Lighting Scenario by Name")

                scen_choice = 'x'
                while scen_choice != '':
                    normal_choices_text = ", ".join( sorted( [ c for c in lc.MODEL_SCENARIO_CONFIG.keys() if 'diag_' not in c ] ) )
                    diag_cp_choices_text = ", ".join( sorted( [ c for c in lc.MODEL_SCENARIO_CONFIG.keys() if 'diag_cp_' in c ] ) )
                    diag_choices_text = ", ".join( sorted( [ c for c in lc.MODEL_SCENARIO_CONFIG.keys() if ( ('diag_' in c) and ('diag_cp_' not in c) ) ] ) )
                    print("\nNormal Scenario Choices: " + normal_choices_text)
                    print("Diagnostic Color Profile Scenario Choices: " + diag_cp_choices_text)
                    print("Other Diagnostic Scenario Choices: " + diag_choices_text)

                    scen_choice = input("=> Input a Scenario and press ENTER (or ENTER only to exit): ")
                    if scen_choice in lc.MODEL_SCENARIO_CONFIG:
                        # Change the scenario and return to the main loop
                        logging.info(f"Starting Scenario: {scen_choice}")
                        lc.init_model_scenario(scen_choice)
                        break
                    else:
                        print(f"Selected Scenario not found: {scen_choice}")


            # If we're in interactive mode and *only* 1 and 4 are pressed, then perform the diagnostic function: Calibrate Distance
            elif ~unattended_mode and retained_pressed_keys == [1,4]:
                logging.info("**** Keys 1 and 4 Pressed: Launching Distance Calibration Procedure")

                # Change lighting scenario to high brightness during calibration
                lc.init_model_scenario('diag_calibrate_distance')

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
            # Calculate the rolling average of distance
            ra_dist = lc._distance_rolling_average( dist )

            # Normalize the distance (Entrance=1, Midway=0.5, Exit=0)
            n_dist = lc.normalize_distance( ra_dist )
            logging.info(f"Distance: {dist}, Rolling Avg: {ra_dist}, Normalized Rolling Avg: {n_dist}")

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
        loop_avg = loop_elapsed_time_metrics['sum'] / ( loop_elapsed_time_metrics['count'] ) if loop_elapsed_time_metrics['count'] > 0 else 0.0
        logging.info(f"Loop Elapsed Time: Avg: {1000.0*loop_avg:.3f} ms, Min: {1000.0*loop_elapsed_time_metrics['min']:.3f} ms, Max: {1000.0*loop_elapsed_time_metrics['max']:.3f} ms, Loops: {loop_elapsed_time_metrics['count']} iterations")

        led_int_avg = led_update_interval['sum'] / ( led_update_interval['count'] ) if led_update_interval['count'] > 0 else 0.0
        logging.info(f"LED Update Interval Time: Avg: {1000.0*led_int_avg:.3f} ms, Min: {1000.0*led_update_interval['min']:.3f} ms, Max: {1000.0*led_update_interval['max']:.3f} ms, Updates: {led_update_interval['count']} iterations")

        led_proc_avg = led_update_proc_time['sum'] / ( led_update_proc_time['count'] ) if led_update_proc_time['count'] > 0 else 0.0
        logging.info(f"LED Update Processing Time: Avg: {1000.0*led_proc_avg:.3f} ms, Min: {1000.0*led_update_proc_time['min']:.3f} ms, Max: {1000.0*led_update_proc_time['max']:.3f} ms, Updates: {led_update_proc_time['count']} iterations")


    # ****************************************************************
    # Continue the loop
    # ****************************************************************
