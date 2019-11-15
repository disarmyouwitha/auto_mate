import os
import sys
import time
import json
import glob
import shutil
import imageio
import threading
import pyautogui
import contextlib
import screen_pixel
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
        os._exit(1)

# [GLOBALS]:
_record = 1
_kb_ctrl = None
_ms_ctrl = None

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
                    act = action(state='key', coords_list={'x': _click_int_x, 'y': _click_int_y}, keyboard_buffer=key)
                    stage.append(act)

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
                act = action(state='key', coords_list={'x': _click_int_x, 'y': _click_int_y}, keyboard_buffer=key)
                stage.append(act)

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
            act = action(state='keyboard', coords_list={'x': _click_int_x, 'y': _click_int_y}, keyboard_buffer=_keyboard_buffer)
            stage.append(act)

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
                act = action(state='pass', coords_list={'x': _click_int_x, 'y': _click_int_y}, keyboard_buffer=_pass)
                stage.append(act)

                print('Click field to resume! / Please use Submit instead of Enter')
                return

            # [SAME = CLICK | DIFF = BOX]:
            if abs(_int_x-_click_int_x) < 5 and abs(_int_y-_click_int_y) < 5:
                act = action(state='click', coords_list=[{'x': _int_x, 'y': _int_y}])
                stage.append(act)
            else:
                act = action(state='box', coords_list=[{'x': _click_int_x, 'y': _click_int_y}, {'x': _int_x, 'y': _int_y}])
                act._set_ssim()
                stage.append(act)

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
    _ssim_filename = None
    _ssim_score = None

    # [Initializer from scratch]:
    def __init__(self, state=None, coords_list=None, keyboard_buffer=None, JSON_STR=None):
        if JSON_STR is None:
            self._state = state
            self._action_id = action._id
            self._coords_list = coords_list
            self._keyboard_buffer = str(keyboard_buffer)

            # [If coords weren't sent as list, add as list]:
            if coords_list and type(coords_list)!=list:
                self._coords_list = [coords_list]

            # [Class ID incremetor]:
            action._id+=1

            # [If BOX try to Capture screenshot from coords]: (for SSIM)
            if self._state == 'box':
                _ssim_control = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=2)
                
                self._ssim_filename = '{0}_action{1}.png'.format(('SEQ' if stage._file_name is None else stage._file_name[:-5]), self._action_id)
                imageio.imwrite(self._ssim_filename, _ssim_control)

            self._PRINT('Added')
        else:
            # [Should only ever be 1 key, but whatever]:
            for key in JSON_STR.keys():
                JSON_DATA = json.loads(JSON_STR[key])
                self._state = JSON_DATA.get('_state')
                self._action_id = JSON_DATA.get('_action_id')
                self._coords_list = JSON_DATA.get('_coords_list')
                self._keyboard_buffer = JSON_DATA.get('_keyboard_buffer')
                self._ssim_filename = JSON_DATA.get('_ssim_filename')
                self._PRINT('Loaded')

    def _set_ssim(self):
        control = imageio.imread(self._ssim_filename)
        test = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=2)
        self._ssim_score  = stage._sp.check_ssim(control, test)

    def _check_ssim(self, thresh=.9):
        control = imageio.imread(self._ssim_filename)
        test = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=2)
        imageio.imwrite('{0}_action{1}.png'.format('TEST', self._action_id), test)
        ssim_score = stage._sp.check_ssim(control, test)
        print("SAVED_SSIM: {}".format(self._ssim_score))
        return True if (ssim_score > thresh) else False

    def _RUN(self):
        self._PRINT('Replay')

        # [CLICK| Click Position]: 
        # ^(Need to check click/double-click for replay)
        if self._state == 'click':
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')
            pyautogui.moveTo(_x, _y, duration=1)
            _ms_ctrl.click(Button.left, 1) # pyautogui wont change active window (OSX)

        # [KEYBOARD| replay typing]:
        if self._state == 'keyboard':
            pyautogui.typewrite(self._keyboard_buffer, interval=.1)

        # [KEY| Special Keys]:
        if self._state == 'key':
            _kb_ctrl.press(stage.str_to_key(self._keyboard_buffer))
            _kb_ctrl.release(stage.str_to_key(self._keyboard_buffer))
            time.sleep(.1)

        # [PASS| Enter password]:
        if self._state == 'pass':
            # [Move mouse && click on _x, _y]: (?)
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')
            pyautogui.click(x=_x, y=_y, button='left', clicks=1)

            pyautogui.typewrite(self._keyboard_buffer, interval=.1)

        # [BOX| CHECK SSIM]:
        if self._state == 'box':
            if self._check_ssim(thresh=.9):
                print('[passed]')
            else:
                print('[failed]')

            # [Draw box coords specified]:
            _start_x = self._coords_list[0].get('x')
            _start_y = self._coords_list[0].get('y')
            _stop_x = self._coords_list[1].get('x')
            _stop_y = self._coords_list[1].get('y')
            _diff_x = (_stop_x - _start_x)
            _diff_y = (_stop_y - _start_y)

            pyautogui.moveTo(_start_x, _start_y, duration=1)
            pyautogui.moveTo((_start_x+_diff_x),_start_y, duration=1)
            pyautogui.moveTo((_start_x+_diff_x),(_start_y+_diff_y), duration=1)
            pyautogui.moveTo(_start_x,(_start_y+_diff_y), duration=1)
            pyautogui.moveTo(_start_x,_start_y, duration=1)

        # [1sec pause]:
        time.sleep(1)

    # [Serializer]:
    def _JSON(self):
        _json_dump = json.dumps(self, default=lambda o: o.__dict__)
        return {'action{0}'.format(self._action_id): _json_dump}

    # [Pretty Print actions]:
    def _PRINT(self, act):
        for _coord in self._coords_list:
            if self._keyboard_buffer is None or self._state == 'pass':
                print('{0} action{1}({2}): {3}'.format(act, self._action_id, self._state, _coord))
            else:
                if self._ssim_score is not None:
                    print('{0} action{1}({2}): {3} | {4} | {5}'.format(act, self._action_id, self._state, _coord, self._keyboard_buffer, self._ssim_score))
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
        if self._index < len(self._stage._action_items):
            result = self._stage._action_items[self._index]

            self._index +=1
            return result

        raise StopIteration


# [Stage Manager to organize actions]:
class stage_manager:
    _sp = None
    _file_name = None
    _action_items = None

    def __init__(self, file_name):
        self._action_items = []
        self._file_name = file_name
        self._sp = screen_pixel.screen_pixel()

    def __iter__(self):
        return action_iterator(self)

    def append(self, action):
        self._action_items.append(action)

    def str_to_key(self, str):
        (_class, _key) = str.split('.') 
        return getattr(sys.modules[__name__], _class)[_key]

    def save_sequence(self, file_name=None):
        _json_seq = {}

        if file_name is None:
            file_name = input('What would you like the filename to be?: ')

        self._file_name = file_name

        for act in self:
            # [Rename SEQ_action0.png to use file_name]
            if act._state == 'box':
                _file_mask = '{0}_action{1}.png'.format(self._file_name[:-5], act._action_id)
                shutil.move(act._ssim_filename, _file_mask)
                act._ssim_filename = _file_mask

            # [Update json_data]:
            _json_seq.update(act._JSON())


        print('[Saving sequence for replay]: {0}'.format(file_name))
        with open(file_name, 'w+') as fp:
            json.dump(_json_seq, fp)

    def load_sequence(self, file_name=None):
        self._action_items = []

        if file_name is None:
            file_name = input('What file would you like to replay?: ')

        print('[Loading replay file]: {0}'.format(file_name))
        with open(file_name) as _json_seq:
            sequence = json.load(_json_seq)

        for _json_act in sequence:
            act = action(JSON_STR={_json_act: sequence[_json_act]})
            self._action_items.append(act)

    def replay_sequence(self):
        print('[Replaying sequence]')
        for act in self._action_items:
            act._RUN()

    def replay_loop_check(self):
        # [See if user wants to continue loop]:
        _again = 1
        while _again > 0:
            _again-=1
            if _again==0:
                _again = input('[Do you wish to Replay again?] (N for no, # for loop): ')
                if _again.isalpha() or _again=='':
                    _again = 0 if (_again.lower() == 'n' or _again.lower() == 'no') else 1
                else:
                    _again = int(_again)

            if _again > 0:
                self.replay_sequence()


# https://pythonhosted.org/pynput/
# https://pyautogui.readthedocs.io/en/latest/cheatsheet.html
# [0]: (Merge listeners into 1 class / Merge controllers into 1 class)
# [1]: Ability to capture Replay of actions (going through form) and (rather than using captured keystrokes) pass in data for replay
#  >>> Click URL bar, pass in: https://www.websitedimensions.com/pixel/
# [2]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
if __name__ == "__main__":
    # [Check command line arguments for mode]:
    try:
        _mode = sys.argv[1]
        accepted_modes = ['record','replay']
        if _mode not in accepted_modes:
            print('Syntax: python3 auto_mate.py record | python3 auto_mate.py replay filename.json')
            os._exit(1)
    except:
        _mode = 'record'

    # [Check command line arguments for file_name]:
    try:
        _file_name = sys.argv[2]
    except:
        _file_name = None

    # [GLOBALS]:
    _kb_ctrl = kb.Controller()
    _ms_ctrl = ms.Controller()
    stage = stage_manager(_file_name)
    mouse_listener = ms.Listener(on_click=on_click, on_move=on_move)
    keyboard_listener = kb.Listener(on_press=on_press, on_release=on_release)
    # ^(non-blocking mouse/keyboard listener)

    # [Replay from file]:
    if 'replay' in _mode:
        if stage._file_name and '.json' in stage._file_name:
            stage.load_sequence(stage._file_name)
            stage.replay_sequence()
            stage.replay_loop_check()
        else:
            print('[Syntax: `python3 auto_mate.py replay filename.json`]')
            os._exit(1)

    if 'record' in _mode:
        with mouse_listener, keyboard_listener:
            # [Recording loop]:
            print('[Mouse/Keyboard listening! Press CTRL to stop recording]')
            while _record > 0:
                time.sleep(1) #pass (?)

            print('[Starting Replay]: 2sec')
            time.sleep(2)

            # [Replay Actions]:
            stage.replay_sequence()

            # [Saving sequence to JSON file for replay]:
            if stage._file_name is None:
                _file_name = input('[Do you wish to save replay?] (`filename.json` for yes): ')

            if _file_name != '':
                stage.save_sequence(_file_name)
            else:
                # [Cleanup unsaved files]:
                shutil.remove('SEQ_*.png')

            stage.replay_loop_check()

    print('[fin.]')
