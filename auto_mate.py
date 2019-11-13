import os
import sys
import time
import json
import threading
import pyautogui
import contextlib
import pynput.mouse as ms
import pynput.keyboard as kb
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Controller

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# [OSX restricts certain actions to root, pynput cant access without sudo]:
if sys.platform == 'darwin':
    if os.getuid() != 0:
        print('[If you are using OSX, please run as root: `sudo python3 auto_mate.py`]')
        sys.exit(1)

# [GLOBALS]:
_record = 1
# _record = 0 | off
# _record = 1 | on (Both)
# _record = 2 | on (Mouse only)
# _record = 3 | on (Keyboard only)
# ^(Soft-set.. Should turn on both Listeners and only act on actions if _record set)

#class omni_listener():

# [MOUSE GLOBALS]:
_click_int_x = None
_click_int_y = None

# [KEYBOARD GLOBALS]:
_typed_last = 0
_keyboard_buffer = ''
_hold_ALT = False
_hold_TAB = False
_hold_CMD = False
_hold_CTRL = False
_hold_SHIFT = False
_CMD_input = False

def on_press(key):
    global _record, _typed_last, _keyboard_buffer, _click_int_x, _click_int_y, _hold_SHIFT, _hold_ALT, _hold_TAB, _hold_CTRL, _hold_CMD, _CMD_input

    if _record > 0:
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

            _pass_thru = False

            # HANDLE_SPECIAL_KEYS()

            # [If SHIFT is pressed]:
            if key == kb.Key.shift:
                _hold_SHIFT = True

            # [if backspace, pop last character from buffer]:
            if key == kb.Key.backspace:
                if len(_keyboard_buffer) > 0:
                    _keyboard_buffer = _keyboard_buffer[:-1]
                else: # [Otherwise add as special character for replay?]:
                    _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
                    stage.append(_act)

            # [Add space for spacebar xD]:
            if key == kb.Key.space:
                _keyboard_buffer+=' '

            # [If ALT key pressed]:
            if key == kb.Key.alt:
                _hold_ALT = True

            # [If CMD key pressed]:
            if key == kb.Key.cmd:
                _hold_CMD = True

            # [If TAB key pressed]:
            if key == kb.Key.tab:
                _hold_TAB = True
                check_keyboard_buffer(interrupt=True)

                _hold_ALT_CMD = False
                if sys.platform == 'darwin':
                    _hold_ALT_CMD = _hold_CMD
                else:
                    _hold_ALT_CMD = _hold_ALT

                # [Ignore alt-tab]: (?)
                if _hold_ALT_CMD:
                    pass
                else: # [Add TAB key]:
                    _pass_thru = True

            # [If CTRL key pressed]:
            if key == kb.Key.ctrl:
                _hold_CTRL = True
                _record = 0
                print('[Listeners "stopped"]')

            # [If ENTER key pressed]:
            if key == kb.Key.enter:
                _pass_thru = True
            
            # [If ARROW key pressed]:
            if key == kb.Key.up:
                _pass_thru = True
            if key == kb.Key.down:
                _pass_thru = True
            if key == kb.Key.left:
                _pass_thru = True
            if key == kb.Key.right:
                _pass_thru = True


            if _pass_thru:
                check_keyboard_buffer(interrupt=True)
                _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
                stage.append(_act)

            CHECK_KEYBOARD_EMERGENCY(_hold_CTRL, _hold_SHIFT)

def on_release(key):
    global _record, _hold_SHIFT, _hold_ALT, _hold_TAB, _hold_CTRL

    if _record > 0:
        if key == kb.Key.alt:
            _hold_ALT = False

        if key == kb.Key.tab:
            _hold_TAB = False

        if key == kb.Key.shift:
            _hold_SHIFT = False

        if key == kb.Key.ctrl:
            _hold_CTRL = False

        if key == kb.Key.cmd:
            _hold_CMD = False

def check_keyboard_buffer(interrupt=False):
    global _typed_last, _keyboard_buffer, _click_int_x, _click_int_y

    if interrupt==True or ((_typed_last > 0) and (time.time() - _typed_last) >= 2):
        if _keyboard_buffer != '':
            # [Action for Keyboard takes x,y of last click and keyboard_buffer]:
            _act = action('keyboard', {'x': _click_int_x, 'y': _click_int_y}, _keyboard_buffer)
            stage.append(_act)

        _keyboard_buffer=''
        _typed_last=0

def on_click(x, y, button, pressed):
    global _record, _click_int_x, _click_int_y, _hold_SHIFT, _CMD_input
    _int_x = int(x)
    _int_y = int(y)

    if _record > 0:
        check_keyboard_buffer(interrupt=True)

        if pressed:
            _click_int_x = int(x)
            _click_int_y = int(y)
        else: # [RELEASED]:
            # [Turn off CMD_input after click]:
            if _CMD_input:
                _CMD_input = False
                return

            # [SHIFT held while clicking | Enter Password]:
            if _hold_SHIFT:
                _CMD_input = True
                _pass = input('Enter password here: ')
                _act = action('pass', {'x': _click_int_x, 'y': _click_int_y}, _pass)
                stage.append(_act)

                print('Click field to resume! / Please use Submit instead of Enter')
                return

            # [SAME = POS | DIFF = BOX]:
            if abs(_int_x-_click_int_x) < 5 and abs(_int_y-_click_int_y) < 5:
                _act = action('click', [{'x': _int_x, 'y': _int_y}])
                stage.append(_act)
            else:
                _act = action('box', [{'x': _click_int_x, 'y': _click_int_y}, {'x': _int_x, 'y': _int_y}])
                stage.append(_act)

def on_move(x, y):
    global _record
    _int_x = int(x)
    _int_y = int(y)

    CHECK_MOUSE_EMERGENCY(_int_x, _int_y)

    if _record > 0:
        check_keyboard_buffer()
        # ^(Flush keyboard buffer)

# [Mouse position at 0,0 is emergency exit condition]:
def CHECK_MOUSE_EMERGENCY(_int_x, _int_y):
    if _int_x == 0 and _int_y == 0:
        print('[MOUSE_PANIC_EXIT]')
        os._exit(1)

# [SHIFT+CTRL is emergency exit condition]:
def CHECK_KEYBOARD_EMERGENCY(_hold_CTRL, _hold_SHIFT):
    if _hold_CTRL and _hold_SHIFT:
        print('[KEYBOARD_PANIC_EXIT]')
        os._exit(1)

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


class action:
    _id = 0
    _state = None
    _action_id = 0
    _coords_list = None
    _keyboard_buffer = None

    # Check if coords_list is actually a list?
    def __init__(self, state=None, coords_list=None, keyboard_buffer=None):
        self._state = state
        self._action_id = action._id
        self._coords_list = coords_list
        self._keyboard_buffer = keyboard_buffer

        # [If coords weren't sent as list, add as list]:
        if coords_list and type(coords_list)!=list:
            self._coords_list = [coords_list]

        self._print('Added')

        # [Class ID incremetor]:
        action._id+=1

    # [Serializer]:
    def _JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    # [Pretty Print actions]:
    def _print(self, act):
        for _coord in self._coords_list:
            if self._keyboard_buffer is None or self._state == 'pass':
                print('{0} action{1}({2}): {3}'.format(act, self._action_id, self._state, _coord))
            else:
                print('{0} action{1}({2}): {3} | {4}'.format(act, self._action_id, self._state, _coord, self._keyboard_buffer))


# [Iterator class]:
class action_iterator:
    _index = None
    _stage = None

    def __init__(self, stage):
        self._index = 0
        self._stage = stage

    def __next__(self):
        if self._index < len(self._stage._action_items): # Check if action_items are fully iterated or not
            result = self._stage._action_items[self._index]

            self._index +=1
            return result

        raise StopIteration

# [Stage Manager to organize actions]:
class stage_manager:
    _kb_ctrl = None
    _ms_ctrl = None
    _action_items = None

    def __init__(self):
        self._kb_ctrl = kb.Controller()
        self._ms_ctrl = ms.Controller()
        self._action_items = []

    def __iter__(self):
        return action_iterator(self)

    def append(self, action):
        self._action_items.append(action)

    def _replay(self, action):
        action._print('Replay')

        # [CLICK| Click Position]: 
        # ^(Need to check click/double-click for replay)
        if action._state == 'click':
            _x = action._coords_list[0].get('x')
            _y = action._coords_list[0].get('y')
            pyautogui.moveTo(_x, _y, duration=1)
            self._ms_ctrl.click(Button.left, 1) # pyautogui wont change active window (OSX)

        # [KEYBOARD| replay typing]:
        if action._state == 'keyboard':
            pyautogui.typewrite(action._keyboard_buffer, interval=.1)

        # [KEY| Special Keys]:
        if action._state == 'key':
            self._kb_ctrl.press(action._keyboard_buffer)
            self._kb_ctrl.release(action._keyboard_buffer)
            time.sleep(.1)

        # [PASS| Enter password]:
        if action._state == 'pass':
            # [Move mouse && click on _x, _y]: (?)
            _x = action._coords_list[0].get('x')
            _y = action._coords_list[0].get('y')
            pyautogui.click(x=_x, y=_y, button='left', clicks=1)

            pyautogui.typewrite(action._keyboard_buffer, interval=.1)

        # [BOX| SSIM?]:
        if action._state == 'box':
            print('SSIM?')
            _start_x = action._coords_list[0].get('x')
            _start_y = action._coords_list[0].get('y')
            _stop_x = action._coords_list[1].get('x')
            _stop_y = action._coords_list[1].get('y')
            _diff_x = (_stop_x - _start_x)
            _diff_y = (_stop_y - _start_y)

            # [Draw box coords specified]:
            pyautogui.moveTo(_start_x, _start_y, duration=1)
            pyautogui.moveTo((_start_x+_diff_x),_start_y, duration=1)
            pyautogui.moveTo((_start_x+_diff_x),(_start_y+_diff_y), duration=1)
            pyautogui.moveTo(_start_x,(_start_y+_diff_y), duration=1)
            pyautogui.moveTo(_start_x,_start_y, duration=1)

        # [1sec pause]:
        time.sleep(1)


# [0]: Need a way so save python class objects (actions)
# [1]: (Merge listeners into 1 class / Merge controllers into 1 class)
# [2]: (use BOX coords for SSIM checking)
# [3]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
# https://pyautogui.readthedocs.io/en/latest/cheatsheet.html
# https://pythonhosted.org/pynput/mouse.html#controlling-the-mouse
# https://pythonhosted.org/pynput/keyboard.html#controlling-the-keyboard
if __name__ == "__main__":
    # [GLOBALS]:
    stage = stage_manager()
    mouse_listener = ms.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener = kb.Listener(on_press=on_press, on_release=on_release)
    # ^(non-blocking mouse/keyboard listener)

    with mouse_listener, keyboard_listener:
        print('[Mouse/Keyboard listening! Press CTRL to stop recording]')
        while _record > 0:
            time.sleep(1) #pass

        #-------
        print('[Starting Replay]: 3sec')
        time.sleep(3)
        #-------

         # [Replay Actions]:
        if _record == 0:
            _again = True
            while _again:
                for action in stage:
                    stage._replay(action)

                #_again = False # Turn off Replay Again
                if _again:
                    _again = input('[Do you wish to Replay again?]:')
                    _again = False if (_again.lower() == 'n' or _again.lower() == 'no') else True

        print('[fin.]')