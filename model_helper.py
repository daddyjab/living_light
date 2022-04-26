# from multiprocessing import cpu_count
import numpy as np
import logging, os
from PIL import Image, ImageDraw, ImageColor

from display_helper import *

class Model():
    """
    Class representing the sides of the model and their LEDs
    """
    def __init__(self):

        # Model Configuration (including some attributes for the simulated model)
        self.MODEL_INTERIOR_COLOR = 'rgb(128,128,128)'
        self.MODEL_OUTLINE_COLOR = 'rgb(0,0,0)'
        self.MODEL_CONFIG = {
            'Left': {
                # Real and Simulated: Arrangement of LEDs in this model (real or simulated)
                'leds': { 'rows': 10, 'cols': 9 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ 159, 180, 184, 204, 208, 228, 232, 253, 257 ],
                                    [ 160, 179, 185, 203, 209, 227, 233, 252, 258 ],
                                    [ 161, 178, 186, 202, 210, 226, 234, 251, 259 ],
                                    [ 162, 177, 187, 201, 211, 225, 235, 250, 260 ],
                                    [ 163, 176, 188, 200, 212, 224, 236, 249, 261 ],
                                    [ 164, 175, 189, 199, 213, 223, 237, 248, 262 ],
                                    [ 165, 174, 190, 198, 214, 222, 238, 247, 263 ],
                                    [ 166, 173, 191, 197, 215, 221, 239, 246, 264 ],
                                    [ 167, 172, 192, 196, 216, 220, 240, 245, 265 ],
                                    [ 168, None, None, None, None, None, None, None, 266 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                'bbox': (0,0, 450,500),                
                },

            'Right': {
                # Arrangement of LEDs in this model (real or simulated)
                'leds': { 'rows': 10, 'cols': 9 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ 28, 32, 52, 55, 75, 78, 99, 101, 122 ],
                                    [ 27, 33, 51, 56, 74, 79, 98, 102, 121 ],
                                    [ 26, 34, 50, 57, 73, 80, 97, 103, 120 ],
                                    [ 25, 35, 49, 58, 72, 81, 96, 104, 119 ],
                                    [ 24, 36, 48, 59, 71, 82, 95, 105, 118 ],
                                    [ 23, 37, 47, 60, 70, 83, 94, 106, 117 ],
                                    [ 22, 38, 46, 61, 69, 84, 93, 107, 116 ],
                                    [ 21, 39, 45, 62, 68, 85, 92, 108, 115 ],
                                    [ 20, 40, 44, 63, 67, 86, 91, 109, 114 ],
                                    [ 19, None, 43, None, 66, 87, 90, 110, 113 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                'bbox': (550,0, 1000,500),
                },
        }

        # Initialize dictionaries aligned to the model configuration
        self.led_array = {}
        for c in self.MODEL_CONFIG:
            # Array of integer-encoded RGB values (e.g., 0x7FFF00) for each model component
            self.led_array[c] = np.zeros( (self.MODEL_CONFIG[c]['leds']['rows'], self.MODEL_CONFIG[c]['leds']['cols']), dtype='int')

        # Model Scenarios
        # 'color_profile': Defines the RGB color to use as the basis around which brightness levels are varied
        #
        # 'led_pattern': Specifies which function will be used to set the brightness for each LED based upon
        #                the LED position in a component of the model, the current timestep, and distance and
        #                proximity sensor values.
        #    
        # 'brightness_scale': A scaling factor > 0.0 that is applied to the brightness of each LED in the pattern,
        #                     which allows brightening or dimming the overall pattern for the scenario.
        #
        # 'cycle_time': For patterns that have movement, the number of seconds required to perform a full cycle of the pattern
        #               per second (secs/cycle).  Can be used to make the pattern run at a slow or fast rate.

        self.MODEL_SCENARIO_CONFIG = {

            # Normal Scenarios
            'Idle': { 'color_profile': '40W Tungsten', 'led_pattern': 'ellipse', 'brightness_scale': 0.5, 'cycle_time': 4.0 },
            'Standard': { 'color_profile': 'High Noon Sun', 'led_pattern': 'come_in', 'brightness_scale': 0.75, 'cycle_time': 4.0 },
            'Energy': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },

            # Diagnostic Scenarios (all performed with brightest color profile)
            'diag_calibrate_distance': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'all_on', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_come_in': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_ellipse': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'ellipse', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_range': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'range', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_all_on': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'all_on', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_all_off': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'all_off', 'brightness_scale': 1.0, 'cycle_time': 4.0 },

            # Color Profile Scenarios (all performed with the 'come_in' pattern)
            'diag_cp_candle': { 'color_profile': 'Candle', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_40w_tungsten': { 'color_profile': '40W Tungsten', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_100w_tungsten': { 'color_profile': '100W Tungsten', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_halogen': { 'color_profile': 'Halogen', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_carbon_arc': { 'color_profile': 'Carbon Arc', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_high_noon_sun': { 'color_profile': 'High Noon Sun', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_direct_sunlight': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_overcast_sky': { 'color_profile': 'Overcast Sky', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
            'diag_cp_clear_blue_sky': { 'color_profile': 'Clear Blue Sky', 'led_pattern': 'come_in', 'brightness_scale': 1.0, 'cycle_time': 4.0 },
        }

        # Current Model scenario
        self.scenario = None

        # Model image (Simulation)
        self.model = None

        # Color Profiles
        # http://planetpixelemporium.com/tutorialpages/light.html
        self.COLOR_PROFILE = {
            'Candle': { 'temp': 1900, 'rgb': (255, 147, 41) },
            '40W Tungsten': { 'temp': 2600, 'rgb': (255, 197, 143) },
            '100W Tungsten': { 'temp': 2850, 'rgb': (255, 214, 170) },
            'Halogen': { 'temp': 3200, 'rgb': (255, 241, 224) },
            'Carbon Arc': { 'temp': 5200, 'rgb': (255, 250, 244) },
            'High Noon Sun': { 'temp': 5400, 'rgb': (255, 255, 251) },
            'Direct Sunlight': { 'temp': 6000, 'rgb': (255, 255, 255) },
            'Overcast Sky': { 'temp': 7000, 'rgb': (201, 226, 255) },
            'Clear Blue Sky': { 'temp': 20000, 'rgb': (64, 156, 255) },
        }

        # Brightness Pattern Functions
        self.BRIGHTNESS_PATTERN_FUNCTION = {
            'come_in': self._pattern_come_in,
            'ellipse': self._pattern_ellipse,
            'range': self._pattern_range,
            'all_off': self._pattern_off,
            'all_on': self._pattern_on,
        }

        # Set shadow control LEDs to provide full brightness for LEDs
        # on the top row and with a fixed column spacing, which will generate
        # a specific, fixed (or possibly varying) shadow on the top of the model
        self.SHADOW_CONTROL_ROWS = [0]
        self.SHADOW_CONTROL_COLUMNS = [0,2,4,6,8]
        self.SHADOW_CONTROL_BRIGHTNESS = 1.0


        # LED Timestep: Interval between calls to update the LED pattern. 
        # Note: This configuration setting must be small enough to permit flexibility in setting
        #       the speed of individual scenario patterns, but large enough that CPU can perform all needed processing
        #       between timesteps and the timesteps are relatively even.
        # 0.05 sec = 50 milliseconds
        self.LED_TIMESTEP_SEC = 0.05
        self.timesteps_per_cycle = None

        # LED Pattern Buffer, which stores a dictionary of 5D numpy arrays
        # for each model component ('Left', 'Right').
        # Value: The color of the LED for each component
        # Dimensions:
        # 1. Proximity: Integer-encoded Entrance/Exit combinations
        #
        # 2. Distance per Cycle: Distance to object in 10 increments from Entrance to Exit
        #
        # 3. Timesteps per Cycle: Maximum number of timesteps needed to complete one cycle of movement,
        #                         which has to be sized to accomodate the worst case duration of a cycle.
        #                         => max. 'cycle_time' [secs/cycle] / self.LED_TIMESTEP_SEC [sec/timestep], then round up to nearest 10
        # 
        # 4. LED Row: Row of the LED
        # 5. LED Column: Column of the LED
        self.N_LED_PATTERN_PROXIMITY = 4
        self.N_LED_PATTERN_DISTANCE = 10
        WORST_CASE_CYCLE_TIME = max( [ self.MODEL_SCENARIO_CONFIG[s]['cycle_time'] for s in self.MODEL_SCENARIO_CONFIG ] )
        self.N_LED_PATTERN_TIMESTEPS = int( 10.0 * np.ceil( 0.1 * ( WORST_CASE_CYCLE_TIME / self.LED_TIMESTEP_SEC) ) )
        self.led_pattern_buffer = {}
        for c in self.MODEL_CONFIG:
            self.led_pattern_buffer[c] = np.zeros( ( 
                                            self.N_LED_PATTERN_PROXIMITY,
                                            self.N_LED_PATTERN_DISTANCE,
                                            self.N_LED_PATTERN_TIMESTEPS,
                                            self.MODEL_CONFIG[c]['leds']['rows'],
                                            self.MODEL_CONFIG[c]['leds']['cols'] )            
                                            , dtype='int' )

        # Initialize but don't start the default scenario
        logging.info("Initializing Lighting Scenario: Idle")
        self.init_model_scenario('Idle')


    def init_model_scenario( self, scenario:str='Idle' ):
        """
        Set the overall lighting scenario in use by the Model
        """

        # Timesteps per Cycle = Cycle Time [secs/cycle] / LED timestep time [secs/timesteps]
        self.timesteps_per_cycle = int( float(self.MODEL_SCENARIO_CONFIG[scenario]['cycle_time']) / self.LED_TIMESTEP_SEC )

        # Load from file the LED Pattern associated with this scenario.
        # If the file does not exist for the LED Pattern, then generate it and save it to a file.
        self.load_or_generate_scenario( scenario )
    

    def load_or_generate_scenario( self, scenario:str=None ):
        """
        Load LED Pattern Buffer data for a specified scenario from a file.
        If the file does not exist for the scenario then generate it and save it to a file.        
        """

        # Store the current scenario type in this object
        self.scenario = scenario

        # Attempt to load the Scenario file
        scenario_clean = scenario.lower().replace(' ', '_')
        scen_filen = 'scen_' + scenario_clean + '.npz'
        scen_filep = os.path.join( '.', 'data', scen_filen )

        if os.path.exists( scen_filep ):

            # LED Pattern file exists, so load it
            logging.info(f"Loading Scenario file: {scen_filep}")
            with np.load( scen_filep ) as lp_file:
                for c in lp_file:
                    self.led_pattern_buffer[c] = lp_file[c]

        else:
            # LED Pattern file does not exist, so generate it
            logging.info(f"Creating Scenario file: {scen_filep}")
            self._generate_scenario_file( scenario )


    def _generate_scenario_file( self, scenario:str=None ):
        """
        Generate the LED Pattern Buffer for a specified scenario and then save it to a file.

        For each model component, iterate all of the permutations of
        Proximity, Distance, Timesteps, and LED Row/Column to populate the
        LED Pattern Buffer.  Then save the LED Pattern Buffer to a file.
        """

        # Store the current scenario type in this object
        self.scenario = scenario

        # Populate the LED Pattern Buffer for each model component
        # Proximity (Exit/Entrance): 0 => (False,False), 1 => (False,True), 2 => (True, True), 3 => (True, False)
        for p in range(self.N_LED_PATTERN_PROXIMITY):

            # Distance (based upon normalized, rolling-average distance sensor values binned into discrete values)
            for d in range(self.N_LED_PATTERN_DISTANCE):

                # Timesteps (where a timer in the main loop controls the time between each LED update)
                for t in range(self.N_LED_PATTERN_TIMESTEPS):

                    # Generate the LED color array for this proximity/distance/timestep
                    # for all model components.  Results populated in dictionary self.led_array
                    self._calc_led_pattern( t_idx=t, d_idx=d, p_idx=p )

                    # Store the LED color array for each model component in the LED Pattern Buffer
                    for c in self.MODEL_CONFIG:
                        self.led_pattern_buffer[c][p][d][t] = self.led_array[c]

        # Save the LED Pattern Buffer to a scenario-specific file
        scenario_clean = scenario.lower().replace(' ', '_')
        scen_filen = 'scen_' + scenario_clean + '.npz'
        scen_filep = os.path.join( '.', 'data', scen_filen )

        np.savez( scen_filep, **self.led_pattern_buffer )


    def update_led_pattern(self, timestep:int=0, distance:float=1.0, proximity:dict={} ):
        """
        When run from within the main loop, this method uses the LED Pattern Buffer to display
        the appropriate LED colors based upon the specified proximity, distance, and timestep values.
        * proximity: Dictionary indicating if object is (True) or is not (False) near a sensor 'Entrance' or 'Exit'
        * distance: Normalized distance [0.0 to 1.0]
        """

        # Proximity: Convert proximity sensor values to a single proximity index [0 to self.N_LED_PATTERN_PROXIMITY]
        p_idx = 0
        if proximity.get('Entrance',False):
            p_idx += 1

        if proximity.get('Exit',False):
            p_idx += 2

        # Distance: Map the normalized distance to a single distance index [0 to self.N_LED_PATTERN_DISTANCE],
        # where self.N_LED_PATTERN_DISTANCE is the Entrance and 0 is the Exit

        # Calculate a single distance value based upon whichever sensors have non-null values
        # Ensure that the individual normalized distances are in the range 0.0 to 1.0.
        d = np.clip(distance, 0.0, 1.0)

        # Convert the normalized distance to a distance index, where d_idx=0 corresponds to the Exit
        d_idx = int( np.round( d * (self.N_LED_PATTERN_DISTANCE-1) ) )
        
        # Timestep, where the interval between timesteps is self.LED_TIMESTEP_SEC
        t_idx = timestep % self.timesteps_per_cycle

        # Retrieve the LED pattern colors from the LED Pattern Buffer
        for c in self.MODEL_CONFIG:
            self.led_array[c] = self.led_pattern_buffer[c][p_idx][d_idx][t_idx]

        # Update the LEDs to reflect the new LED colors (for either physical LEDs or simulated LEDs)
        self.draw_model_leds()


    def _calc_led_pattern(self, t_idx:int=None, d_idx:int=None, p_idx:int=None ):
        """
        Calculate the LED Pattern for the specified proximity, distance, and timestep
        for the LED Pattern currently in use.  Result is stored in dictionary self.led_array.

        Maps an array of scalar values in the range [0.0 to 1.0] and maps it to RGB value as integer
        that are consistent with the specified or default color profile.
        The mapping is done by:
        1. Converting the color profile base RGB to the Hue, Lightness, Saturation (HLS) color scheme
        2. Then adjusting only the Lightness factor proportional to the brightness value in the input array
        3. Converting the resulting HLS tuple into a single integer representing a RGB value
        4. Doing the above for each element in the array
        """

        # Use the Color Profile specified in the Light Scenario
        color_profile = self.MODEL_SCENARIO_CONFIG[self.scenario]['color_profile']

        # Get the base HLS values that correspond to the color profile RGB
        h_prof, l_prof, s_prof = rgb_tuple_to_hls( np.array(self.COLOR_PROFILE[color_profile]['rgb']) )

        # Helper function to map a brightness value to an integer-encoded RGB
        # value based upon HLS values extracted above from the associated color profile
        def _helper_brightness_to_rgb_in_profile( b:float=None ) -> tuple:
            # Adjust the lightness factor based upon the brightness value [0.0 to 1.0]
            rgb = hls_to_rgb_tuple( (h_prof, np.clip(b*l_prof, 0.0, 1.0), s_prof) )
            return rgb_tuple_to_int( rgb )

        # Use the LED Pattern specified in the Light Scenario
        led_pattern = self.MODEL_SCENARIO_CONFIG[self.scenario]['led_pattern']

        # Constrain the brightness scaling factor
        b_scale = self.MODEL_SCENARIO_CONFIG[self.scenario]['brightness_scale']

        # Calculate a snapshot in the specified brightness pattern and
        # return an array of RGB color strings for each Model component
        # Use a specified Bightness Pattern Function associated with the current scenario
        # to generate a set of RGB string values for each of the components of the model
        for c in self.MODEL_CONFIG:

            # Use numpy iterator to set the LED color values
            # (about 35% performance improvement over previous nested loop approach)
            with np.nditer( self.led_array[c], flags=['multi_index'], op_flags=['readwrite']) as la_iter:
                for led_col in la_iter:

                    # Calculate a brightness value for this LED based upon
                    # it's location, size of the model component,
                    # the timestep, and the distance and proximity sensor values
                    b_val = self.BRIGHTNESS_PATTERN_FUNCTION[led_pattern](
                            c,
                            la_iter.multi_index[0], la_iter.multi_index[1],
                            self.MODEL_CONFIG[c]['leds']['rows'], self.MODEL_CONFIG[c]['leds']['cols'],
                            t_idx, d_idx, p_idx )

                    # Translate the brightness value into an integer-encoded RGB
                    # value based upon the selected color profile,
                    # with brightness scaled by the b_scale factor supplied as an arg
                    led_col[...] = _helper_brightness_to_rgb_in_profile( b_scale * b_val )


    # **********************************************************************************************
    # Brightness Pattern Functions, which LED brightness/behavior
    # based upon location of the LED, the number of LEDs on the component (sides, top),
    # current timestep, measured distance to an object, and objects in proximity to entrance/exit
    #
    # Notes
    #
    # * Pattern Movement
    #   * Movement is simulated by varying the brightness of LEDs over time.
    #   * The speed with which a pattern performs one full "cycle" of movement (e.g., Entrance to Exit)
    #     is determined by the scenario configuration parameter self.MODEL_SCENARIO_CONFIG[scenario]['cycle_time'],
    #     with the unit of seconds per cycle.
    #   * The rate at which individual LEDs need to be changed also depends upon the number of LEDs
    #     configured in the model component in the direction of simulated movement.
    #     This can be calculated as the number of LEDs that the pattern will shift for every timestep
    #     => 

    #   * For Brightness Pattern Functions that simulate movement
    #   * The "speed" of the pattern is defined as rate at which a pattern moves from its
    #     starting point (e.g., Entrance in many cases) to its ending point (e.g., Exit in many cases).
    #   * Speed will vary depending upon the dimensions of the model components so that
    #     the pattern will start and end on each component in synchronization with the other components,
    #     even if one component has 7 columns of LEDs, another has 9, and another has 17.
    #     
    #
    # * Respiration rate:
    #   * At rest (adult normal): 12 to 20 breaths per minute => 3 to 5 seconds per breath
    #   * After brisk walk (adult normal): 30 breaths per minute => 2 seconds per breath
    #   * During exercise (adult normal): 40-60 breaths per minute => 1 to 1.5 seconds per breath
    # **********************************************************************************************


    def _pattern_come_in( self, c, r_ix, c_ix, n_r, n_c, t:int=0, dist:int=0, prox:int=0 ):
        """
        Provide an elliptic pattern of brightness that invites a person to enter the space,
        with the pattern brighness overlaid with a slower overall variation in brightness
        akin to "breathing"
        """

        # Set shadow control LEDs to provide full brightness for LEDs
        # on the top row and with a fixed column spacing, which will generate
        # a specific, fixed (or possibly varying) shadow on the top of the model
        if r_ix in self.SHADOW_CONTROL_ROWS:
            return self.SHADOW_CONTROL_BRIGHTNESS if c_ix in self.SHADOW_CONTROL_COLUMNS else 0.0
      
        # Rate at which column should be incremented per timestep (LEDs/timestep)
        # [LED columns/timestep]=> # of Columns [LED columns/cycle] / Timesteps per Cycle [timesteps/cycle]
        col_inc = float(n_c) / self.timesteps_per_cycle

        # Rate at which "breathing" should be incremented per timestep
        # Breathing Rate = [One Breath (dim->bright->dim) / Cycle]
        BREATHING_RATE = 1.0

        # Breathing Increment [ Breaths / Timestep ] = [ One Breath (dim->bright->dim) / Cycle ] / Timesteps per Cycle [timesteps/cycle]
        breath_inc = BREATHING_RATE / self.timesteps_per_cycle

        # Brightness decomposed to a fixed base brightness level
        # plus an adjusted brightness that can vary based upon the various input parameters
        b_fixed = 0.3
        b_adj = 1.0

        # Sinusoidal cycling of brightness based upon column and timestep
        b_adj = np.abs( np.sin( np.pi * ( (c_ix - col_inc*(t % self.timesteps_per_cycle))/(n_c-1) ) ) if n_c > 1 else 1.0 )

        # With slower sinusoidal cycling of brightness based only upon time
        b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # # Vary the adjustable part of the brightness by a slow-moving time function that simulates breathing rate.
        # if c=='Right':
        #     # Sinusoidal cycling of brightness based upon column and timestep
        #     b_adj = np.abs( np.sin( np.pi * ( (c_ix - col_inc*(t % self.timesteps_per_cycle))/(n_c-1) ) ) if n_c > 1 else 1.0 )

        #     # With slower sinusoidal cycling of brightness based only upon time
        #     b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # elif c=='Left':
        #     # Sinusoidal cycling of brightness based upon column and timestep
        #     b_adj = np.abs( np.sin( np.pi * ( (c_ix - col_inc*(t % self.timesteps_per_cycle))/(n_c-1) ) ) ) if n_c > 1 else 1.0

        #     # With slower sinusoidal cycling of brightness based only upon time
        #     b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # Return the composite brightness value
        return b_fixed + (1.0-b_fixed) * b_adj


    def _pattern_ellipse( self, c, r_ix, c_ix, n_r, n_c, t:int=0, dist:int=0, prox:int=0 ):
        """
        Provide a rectangular pattern of brightness that invites a person to enter the space,
        with the pattern brighness overlaid with a slower overall variation in brightness
        akin to "breathing"
        """

        # Set shadow control LEDs to provide full brightness for LEDs
        # on the top row and with a fixed column spacing, which will generate
        # a specific, fixed (or possibly varying) shadow on the top of the model
        if r_ix in self.SHADOW_CONTROL_ROWS:
            return self.SHADOW_CONTROL_BRIGHTNESS if c_ix in self.SHADOW_CONTROL_COLUMNS else 0.0
      
        # Rate at which column should be incremented per timestep (LEDs/timestep)
        # [LED columns/timestep]=> # of Columns [LED columns/cycle] / Timesteps per Cycle [timesteps/cycle]
        col_inc = float(n_c) / self.timesteps_per_cycle

        # Rate at which "breathing" should be incremented per timestep
        # Breathing Rate = [One Breath (dim->bright->dim) / Cycle]
        BREATHING_RATE = 1.0

        # Breathing Increment [ Breaths / Timestep ] = [ One Breath (dim->bright->dim) / Cycle ] / Timesteps per Cycle [timesteps/cycle]
        breath_inc = BREATHING_RATE / self.timesteps_per_cycle

        # Brightness decomposed to a fixed base brightness level
        # plus an adjusted brightness that can vary based upon the various input parameters
        b_fixed = 0.3
        b_adj = 1.0

        # Establish the focus column of the image
        r_focus = n_r//2
        c_focus = n_c//2

        # Ellipse of brightness based upon row and column
        # overlaid with sinusoidal cycling of brightness based upon timestep only
        b_steep = 4.0
        b_adj = 1.0 - np.power( np.abs( r_focus-r_ix )**b_steep + np.abs( col_inc*(t % self.timesteps_per_cycle)-c_ix )**b_steep, 1.0/b_steep ) / np.power( r_focus**3 + c_focus**b_steep, 1.0/b_steep ) 

        # With slower sinusoidal cycling of brightness based only upon time
        b_adj = np.clip( b_adj, 0.0, 1.0 )
        b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # # Vary the adjustable part of the brightness by a slow-moving time function that simulates breathing rate.
        # if c=='Right':
        #     # Ellipse of brightness based upon row and column
        #     # overlaid with sinusoidal cycling of brightness based upon timestep only
        #     b_steep = 4.0
        #     b_adj = 1.0 - np.power( np.abs( r_focus-r_ix )**b_steep + np.abs( col_inc*(t % self.timesteps_per_cycle)-c_ix )**b_steep, 1.0/b_steep ) / np.power( r_focus**3 + c_focus**b_steep, 1.0/b_steep ) 

        #     # With slower sinusoidal cycling of brightness based only upon time
        #     b_adj = np.clip( b_adj, 0.0, 1.0 )
        #     b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # elif c=='Left':
        #     # Ellipse of brightness based upon row and column
        #     # overlaid with sinusoidal cycling of brightness based upon timestep only
        #     b_steep = 4.0
        #     b_adj = 1.0 - np.power( np.abs( r_focus-r_ix )**b_steep + np.abs( col_inc*(t % self.timesteps_per_cycle)-c_ix )**b_steep, 1.0/b_steep ) / np.power( r_focus**3 + c_focus**b_steep, 1.0/b_steep )

        #     # With slower sinusoidal cycling of brightness based only upon time
        #     b_adj = np.clip( b_adj, 0.0, 1.0 )
        #     b_adj *= np.abs( np.sin( np.pi * breath_inc*t ) )

        # Return the composite brightness value
        return b_fixed + (1.0-b_fixed) * b_adj


    def _pattern_range( self, c, r_ix, c_ix, n_r, n_c, t:int=0, dist:int=0, prox:int=0 ):
        """
        A basic diagnostic pattern showing the full range of brightness 0.0 to 1.0
        across the full range of row and column positions (0,0) to (n_r,n_c).
        Add a border of full-bright lights on each edge (0,0), (0,n_c), (n_r,0), (n_r, n_r)
        """

        # Set shadow control LEDs to provide full brightness for LEDs
        # on the top row and with a fixed column spacing, which will generate
        # a specific, fixed (or possibly varying) shadow on the top of the model
        if r_ix in self.SHADOW_CONTROL_ROWS:
            return self.SHADOW_CONTROL_BRIGHTNESS if c_ix in self.SHADOW_CONTROL_COLUMNS else 0.0
      
        # Initialize the brightness level
        b = 0

        # Border
        if (r_ix in [1, n_r-1]) or (c_ix in [0, n_c-1]):
            return 1.0

        # Low to High Brightness based upon row and column
        b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        # # Show the full range of brightness values on all components (sides, top) of the model
        # elif c=='Right':
        #     # Low to High Brightness based upon row and column
        #     b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        # elif c=='Left':
        #     # Low to High Brightness based upon row and column
        #     b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        return b


    def _pattern_off( self, c, r_ix, c_ix, n_r, n_c, t:int=0, dist:int=0, prox:int=0 ):
        """
        Set the brightness to its lowest level
        """
        return 0.0


    def _pattern_on( self, c, r_ix, c_ix, n_r, n_c, t:int=0, dist:int=0, prox:int=0 ):
        """
        Set the brightness to its highest level
        """
        return 1.0



    # ***********************************************
    # Methods to Simulate LED Behavior in the Model
    # ***********************************************
    def draw_simulated_model_framework(self):
        """
        Draw the main components of the model: sides, top
        """
        # Create background enclosure for the model
        MAX_IMAGE_SIZE = (1000,500)
        self.model = Image.new( "RGB", MAX_IMAGE_SIZE, color=(10,10,10) )

        # Prepare to draw objects
        model_draw = ImageDraw.Draw(self.model)

        for c in self.MODEL_CONFIG:
            model_draw.rectangle( self.MODEL_CONFIG[c]['bbox'], fill=self.MODEL_INTERIOR_COLOR, outline=self.MODEL_OUTLINE_COLOR )

    def draw_model_leds(self):
        """
        Draw LEDs on the model based upon the configurations
        of the model and the color for each LED (as RGB string)
        """

        # Prepare to draw objects
        model_draw = ImageDraw.Draw(self.model)

        # LEDs
        def _draw_led( xy, color=0x000000 ):
            """
            Draw one LED on simulated model
            * xy: tuple (x,y) specifying the location to draw the LED on the simulated model
            * color: RGB value encoded as an integer (0xRRGGBB)
            """
            # For some reason, ImageDraw expects hex encoded color to be encoded as 0xBBGGRR,
            # so need to extract the colors
            rgb = rgb_int_to_tuple( color )
            # print(xy, color, rgb)
            LED_RADIUS = 5
            model_draw.ellipse( [ (xy[0]-LED_RADIUS,xy[1]-LED_RADIUS), (xy[0]+LED_RADIUS,xy[1]+LED_RADIUS)], fill=rgb, outline='rgb(0,0,0)' )

        for c in self.MODEL_CONFIG:

            # Determine the width and height of this component
            bbox = self.MODEL_CONFIG[c]['bbox']
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            # How many columns and rows of LEDs need to fit in this space
            n_cols = self.MODEL_CONFIG[c]['leds']['cols']
            n_rows = self.MODEL_CONFIG[c]['leds']['rows']

            # Determine the number of pixels per LED,
            # Adding 1 to the count so that LEDs will not be placed on an edge
            pix_per_col = w // (n_cols + 1)
            pix_per_row = h // (n_rows + 1)

            # Draw the LEDs, starting with index 1 (to avoid an edge)
            for col in range(1,n_cols+1):
                for row in range(1, n_rows+1):

                    # Draw the LED using the specified color
                    if self.led_array[c][row-1][col-1]:
                        _draw_led( ( pix_per_col*col + bbox[0], pix_per_row*row + bbox[1] ), color=self.led_array[c][row-1][col-1] )
                    else:
                        _draw_led( ( pix_per_col*col + bbox[0], pix_per_row*row + bbox[1] ) )

