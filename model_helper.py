from multiprocessing import cpu_count
import numpy as np
import logging
from PIL import Image, ImageDraw, ImageColor

from display_helper import *

class Model():
    """
    Class representing the sides and top of the model and their LEDs
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
                                    [ 122, 101, 99, 78, 75, 55, 52, 32, 28 ],
                                    [ 121, 102, 98, 79, 74, 56, 51, 33, 27 ],
                                    [ 120, 103, 97, 80, 73, 57, 50, 34, 26 ],
                                    [ 119, 104, 96, 81, 72, 58, 49, 35, 25 ],
                                    [ 118, 105, 95, 82, 71, 59, 48, 36, 24 ],
                                    [ 117, 106, 94, 83, 70, 60, 47, 37, 23 ],
                                    [ 116, 107, 93, 84, 69, 61, 46, 38, 22 ],
                                    [ 115, 108, 92, 85, 68, 62, 45, 39, 21 ],
                                    [ 114, 109, 91, 86, 67, 63, 44, 40, 20 ],
                                    [ 113, 110, 90, 87, 66, None, 43, None, 19 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                # 'bbox': (0,200, 200,400),
                'bbox': (0,600, 600,1000),                
                },

            'Top': {
                # Arrangement of LEDs in this model (real or simulated)
                'leds': { 'rows': 3, 'cols': 17 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, None ],
                                    [ 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, None ],
                                    [ 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                'bbox': (600,0, 1000,600),
                },

            'Right': {
                # Arrangement of LEDs in this model (real or simulated)
                'leds': { 'rows': 10, 'cols': 9 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ None, None, 278, 258, None, 234, 230, 210, 207 ],
                                    [ None, None, 277, 259, 254, 235, 229, 211, 206 ],
                                    [ None, None, 276, 260, 253, 236, 228, 212, 205 ],
                                    [ None, None, 275, 261, 252, 237, 227, 213, 204 ],
                                    [ None, None, 274, 262, 251, 238, 226, 214, 203 ],
                                    [ None, None, 273, 263, 250, 239, 225, 215, 202 ],
                                    [ None, None, 272, 264, 249, 240, 224, 216, 201 ],
                                    [ None, None, 271, 265, 248, 241, 223, 217, 200 ],
                                    [ None, None, 270, 266, 247, 242, 222, 218, 199 ],
                                    [ None, None, 269, None, 246, 243, 221, None, 198 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                'bbox': (1000,600, 1600,1000),
                },
        }

        # Model Scenarios
        self.MODEL_SCENARIO_CONFIG = {

            # Normal Scenarios
            'Idle': { 'color_profile': '40W Tungsten', 'led_pattern': 'Come In' },
            'Standard': { 'color_profile': 'High Noon Sun', 'led_pattern': 'Come In' },
            'Energy': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Come In' },

            # Diagnostic Scenarios (all performed with brightest color profile)
            'diag_calibrate_distance': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'On' },
            'diag_come_in': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Come In' },
            'diag_ellipse': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Ellipse' },
            'diag_range': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Range' },
            'diag_all_on': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'On' },
            'diag_all_off': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Off' },

            # Obsolete Scenarios
            # 'Brightness Range': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Range' },
            # 'Off': { 'color_profile': 'Direct Sunlight', 'led_pattern': 'Off' },
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

        # Initialize but don't start the default scenario
        logging.info("Initializing Lighting Scenario: Idle")
        self.init_model_scenario( scenario='Idle' )


    # ***********************************************
    # Methods to Simulate LED Behavior in the Model
    # ***********************************************
    def draw_model_sides_top(self):
        """
        Draw the main components of the model: sides, top
        """
        # Create background enclosure for the model
        MAX_IMAGE_SIZE = (1600,1000)
        self.model = Image.new( "RGB", MAX_IMAGE_SIZE, color=(10,10,10) )

        # Prepare to draw objects
        model_draw = ImageDraw.Draw(self.model)

        for c in self.MODEL_CONFIG:
            model_draw.rectangle( self.MODEL_CONFIG[c]['bbox'], fill=self.MODEL_INTERIOR_COLOR, outline=self.MODEL_OUTLINE_COLOR )

    def draw_model_leds(self, led_colors:dict=None ):
        """
        Draw LEDs on the model based upon the configurations
        of the model and the color for each LED (as RGB string)
        """

        # Prepare to draw objects
        model_draw = ImageDraw.Draw(self.model)

        # LEDs
        def _draw_led( xy, color='rgb(0,0,0)' ):
            """
            Draw one LED
            """
            LED_RADIUS = 5
            model_draw.ellipse( [ (xy[0]-LED_RADIUS,xy[1]-LED_RADIUS), (xy[0]+LED_RADIUS,xy[1]+LED_RADIUS)], fill=color, outline='rgb(0,0,0)' )

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
                    if led_colors:
                        _draw_led( ( pix_per_col*col + bbox[0], pix_per_row*row + bbox[1] ), color=led_colors[c][row-1][col-1] )
                    else:
                        _draw_led( ( pix_per_col*col + bbox[0], pix_per_row*row + bbox[1] ) )

    # ***********************************************
    # Methods for Mapping Brightness
    # within Color Profile to LED Colors
    # ***********************************************

    def get_color_profile( self, source=None, temp=None ):
        """
        Set RGB color values based upon light source or light temperature

        Reference:
        * http://planetpixelemporium.com/tutorialpages/light.html
        """

        if (source is not None) and (temp is None):
            return { source: self.COLOR_PROFILE[source] }

        if (source is None) and (temp is not None):
            for source in self.COLOR_PROFILE:
                if temp == self.COLOR_PROFILE[source]['temp']:
                    return { source: self.COLOR_PROFILE[source] }

        return self.COLOR_PROFILE


    # Create arrays representing the LED colors
    def map_led_brightness_to_rgb_string(self, brightness_array=None, c_profile='Direct Sunlight' ) -> np.ndarray:
        """
        Maps an array of scalar values in the range [0.0 to 1.0] and maps it to RGB value strings
        that are consistent with the specified or default color profile.
        The mapping is done by:
        1. Converting the color profile base RGB to the Hue, Lightness, Saturation (HLS) color scheme
        2. Then adjusting only the Lightness factor proportional to the brightness value in the input array
        3. Doing the above for each element in the array
        """

        # Create a numpy array of the same dimension as the input brightness array
        led_array = np.full_like( brightness_array, fill_value=np.nan )

        # Clip the values in the brightness array to the range [0.0 to 1.0]
        b_array = np.clip( brightness_array, 0.0, 1.0 )

        # Get the base HLS values that correspond to the color profile RGB
        h_prof, l_prof, s_prof = rgb_int_to_hls( np.array(self.COLOR_PROFILE[c_profile]['rgb']) )

        # Helper function to map 
        def _helper_brightness_to_rgb_in_profile( b:float=None ) -> tuple:
            # Adjust the lightness factor based upon the brightness value [0.0 to 1.0]
            rgb = hls_to_rgb_int( (h_prof, b*l_prof, s_prof) )
            return rgb_to_string( rgb )

        # Perform a vector operation on all of the input array values
        led_array = np.vectorize( _helper_brightness_to_rgb_in_profile )( brightness_array )

        # Return the array of LED RGB string values
        return led_array        


    def led_test_pattern(self, pattern='Range', color_profile='Direct Sunlight' ) -> np.ndarray:
        """
        Create a test pattern of LED colors (dictionary of arrays containing RGB strings)

        * pattern:
            'Range': LEDs are set to display the full range of brightness for the specified color profile [default]
            'Random': Each LED set to a random brightness for the specified color profile
            'On': All LEDs set to maximum brightness for the specified color profile
            'Off': All LEDs set to the minimum brightness for the specified color profile

        * color_profile: Color Profile selection from self.COLOR_PROFILE [default: 'Direct Sunlight']
        """
        led_colors = {}
        for c in self.MODEL_CONFIG:

            # Component LED config
            rows = self.MODEL_CONFIG[c]['leds']['rows']
            cols = self.MODEL_CONFIG[c]['leds']['cols']

            # Create an array of the proper dimensions for this component of the model
            b_arr = np.zeros( (rows,cols) )

            if pattern.lower() == 'random':
                # Set each LED to a random brightness
                b_arr = np.random.rand( rows, cols )

            elif pattern.lower() == 'on':
                # Set all LEDs to on / maximum brightness
                b_arr = np.ones( (rows,cols) )

            elif pattern.lower() == 'off':
                # Set all LEDs to off / minimium brightness
                # Note: No additional action required for this
                pass

            else:
                # Set the LEDs to show the full range of brightness from 0.0 to 1.0 
                for row_ix in range(rows):
                    for col_ix in range(cols):
                        b_arr[row_ix,col_ix] = float(row_ix)/(rows-1) if rows > 1 else 1.0
                        b_arr[row_ix,col_ix] *= float(col_ix)/(cols-1) if cols > 1 else 1.0

            # get the LED colors for this component based upon the specified Color Profile
            led_colors[c] = self.map_led_brightness_to_rgb_string( b_arr, color_profile )

        # Return a dictionary with arrays of LED colors that match the components of the Model
        return led_colors

    def init_model_scenario( self, scenario:str='Idle' ):
        """
        Set the overall lighting scenario in use by the Model
        """

        # Store the scenario in this object
        self.scenario = scenario

        # Stop any currently running scenario and prepare (but don't start) the requested scenario
        # @TODO
        pass


    def update_led_pattern(self, timestep:int=None, distance:tuple=None, proximity:dict=None, override_cp:str=None, override_pat:str=None ):
        """
        Within the main loop, update the LED pattern that is currently
        running based upon the timestep that is specified

        Do what's needed to make one update to the LEDs based upon:
        * The current scenario (and associated LED Pattern and Color Profile)
        * The current timestep
        * Distance measured to objects in the Model
        * Proximity of objects to Entrance or Exit
        """

        # Use the Color Profile specified in the Light Scenario,
        # unless an override Color Profile has been provided
        if override_cp:
            color_profile = override_cp
        else:
            color_profile = self.MODEL_SCENARIO_CONFIG[self.scenario]['color_profile']

        # Use the LED Pattern specified in the Light Scenario,
        # unless an override LED Pattern has been provided
        if override_pat:
            led_pattern = override_pat
        else:
            led_pattern = self.MODEL_SCENARIO_CONFIG[self.scenario]['led_pattern']

        # Functions that implement LED patterns 
        BRIGHTNESS_PATTERN_FUNCTION = {
            'Come In': self._pattern_come_in,
            'Ellipse': self._pattern_ellipse,
            'Range': self._pattern_range,
            'Off': self._pattern_off,
            'On': self._pattern_on,
        }

        # Increment the LED pattern and return an array of RGB color strings for each Model component
        # Use a specified Bightness Pattern Function associated with the current scenario
        # to generate a set of RGB string values for each of the components of the model
        brightness_vals = {}
        led_colors = {}
        for c in self.MODEL_CONFIG:

            # Component LED config
            rows = self.MODEL_CONFIG[c]['leds']['rows']
            cols = self.MODEL_CONFIG[c]['leds']['cols']

            # Create an array of the proper dimensions for this component of the model
            brightness_vals[c] = np.zeros( (rows,cols) )

            # Set the LEDs to show the full range of brightness from 0.0 to 1.0 
            for row_ix in range(rows):
                for col_ix in range(cols):

                    # Generate brightness levels based upon a supplied function
                    brightness_vals[c][row_ix,col_ix] = BRIGHTNESS_PATTERN_FUNCTION[led_pattern]( c, row_ix, col_ix, rows, cols, timestep, distance, proximity )

            # Convert brightness levels to RGB strings
            led_colors[c] = self.map_led_brightness_to_rgb_string( brightness_vals[c], color_profile )
        
        # Update the LEDs (either physical LEDs or simulated LEDs)
        self.draw_model_leds( led_colors )


    # **********************************************************************************************
    # Brightness Pattern Functions, which LED brightness/behavior
    # based upon location of the LED, the number of LEDs on the component (sides, top),
    # current timestep, measured distance to an object, and objects in proximity to entrance/exit
    #
    # Note:
    # * Respiration rate at rest (adult normal): 12 to 20 breaths per minute => 3 to 5 seconds per breath
    # * Respiration rate after brisk walk (adul normal): 30 breaths per minute => 2 seconds per breath
    # * Respiration rate during exercise (adult normal): 40-60 breaths per minute => 1 to 1.5 seconds per breath
    # **********************************************************************************************
    def _pattern_come_in( self, c, r_ix, c_ix, n_r, n_c, t=0, dist:tuple=None, prox:dict=None ):
        """
        Provide a brightness patternt that invites a person to enter the space
        """

        # Brightness decomposed to a fixed base brightness level
        # plus an adjusted brightness that can vary based upon the various input parameters
        b_fixed = 0.3
        b_adj = 1.0

        # Vary the adjustable part of the brightness by a slow-moving time function that simulates breathing rate.
        if c=='Right':
            # Sinusoidal cycling of brightness based upon column and timestep
            b_adj = np.abs( np.sin( np.pi * ( (c_ix + t)/(n_c-1) ) ) if n_c > 1 else 1.0 )
            b_adj *= np.abs( np.sin( np.pi * t/40 ) )

        elif c=='Top':
            # Sinusoidal cycling of brightness based upon column and timestep
            b_adj = np.abs( np.sin( np.pi * ( (c_ix + t)/(n_c-1) ) ) if n_c > 1 else 1.0 )
            b_adj *= np.abs( np.sin( np.pi * t/40 ) )

        elif c=='Left':
            # Sinusoidal cycling of brightness based upon column and timestep
            b_adj = np.abs( np.sin( np.pi * ( (c_ix - t)/(n_c-1) ) ) ) if n_c > 1 else 1.0
            b_adj *= np.abs( np.sin( np.pi * t/40 ) )

        # Return the composite brightness value
        return b_fixed + (1.0-b_fixed) * b_adj


    def _pattern_ellipse( self, c, r_ix, c_ix, n_r, n_c, t=0, dist:tuple=None, prox:dict=None ):
        """
        Provide a brightness patternt that invites a person to enter the space
        """

        # Brightness decomposed to a fixed base brightness level
        # plus an adjusted brightness that can vary based upon the various input parameters
        b_fixed = 0.3
        b_adj = 1.0

        # Establish the focus column of the image
        r_focus = n_r//2
        c_focus = n_c//2

        # Vary the adjustable part of the brightness by a slow-moving time function that simulates breathing rate.
        if c=='Right':
            # Ellipse of brightness based upon row and column
            # overlaid with sinusoidal cycling of brightness based upon timestep only
            b_steep = 4.0
            t_breathe = 50
            b_adj = 1.0 - np.power( np.abs( r_focus-r_ix )**b_steep + np.abs( (n_c-(t % n_c))-c_ix )**b_steep, 1.0/b_steep ) / np.power( r_focus**3 + c_focus**b_steep, 1.0/b_steep ) 
            b_adj = np.clip( b_adj, 0.0, 1.0 ) * np.abs( np.sin( np.pi * t/t_breathe ) )

        elif c=='Top':
            # Sinusoidal cycling of brightness based upon timestep only
            t_breathe = 50
            b_adj = np.abs( np.sin( np.pi * t/t_breathe ) )

        elif c=='Left':
            # Ellipse of brightness based upon row and column
            # overlaid with sinusoidal cycling of brightness based upon timestep only
            b_steep = 4.0
            t_breathe = 50
            b_adj = 1.0 - np.power( np.abs( r_focus-r_ix )**b_steep + np.abs( (t % n_c)-c_ix )**b_steep, 1.0/b_steep ) / np.power( r_focus**3 + c_focus**b_steep, 1.0/b_steep )
            b_adj = np.clip( b_adj, 0.0, 1.0 ) * np.abs( np.sin( np.pi * t/t_breathe ) )

        # Return the composite brightness value
        return b_fixed + (1.0-b_fixed) * b_adj

    def _pattern_range( self, c, r_ix, c_ix, n_r, n_c, t=0, dist:tuple=None, prox:dict=None ):
        """
        A basic diagnostic pattern showing the full range of brightness 0.0 to 1.0
        across the full range of row and column positions (0,0) to (n_r,n_c)
        """

        # Initialize the brightness level
        b = 0

        # Show the full range of brightness values on all components (sides, top) of the model
        if c=='Right':
            # Low to High Brightness based upon row and column
            b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        elif c=='Top':
            # Low to High Brightness based upon row and column
            b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        elif c=='Left':
            # Low to High Brightness based upon row and column
            b = (float(r_ix)/(n_r-1) if n_r > 1 else 1.0) * (float(c_ix)/(n_c-1) if n_c > 1 else 1.0)

        return b

    def _pattern_off( self, c, r_ix, c_ix, n_r, n_c, t=0, dist:tuple=None, prox:dict=None ):
        """
        Set the brightness to its lowest level
        """
        return 0.0

    def _pattern_on( self, c, r_ix, c_ix, n_r, n_c, t=0, dist:tuple=None, prox:dict=None ):
        """
        Set the brightness to its highest level
        """
        return 1.0

