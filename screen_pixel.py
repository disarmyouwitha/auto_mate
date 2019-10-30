import os
import sys
import cv2
import json
import time
import numpy
import imageio
import pyautogui

# [Import Quartz for OSX, else use MSS]: (for screen_pixel.capture())
if sys.platform == 'darwin':
    import Quartz.CoreGraphics as CG
else:
    import mss

class screen_pixel(object):
    _data = None
    _numpy = None
    _width = None
    _height = None

    def capture(self):
        if sys.platform == 'darwin':
            self.capture_osx()
        else:
            self.capture_mss()

    def capture_osx(self):
        region = CG.CGRectInfinite

        # [Create screenshot as CGImage]:
        image = CG.CGWindowListCreateImage(region, CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID, CG.kCGWindowImageDefault)

        # [Intermediate step, get pixel data as CGDataProvider]:
        prov = CG.CGImageGetDataProvider(image)

        # [Copy data out of CGDataProvider, becomes string of bytes]:
        self._data = CG.CGDataProviderCopyData(prov)

        # [Get width/height of image]:
        self._width = CG.CGImageGetWidth(image)
        self._height = CG.CGImageGetHeight(image)

        # [Get raw pixels from the screen, save it to a Numpy array as RGB]:
        imgdata=numpy.frombuffer(self._data,dtype=numpy.uint8).reshape(int(len(self._data)/4),4)
        _numpy_bgr = imgdata[:self._width*self._height,:-1].reshape(self._height,self._width,3)
        _numpy_rgb = _numpy_bgr[...,::-1]
        self._numpy = _numpy_rgb
        #imageio.imwrite('screen.png', self._numpy)

    def capture_mss(self):
        with mss.mss() as sct:
            # [Equivalent to CG.CGRectInfinite]:
            monitor = sct.monitors[0] #0: All | 1: first | 2: second
            self._width = monitor['width']
            self._height = monitor['height']

            # [Get raw pixels from the screen, save it to a Numpy array as RGB]:
            _numpy_bgr = numpy.array(sct.grab(monitor))
            _numpy_rgb = cv2.cvtColor(_numpy_bgr, cv2.COLOR_BGR2RGB)
            self._numpy = _numpy_rgb
            #imageio.imwrite('screen_mss.png', self._numpy)

    def resize_image(self, nemo, scale_percent=50):
        width = int(nemo.shape[1] * scale_percent / 100)
        height = int(nemo.shape[0] * scale_percent / 100)
        dim = (width, height)
        nemo_scaled = cv2.resize(nemo, dim, interpolation = cv2.INTER_AREA)
        return nemo_scaled 

    # [To facilitate screen grabbing Box area]:
    def grab_rect(self, json_coords_start, json_coords_stop, mod=1):
        _start_x = json_coords_start.get('x')
        _start_y = json_coords_start.get('y')
        start_x = (_start_x*mod)
        start_y = (_start_y*mod)

        _stop_x = json_coords_stop.get('x')
        _stop_y = json_coords_stop.get('y')
        stop_x = (_stop_x*mod)
        stop_y = (_stop_y*mod)

        # [Trim _numpy array to rect]:
        self.capture()
        return self._numpy[start_y:stop_y,start_x:stop_x]

    def draw_rect(self, json_coords_start, json_coords_stop, mod=1):
        _start_x = json_coords_start.get('x')
        _start_y = json_coords_start.get('y')
        _start_x = (_start_x*mod)
        _start_y = (_start_y*mod)

        _stop_x = json_coords_stop.get('x')
        _stop_y = json_coords_stop.get('y')
        _stop_x = (_stop_x*mod)
        _stop_y = (_stop_y*mod)

        # [Draw box around Scan Area specified with mouse]:
        print('Pause. Drawing scan area with mouse:')
        time.sleep(2)

        _diff_x = (_stop_x - _start_x)
        _diff_y = (_stop_y - _start_y)
        pyautogui.moveTo(_start_x, _start_y, duration=1)
        pyautogui.moveTo((_start_x+_diff_x),_start_y, duration=1)
        pyautogui.moveTo((_start_x+_diff_x),(_start_y+_diff_y), duration=1)
        pyautogui.moveTo(_start_x,(_start_y+_diff_y), duration=1)
        pyautogui.moveTo(_start_x,_start_y, duration=1)

    def move_to(self, json_coords_start, dura=1):
        # [Draw box around Scan Area specified with mouse]:
        print('Pause. (2sec) Moving mouse to recorded Pos:')
        time.sleep(2)

        pyautogui.moveTo(json_coords_start.get('x'), json_coords_start.get('y'), duration=dura)
    
    def click_to(self, json_coords_start, dura=1):
        self.move_to(json_coords_start, dura)
        pyautogui.leftClick(x=json_coords_start.get('x'), y=json_coords_start.get('y'))