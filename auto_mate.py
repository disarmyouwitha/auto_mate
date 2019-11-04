import os
import sys
import time
import json
import contextlib
from pynput import mouse, keyboard

class action():
    _id = 0
    _state = None
    _action_id = 0
    _coords_list = None

    # Check if coords_list is actually a list?
    def __init__(self, state=None, coords_list=None):
        self._state = state
        self._action_id = action._id
        self._coords_list = coords_list

        # [If coords weren't sent as list, add as list]:
        if type(coords_list)!=list:
            self._coords_list = [coords_list]

        #self.print_info()

        # [Class ID incremetor]:
        action._id+=1
        

    def print_info(self):
        for _coord in self._coords_list:
            print('Coords added to action{0}({1}): {2}'.format(self._action_id, self._state, _coord))


# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


# https://pynput.readthedocs.io/en/latest/
# https://pythonhosted.org/pynput/keyboard.html
# [-]: Find better/prettier way to create windows in Python.
# [0]: on CLICK -- Create action('pos', {click_coords})
# ^ (POS coords are used for click replay)
# [1]: on DRAG -- Create action('box', {start_coords, stop_coords})
# ^ (BOX coords are used for SSIM checking)
# [-]: Create class/json for `action` (Click, drag(screengrab for SSIM), etc)
# [0]: Record Sequence of actions
# [1]: Playback Sequence of actions
# [2]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right. 
if __name__ == "__main__":
    action_items = []
    action_items.append(action('pos', {'x': 3, 'y': 3}))
    action_items.append(action('pos', [{'x': 7, 'y': 7}]))
    action_items.append(action('box', [{'x': 0, 'y': 0}, {'x': 10, 'y': 10}]))

    # [Try from config file]:
    config_filename = 'try_coords.json'
    with open(config_filename) as config_file:
        configs = json.load(config_file)

    coords = []
    coords.append(configs['scanarea_start'])
    coords.append(configs['scanarea_stop'])
    action_items.append(action('box', coords))

    # [action_items list for replay]:
    for _action in action_items:
        _action.print_info()
