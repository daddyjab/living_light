# import numpy as np
# from PIL import Image, ImageDraw, ImageColor
# import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
# from IPython.display import HTML
from IPython.display import Image as disp_Image
import colorsys
# import re

def display_images( images=None, ms=50, loop=10 ):
     """
     Animate a list of images by creating a GIF file
     then displaying the resulting GIF file
     """

     # Save options
     save_opts = { 'fp':'dev_animated_image.png', 'format':'GIF' }

     # Get the first image and setup for any remaining images
     try:
          first_img = images[0]
          SAVE_MULTI_OPTS = { 'append_images':images[1:], 'save_all':True, 'duration':ms, 'loop':loop }
          save_opts.update(SAVE_MULTI_OPTS)

     except TypeError:
          first_img = images

     # Save the image to a temp file as a GIF
     # (but with extention *.png as required by disp_Image (i.e., display.Image))
     first_img.save(**save_opts)

     # Display the GIF from the temp file
     display( disp_Image( filename=save_opts["fp"], format='png') )

def rgb_to_string( rgb:tuple ) -> str:
     return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

def rgb_string_to_tuple( rgb_str:str ) -> tuple:
     return tuple([ int(x) for x in rgb_str.replace('rgb(','').replace(')','').split(',') ])


def rgb_int_to_hls( rgb:tuple ) -> tuple:
     """
     Convert RGB to HLS
     RGB: Values 0 to 255
     HLS: Values 0.0 to 1.0
     """
     return colorsys.rgb_to_hls( *[ x/255.0 for x in rgb ])


def rgb_int_to_hsv( rgb:tuple ) -> tuple:
     """
     Convert RGB to HSV
     RGB: Values 0 to 255
     HSV: Values 0.0 to 1.0
     """
     return colorsys.rgb_to_hsv( *[ x/255.0 for x in rgb ])


def hsv_to_rgb_int( hsv:tuple ) -> tuple:
     """
     Convert HSV to RGB
     HSV: Values 0.0 to 1.0
     RGB: Values 0 to 255
     """
     return [ int(round(255*x)) for x in colorsys.hsv_to_rgb(*hsv) ]


def hls_to_rgb_int( hls:tuple ) -> tuple:
     """
     Convert HLS to RGB
     HLS: Values 0.0 to 1.0
     RGB: Values 0 to 255
     """
     return [ int(round(255*x)) for x in colorsys.hls_to_rgb(*hls) ]

