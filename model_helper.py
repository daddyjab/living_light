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
                'leds': { 'rows': 10, 'cols': 7 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ 207, 210, 230, 234, None, 258, 278 ],
                                    [ 206, 211, 229, 235, 254, 259, 277 ],
                                    [ 205, 212, 228, 236, 253, 260, 276 ],
                                    [ 204, 213, 227, 237, 252, 261, 275 ],
                                    [ 203, 214, 226, 238, 251, 262, 274 ],
                                    [ 202, 215, 225, 239, 250, 263, 273 ],
                                    [ 201, 216, 224, 240, 249, 264, 272 ],
                                    [ 200, 217, 223, 241, 248, 265, 271 ],
                                    [ 199, 218, 222, 242, 247, 266, 270 ],
                                    [ 198, None, 221, 243, 246, None, 269 ]
                                    ]),

                # Simulated: Dimensions of this component in the simulated model
                'bbox': (0,600, 600,1000),                
                },

            'Top': {
                # Arrangement of LEDs in this model (real or simulated)
                'leds': { 'rows': 3, 'cols': 17 },

                # Real: Mapping of the rows/cols and physical LED numbers on the LED Strip
                #       Set as a np.array of shape defined by leds => rows/cols above
                'led_ids': np.array([
                                    [ 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175, 174, 173, 172 ],
                                    [ None, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168 ],
                                    [ None, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134 ]
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
                'bbox': (1000,600, 1600,1000),
                },
        }

        # Initialize dictionaries aligned to the model configuration
        self.brightness_vals = {}
        self.led_array = {}
        for c in self.MODEL_CONFIG:
            # Array of brightness values [0.0 to 1.0] for each model component
            self.brightness_vals[c] = np.zeros( (self.MODEL_CONFIG[c]['leds']['rows'], self.MODEL_CONFIG[c]['leds']['cols']) )        

            # Array of integer-encoded RGB values (e.g., 0x7FFF00) for each model component
            self.led_array[c] = np.zeros( (self.MODEL_CONFIG[c]['leds']['rows'], self.MODEL_CONFIG[c]['leds']['cols']), dtype='int')


        # Model Scenarios
        self.MODEL_SCENARIO_CONFIG = {

            # Normal Scenarios
            'Idle': { 'color_profile': '40W Tungsten', 'led_pattern': 'Ellipse' },
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

        # Brightness Pattern Functions
        self.BRIGHTNESS_PATTERN_FUNCTION = {
            'Come In': self._pattern_come_in,
            'Ellipse': self._pattern_ellipse,
            'Range': self._pattern_range,
            'Off': self._pattern_off,
            'On': self._pattern_on,
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


    def init_model_scenario( self, scenario:str='Idle' ):
        """
        Set the overall lighting scenario in use by the Model
        """

        # Store the current scenario type in this object
        self.scenario = scenario

        # Other scenario-specific processing is done in real-time to provide for
        # lighting patterns that respond to distance and other sensor data
        pass


    def update_led_pattern(self, timestep:int=None, distance:tuple=None, proximity:dict=None ):
        """
        Within the main loop, update the LED pattern that is currently
        running based upon the timestep that is specified

        Do what's needed to make one update to the LEDs based upon:
        * The current scenario (and associated LED Pattern and Color Profile)
        * The current timestep
        * Distance measured to objects in the Model
        * Proximity of objects to Entrance or Exit

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
            rgb = hls_to_rgb_tuple( (h_prof, b*l_prof, s_prof) )
            return rgb_tuple_to_int( rgb )

        # Use the LED Pattern specified in the Light Scenario
        led_pattern = self.MODEL_SCENARIO_CONFIG[self.scenario]['led_pattern']

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
                            timestep, distance, proximity )

                    # Translate the brightness value into an integer-encoded RGB
                    # value based upon the selected color profile
                    led_col[...] = _helper_brightness_to_rgb_in_profile( b_val )

        # Update the LEDs (using either physical LEDs or simulated LEDs)
        self.draw_model_leds()


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

