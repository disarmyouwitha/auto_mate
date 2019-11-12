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
#class omni_controller():

# [OSX restricts certain actions to root, pynput cant access without sudo]:
if sys.platform == 'darwin':
    if os.getuid() != 0:
        print('[If you are using OSX, please run as root: `sudo python3 auto_mate.py`]')
        sys.exit(1)

# [GLOBALS]:
action_items = []
_record = 1
# _record = 0 | off
# _record = 1 | on (Both)
# _record = 2 | on (Mouse only)
# _record = 3 | on (Keyboard only)

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
                    action_items.append(_act)

            # [Add space for spacebar xD]:
            if key == kb.Key.space:
                _keyboard_buffer+=' '

            # [If ALT is pressed]:
            if key == kb.Key.alt:
                _hold_ALT = True

            # [If CMD is pressed]:
            if key == kb.Key.cmd:
                _hold_CMD = True

            # [If TAB is pressed]:
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
                    _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
                    action_items.append(_act)

            # [If ENTER is pressed]:
            if key == kb.Key.enter:
                check_keyboard_buffer(interrupt=True)
                _act = action('key', {'x': _click_int_x, 'y': _click_int_y}, key)
                action_items.append(_act)

            # [If CTRL is pressed]:
            if key == kb.Key.ctrl:
                _hold_CTRL = True
                _record = 0
                print('[Listeners "stopped"]')

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
            action_items.append(_act)

        _keyboard_buffer=''
        _typed_last=0

def on_click(x, y, button, pressed):
    global _record, _click_int_x, _click_int_y, _hold_SHIFT, _CMD_input
    _int_x = int(x)
    _int_y = int(y)

    if _record > 0:
        check_keyboard_buffer()

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


class action():
    _id = 0
    _state = None
    _action_id = 0
    _coords_list = None
    _ms_controller = None
    _kb_controller = None
    _keyboard_buffer = None

    # Check if coords_list is actually a list?
    def __init__(self, state=None, coords_list=None, keyboard_buffer=None):
        self._state = state
        self._action_id = action._id
        self._coords_list = coords_list
        self._keyboard_buffer = keyboard_buffer

        self._ms_ctrl = ms.Controller()
        self._kb_ctrl = kb.Controller()

        # [If coords weren't sent as list, add as list]:
        if coords_list and type(coords_list)!=list:
            self._coords_list = [coords_list]

        self.print_info('Added')

        # [Class ID incremetor]:
        action._id+=1

    def replay(self):
        self.print_info('Replay')

        # [POS| Click Position]: # Need to check click/double-click for replay
        if self._state == 'pos':
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')

            # [Set pointer position]:
            self.move_to(_x, _y)

            # [Press and release]:
            self._ms_ctrl.click(ms.Button.left, 1)
            #self._ms_ctrl.click(ms.Button.left, 2) # Need to check click/double-click for replay

        # [KEYBOARD| replay typing]:
        if self._state == 'keyboard':
            self._kb_ctrl.type(self._keyboard_buffer)

        # [KEY| Special Keys]:
        if self._state == 'key':
            self._kb_ctrl.press(self._keyboard_buffer)
            self._kb_ctrl.release(self._keyboard_buffer)

        # [PASS| Enter password]:
        if self._state == 'pass':
            # Move mouse && click on _x, _y?
            self._kb_ctrl.type(self._keyboard_buffer)

        # [BOX| SSIM?]:
        if self._state == 'box':
            print('SSIM?')
            _start_x = self._coords_list[0].get('x')
            _start_y = self._coords_list[0].get('y')
            _stop_x = self._coords_list[1].get('x')
            _stop_y = self._coords_list[1].get('y')
            # ..draw_rect()...

        # [2sec pause]:
        time.sleep(2)

    # [Moved into `actions` class.. Needs to be moved into `omni_controller` which is brought up by action: self._omni_ctrl]
    def move_to(self, int_x, int_y):
        (x, y) = self._ms_ctrl.position
        _x = int(x)
        _y = int(y)

        while True:
            if (_x == int_x) and (_y == int_y):
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

            self._ms_ctrl.position = (_x, _y)

    # [Pretty Print actions]:
    def print_info(self, act):
        for _coord in self._coords_list:
            if self._keyboard_buffer is None:
                print('{0} action{1}({2}): {3}'.format(act, self._action_id, self._state, _coord))
            else:
                print('{0} action{1}({2}): {3} | {4}'.format(act, self._action_id, self._state, _coord, self._keyboard_buffer))


# https://pynput.readthedocs.io/en/latest
# [0]: action_replay becomes Action->replay()
# [1]: (Merge listeners into 1 class / Merge controllers into 1 class [Shared Class?])
# [2]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
# [3]: (use BOX coords for SSIM checking)
if __name__ == "__main__":
    # [Record Actions]:
    if _record > 0:
        if _record == 1 or _record == 2:
            # [non-blocking mouse listener]:
            mouse_listener = ms.Listener(on_click=on_click, on_move=on_move)
            mouse_listener.start()

        if _record == 1 or _record == 3:
            # [non-blocking keyboard listener]:
            keyboard_listener = kb.Listener(on_press=on_press, on_release=on_release)
            keyboard_listener.start()

        print('[Mouse listening for clicks! Press CTRL to stop.]')
        while _record > 0:
            time.sleep(1)
        print('[Exiting listening loop!]')

    #-------
    print('[Starting Replay]: 3sec')
    time.sleep(3)
    #-------

    # [Replay Actions]:
    if _record == 0:
        for _action in action_items:
            _action.replay()

    print('[fin.]')
    mouse_listener.stop()
    keyboard_listener.stop()

