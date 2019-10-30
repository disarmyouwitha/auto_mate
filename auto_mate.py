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

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))

def booya():
    return 'woomy!'

if __name__ == "__main__":
    print('Booya!')
    #with timer('calibrate_box'):
    #    mc = mouse_listener.mouse_listener('calibrate_box')
    #    mc.run()

    #with timer('calibrate_pos'):
    #    mc = mouse_listener.mouse_listener('calibrate_pos')
    #    mc.run()