import os
import sys
import time
import json
import contextlib
import pynput.mouse as ms
import pynput.keyboard as kb
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Controller

#class omni_listener():

# [GLOBALS]:
action_items = []

# [MOUSE GLOBALS]:
_click_int_x = None
_click_int_y = None
_mouse_record = True

# [KEYBOARD GLOBALS]:
_typed_last = 0
_keyboard_buffer = ''
_hold_ALT = False
_hold_TAB = False
_hold_SHIFT = False
_CMD_input = False

def on_press(key):
    global _mouse_record, _typed_last, _keyboard_buffer, _click_int_x, _click_int_y, _hold_SHIFT, _hold_ALT, _hold_TAB, _CMD_input

    # [CMD_input for passwords, etc]:
    if _CMD_input:
        return

    check_keyboard_buffer()

    try:
        _key = key.char
        if _typed_last == 0:
            _typed_last = time.time()

        _keyboard_buffer+=key.char
        _typed_last = time.time()
    except AttributeError:
        # [Pass-through on other special characters]: 
        #print('special key {0} pressed'.format(key))
        # ^DEBUGG

        # [If SHIFT is pressed]:
        if key == kb.Key.shift:
            _hold_SHIFT = True

        # [if backspace, pop last character from buffer]:
        if key == kb.Key.backspace:
            _keyboard_buffer = _keyboard_buffer[:-1]

        # [Add space for spacebar xD]:
        if key == kb.Key.space:
            _keyboard_buffer+=' '

        # [If ALT is pressed]:
        if key == kb.Key.alt:
            _hold_ALT = True

        # [If TAB is pressed]:
        if key == kb.Key.tab:
            _hold_TAB = True
            check_keyboard_buffer(interrupt=True)

            # [Ignore Alt-tab]:
            if _hold_ALT:
                print('alt-tab')
                pass
            else:
                _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
                action_items.append(_act)

        # [If ENTER is pressed]:
        if key == kb.Key.enter:
            check_keyboard_buffer(interrupt=True)
            _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
            action_items.append(_act)

        # [If CTRL is pressed]:
        if key == kb.Key.ctrl:
            print('[stopping listeners!]')
            _mouse_record = False

def on_release(key):
    global _hold_SHIFT, _hold_ALT, _hold_TAB

    if key == kb.Key.alt:
        _hold_ALT = False

    if key == kb.Key.tab:
        _hold_TAB = False

    if key == kb.Key.shift:
        _hold_SHIFT = False

def check_keyboard_buffer(interrupt=False):
    global _typed_last, _keyboard_buffer, _click_int_x, _click_int_y

    if interrupt==True or ((_typed_last > 0) and (time.time() - _typed_last) >= 2):
        if _keyboard_buffer != '':
            # [Action for Keyboard takes x,y of last click and keyboard_buffer]:
            _act = action('keyboard', {'x': _click_int_x, 'y': _click_int_y}, _keyboard_buffer)
            action_items.append(_act)

        _keyboard_buffer=''
        _typed_last=0

def on_click(x, y, button, pressed):
    global _mouse_record, _click_int_x, _click_int_y, _hold_SHIFT, _CMD_input
    _int_x = int(x)
    _int_y = int(y)

    check_keyboard_buffer()

    if pressed:
        #print('Pressed at: {0}'.format((_int_x, _int_y)))
        _click_int_x = int(x)
        _click_int_y = int(y)
    else:
        #print('Released at: {0}'.format((_int_x, _int_y)))

        # [Turn off CMD_input after click]:
        if _CMD_input:
            _CMD_input = False
            return

        # [SHIFT held while clicking | Enter Password]:
        if _hold_SHIFT:
            _CMD_input = True
            _pass = input('Enter password here: ')
            _act = action('pass', {'x': _click_int_x, 'y': _click_int_y}, _pass)
            action_items.append(_act)

            print('Click field to resume! / Please use Submit instead of Enter')
            return

        # [SAME = POS | DIFF = BOX]:
        if _int_x == _click_int_x and _int_y == _click_int_y:
            _act = action('pos', [{'x': _int_x, 'y': _int_y}])
            action_items.append(_act)
        else:
            _act = action('box', [{'x': _click_int_x, 'y': _click_int_y}, {'x': _int_x, 'y': _int_y}])
            action_items.append(_act)

def on_move(x, y):
    _int_x = int(x)
    _int_y = int(y)

    check_keyboard_buffer()
    #print('Pointer moved to {0}'.format((_int_x, _int_y)))

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


class action():
    _id = 0
    _state = None
    _action_id = 0
    _coords_list = None
    _keyboard_buffer = ''

    # Check if coords_list is actually a list?
    def __init__(self, state=None, coords_list=None, keyboard_buffer=None):
        self._state = state
        self._action_id = action._id
        self._coords_list = coords_list
        self._keyboard_buffer = keyboard_buffer

        # [If coords weren't sent as list, add as list]:
        if coords_list and type(coords_list)!=list:
            self._coords_list = [coords_list]

        #self.print_info()

        # [Class ID incremetor]:
        action._id+=1

    def print_info(self):
        for _coord in self._coords_list:
            print('Added to action{0}({1}): {2} | {3}'.format(self._action_id, self._state, _coord, self._keyboard_buffer))


def action_replay(action):
    mouse = ms.Controller()
    keyboard = kb.Controller()
    action.print_info() ##

    # [POS| Click Position]:
    if action._state == 'pos':
        _x = action._coords_list[0].get('x')
        _y = action._coords_list[0].get('y')

        # Set pointer position
        mouse.position = (_x, _y)

        # Press and release
        #mouse.press(ms.Button.left)
        #mouse.release(ms.Button.left)
        #mouse.click(ms.Button.left, 1)
        mouse.click(ms.Button.left, 2)

    # [KEYBOARD| replay typing]:
    if action._state == 'keyboard':
        print('Replay typing')

    # [KEY| Special Keys]:
    if action._state == 'key':
        print('Using special key')

    # [PASS| Enter password]:
    if action._state == 'pass':
        print('Entering Password')

    # [BOX| SSIM?]:
    if action._state == 'box':
        print('SSIM?')
        _start_x = action._coords_list[0].get('x')
        _start_y = action._coords_list[0].get('y')
        _stop_x = action._coords_list[1].get('x')
        _stop_y = action._coords_list[1].get('y')

    sys.exit(1)


def move_to(int_x, int_y):
    mouse = ms.Controller()

    (x, y) = mouse.position
    _x = int(x)
    _y = int(y)

    while True:
        if (_x == int_x) and (_y == int_y):
            print('ARRIVED!')
            break

        # [Mod X]:
        if _x > int_x:
            _x-=1
        if _x < int_x:
            _x+=1

        # [Mod Y]:
        if _y > int_y:
            _y-=1
        if _y < int_y:
            _y+=1

        mouse.position = (_x, _y)


# https://pynput.readthedocs.io/en/latest
# [0]: Playback Sequence of actions
#  ^ (Merge listeners into 1 class / Merge controllers into 1 class [Shared Class?])
# [1]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
# [2]: (use BOX coords for SSIM checking)
if __name__ == "__main__":
    '''
    # [non-blocking keyboard listener]:
    listener = kb.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # [non-blocking mouse listener]:
    listener = ms.Listener(on_click=on_click, on_move=on_move)
    listener.start()

    print('[Mouse listening for clicks! Press CTRL to stop.]')
    while _mouse_record:
        time.sleep(1)
    print('[fin.]')

    for _action in action_items:
        _action.print_info()
    '''

    #print('[Starting Replay]: 3sec')
    #time.sleep(3)

    move_to(100,100)

    '''
    # [Steps to log in]: (Previously Recorded)
    action_items.append(action('pos', [{'x': 1859, 'y': 230}]))
    action_items.append(action('pos', [{'x': 1147, 'y': 266}]))
    action_items.append(action('keyboard', [{'x': 1147, 'y': 266}], 'staging.uservices.com'))
    action_items.append(action('key', [{'x': 1147, 'y': 266}], 'Key.enter'))
    action_items.append(action('pos', [{'x': 718, 'y': 363}]))
    action_items.append(action('keyboard', [{'x': 718, 'y': 363}], 'jholloway'))
    action_items.append(action('key', [{'x': 718, 'y': 363}], 'Key.tab'))
    action_items.append(action('pass', [{'x': 735, 'y': 393}], 'Meowth73'))
    action_items.append(action('pos', [{'x': 561, 'y': 456}]))
    

    # [action_items list for replay]:
    for _action in action_items:
        action_replay(_action)
    '''

    '''
    action_items = []
    action_items.append(action('pos', {'x': 3, 'y': 3}))
    action_items.append(action('pos', [{'x': 7, 'y': 7}]))
    action_items.append(action('box', [{'x': 0, 'y': 0}, {'x': 10, 'y': 10}]))
    '''