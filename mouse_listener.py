import sys
import cv2
import json
import time
import imageio
import screen_pixel
from pymouse import PyMouseEvent

class mouse_listener(PyMouseEvent):
    _sp = None
    _coords_start = None
    _coords_stop = None
    _calibrating_box = False
    _calibrating_pos = False
    _calibrating_seq = False # Calibrate Sequence of events for replay.

    def __init__(self, state=None):
        PyMouseEvent.__init__(self)
        self._sp = screen_pixel.screen_pixel()

        if state == 'calibrate_pos':
            print('[Calibrating Pos: Click the area you would like to record!]')
            self._calibrating_pos = True
        elif state == 'calibrate_box':
            print('[Calibrating Box: Click at the top-left && drag to lower-right to select area.]')
            self._calibrating_box = True
        else:
            print('[Mouse Listening]')

    def click(self, x, y, button, press):
        int_x = int(x)
        int_y = int(y)

        if button==1 and press and self._calibrating_seq:
            print('Recorded Click!: ({0}, {1})'.format(int_x, int_y))

         # [Code for Pos selection]:
        if button==1 and press and self._calibrating_pos:
            print('Woomy!: ({0}, {1})'.format(int_x, int_y))
            self._coords_start = { "x":int_x, "y":int_y }
            self._sp.click_to(self._coords_start)
            self._calibrating_pos = False
            cv2.destroyAllWindows()
            self.stop()

        # [Code for Box selection]:
        if button==1 and self._calibrating_box:
            print('Woomy!: ({0}, {1})'.format(int_x, int_y))

            if press:
                self._coords_start = { "x":int_x, "y":int_y }
            else:
                self._coords_stop = { "x":int_x, "y":int_y }

            # [Send coords back over to bobberbot]:
            if self._coords_stop is not None:
                self._sp.draw_rect(self._coords_start, self._coords_stop, mod=1)
                nemo = self._sp.grab_rect(self._coords_start, self._coords_stop, mod=1)
                imageio.imwrite('calibrate_box.png',nemo)
                self._calibrating_box = False
                cv2.destroyAllWindows()
                self.stop()