import os
import sys
import time
#import json
import imageio
#import pyautogui
import contextlib
#import skimage.metrics   #Move SSIM to screen_pixel functions for auto_mate
from pynput import mouse, keyboard
#import mouse_listener

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))

def booya():
    return 'woomy!'

# [Use `pynput` for listening with asyc/callbacks]:
# [Use `pynput` for controlling mouse/keyboard]:
# https://pynput.readthedocs.io/en/latest/
# https://pythonhosted.org/pynput/keyboard.html




# [-]: Find better/prettier way to create windows in Python.
# [0]: Switch  library to `pynput` for mouse/keyboard listening/control(?)
# [1]: Switch to using callbacks from listeners to call actions (pos/grab)
# [2]: Create class/json for `action` (Click, drag(screengrab for SSIM), etc)
# [3]: Record Sequence of actions
# [4]: Playback Sequence of actions
# [5]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right. 
if __name__ == "__main__":
    print(booya())

    print('[fin.]')

    '''
    #with timer('calibrate_box'):
    #    mc = mouse_listener.mouse_listener('calibrate_box')
    #    mc.run()

    #with timer('calibrate_pos'):
    #    mc = mouse_listener.mouse_listener('calibrate_pos')
    #    mc.run()
    '''