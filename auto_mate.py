import os
import sys
import time
import json
import imageio
import pyautogui
import contextlib
import skimage.metrics
import mouse_listener

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True


# I THINK that this wont work the same as reference script (thresh/mouse_listener)
# I THINK that this script needs to combine mouse + keyboard listening for recording
# I THINK I can do do with:
from pynput import mouse, keyboard
# ^(Using asyc/callbacks for each, and collecting them here as `Object action` or something like that.)
# https://pynput.readthedocs.io/en/latest/

# OTHERWISE.. maybe keep using PyUserInput && hooking keyboard too?
from pymouse import PyMouseEvent
from pykeyboard import PyKeyboard
# https://github.com/PyUserInput/PyUserInput


# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))

def record_sequence():
    print('record_sequence')

def playback_sequence():
    print('playback_sequence')

if __name__ == "__main__":
    #record_sequence()
    # click: {x,y}
    # click: {x,y}
    # type: str

    #with timer('calibrate_box'):
    #    mc = mouse_listener.mouse_listener('calibrate_box')
    #    mc.run()

    #with timer('calibrate_pos'):
    #    mc = mouse_listener.mouse_listener('calibrate_pos')
    #    mc.run()

    print('[fin.]')