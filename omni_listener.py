import os
import sys
import time
from action import action
import pynput.mouse as ms
import pynput.keyboard as kb
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Controller

class omni_listener():
    # [CONTROLLERS]:
    _stage = None
    _ms_ctrl = None # (Because pyautogui can't click to a not active window)
    _kb_ctrl = None # (Might replace with pyautogui keyUp/keyDown so we don't have to load this controller.. need to check support on osx/win)

    # [MOUSE GLOBALS]:
    _last_click = 0
    _last_int_x = None
    _last_int_y = None

    # [KEYBOARD GLOBALS]:
    _last_typed = 0
    _hold_ESC = False
    _hold_ALT = False
    _hold_TAB = False
    _hold_CMD = False
    _hold_CTRL = False
    _hold_SHIFT = False
    _PASS_input = False
    _keyboard_buffer = ''
    _keyboard_buffer

    def __init__(self, stage=None):
        self._stage = stage
        self._kb_ctrl = kb.Controller()
        self._ms_ctrl = ms.Controller()

        self.mouse_listener = ms.Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
        self.keyboard_listener = kb.Listener(on_press=self.on_press, on_release=self.on_release)
        # ^(non-blocking mouse/keyboard listener)

    # [Mouse position at 0,0 is emergency exit condition]:
    def CHECK_MOUSE_EMERGENCY(self, _int_x, _int_y):
        if _int_x == 0 and _int_y == 0:
            print('[MOUSE_PANIC_EXIT]')
            os._exit(1)

    def CLICK(self, which_click='left', num_clicks=1, type_click='click'):
        if type_click=='click':
            if which_click == 'right-click':
                self._ms_ctrl.click(ms.Button.right, num_clicks)
            else:
                self._ms_ctrl.click(ms.Button.left, num_clicks)
        elif type_click=='press':
            if which_click == 'right-click':
                self._ms_ctrl.press(ms.Button.right)
            else:
                self._ms_ctrl.press(ms.Button.left)
        elif type_click=='release':
            if which_click == 'right-click':
                self._ms_ctrl.release(ms.Button.right)
            else:
                self._ms_ctrl.release(ms.Button.left)

    def PRESS(self, key):
        self._kb_ctrl.press(key)
        self._handle_special_press(key)

    def RELEASE(self, key):
        self._kb_ctrl.release(key)
        self._handle_special_release(key)

    # [Takes action._keyboard_buffer with delimited Key values]: (Key.tab|Key.cmd|3)
    def _str_to_key(self, _str):
        _str_split = _str.split('|')
        _key_list = []
        for key in _str_split:
            try:
                _pressed = int(key)
            except:
                (_class, _key) = key.split('.')
                _key_ = getattr(sys.modules[__name__], _class)[_key]
                _key_list.append(_key_)

        return (_key_list, _pressed)

    # [NEEDS helper function]: # _handle_special_keys()
    def on_press(self, key):
        if self._stage._record > 0:
            # [CMD_input for passwords, etc]:
            if self._PASS_input:
                return

            # [Check keyboard buffer]:
            self._check_keyboard_buffer()

            try:
                _key = key.char
                self._keyboard_buffer+=key.char
                self._last_typed = time.time()

                # [If _held_keys treat as char in sequence]:
                _held_keys = self._held_keys()
                _held_cnt = len(_held_keys)
                if _held_cnt >= 2:
                    self._check_keyboard_buffer(interrupt=True)

            except AttributeError: 
                #print('special key {0} pressed'.format(key))
                # ^DEBUGG

                self._last_typed = 0 #time.time()

                # [if backspace, pop last character from buffer]:
                if key == kb.Key.backspace:
                    if len(self._keyboard_buffer) > 0:
                        self._keyboard_buffer = self._keyboard_buffer[:-1]
                    else: # [Otherwise add as special character for replay?]:
                        act = action(state='key', coords_list={'x': self._last_int_x, 'y': self._last_int_y}, keyboard_buffer='{0}|1'.format(key), stage=self._stage)
                        self._stage._append(act)

                # [Add space for spacebar xD]:
                if key == kb.Key.space:
                    self._keyboard_buffer+=' '

                # [If ESC key pressed]:
                if key == kb.Key.esc:
                    self._hold_ESC = True
                    self._stage._record = 0
                    print('[Listeners "stopped"]')

                self._handle_special_press(key)

    def _handle_special_press(self, key):
        _pass_thru = False

        # [If ALT key pressed]: (Don't accept HELD tab as multiple presses)
        if key == kb.Key.alt:
            if self._hold_ALT == False:
                self._hold_ALT = True
                _pass_thru = True

        # [If CMD key pressed]: (Don't accept HELD tab as multiple presses)
        if key == kb.Key.cmd:
            if self._hold_CMD == False:
                self._hold_CMD = True
                _pass_thru = True

        # [If SHIFT is pressed]: (Don't accept HELD tab as multiple presses)
        if key == kb.Key.shift:
            if self._hold_SHIFT == False:
                self._hold_SHIFT = True
                _pass_thru = True

        # [If CTRL key pressed]: (Don't accept HELD tab as multiple presses)
        if key == kb.Key.ctrl:
            if self._hold_CTRL == False:
                self._hold_CTRL = True
                _pass_thru = True

        # [If ENTER key pressed]: (ENTER will reset _keyboard_buffer)
        if key == kb.Key.enter:
            self._check_keyboard_buffer(interrupt=True)
            _pass_thru = True

        # [If TAB key pressed]: (ENTER will reset _keyboard_buffer)
        if key == kb.Key.tab:
            if self._hold_TAB == False:
                self._hold_TAB = True
                _pass_thru = True
                self._check_keyboard_buffer(interrupt=True)

        # [If ARROW key pressed]: (Held keys?)
        if key == kb.Key.up:
            _pass_thru = True
        if key == kb.Key.down:
            _pass_thru = True
        if key == kb.Key.left:
            _pass_thru = True
        if key == kb.Key.right:
            _pass_thru = True

        # [Add pressed key to action list]:
        if self._stage._record > 0 and _pass_thru:
            # [If _keyboard_buffer is empty (user is not typing) add Key action]:
            if len(self._keyboard_buffer) == 0:
                _held_keys = self._held_keys()
                _held_cnt = len(_held_keys)

                # [Remove self from _held_keys]:
                if key in _held_keys:
                    _held_keys.remove(key)

                # [Determine how key should be replayed]:
                if _held_cnt<=1:
                    key_pressed = '{0}|{1}'.format(key, 1)
                else:
                    key_pressed = ''
                    key_pressed+= '{0}|'.format(key)
                    for _key in _held_keys:
                        key_pressed+= '{0}|'.format(_key)
                    key_pressed = '{0}|{1}'.format(key_pressed[:-1], 3)

                # [Check if key combination was pressed, send that instead]:
                act = action(state='key', coords_list={'x': None, 'y': None}, keyboard_buffer=key_pressed, stage=self._stage)
                self._stage._append(act)

    # [Check HELD status of keys]:
    def _held_keys(self):
        _key_list = []

        if self._hold_ESC:
            _key_list.append(kb.Key.esc)
        if self._hold_ALT:
            _key_list.append(kb.Key.alt)
        if self._hold_TAB:
            _key_list.append(kb.Key.tab)
        if self._hold_CMD:
            _key_list.append(kb.Key.cmd)
        if self._hold_CTRL:
            _key_list.append(kb.Key.ctrl)
        if self._hold_SHIFT:
            _key_list.append(kb.Key.shift)

        return _key_list 

    def on_release(self, key):
        if self._stage._record > 0:
            self._check_keyboard_buffer()
            self._handle_special_release(key)

    # [Special conditions on release]:
    def _handle_special_release(self, key):
        # [Ignore kb.KeyCode]:
        if type(key) == kb.Key:
            if key == kb.Key.alt:
                self._hold_ALT = False
            if key == kb.Key.tab:
                self._hold_TAB = False
            if key == kb.Key.shift:
                self._hold_SHIFT = False
            if key == kb.Key.ctrl:
                self._hold_CTRL = False
            if key == kb.Key.esc:
                self._hold_ESC = False
            if key == kb.Key.cmd:
                self._hold_CMD = False

            # [Add released key to action list]: (if recording)
            if self._stage._record > 0:
                # [If _keyboard_buffer is empty (user is not typing) add Key action]:
                if len(self._keyboard_buffer) == 0:

                    # [Try to determine if release key should be added, or key upgraded from press to tap]:
                    _prev_act = self._stage._peek()
                    (_prev_key_list, _prev_pressed) = self._str_to_key(_prev_act._keyboard_buffer)

                    _same_key = False
                    if key == _prev_key_list[0]:
                        _same_key = True

                    key_pressed = None
                    if _prev_pressed == 1:
                        if _same_key: 
                            key_pressed = '{0}|3'.format(_prev_act._keyboard_buffer[:-2])
                        else:
                            key_pressed = '{0}|0'.format(key)
                    elif _prev_pressed == 3:
                        if _same_key:
                            key_pressed = None
                        else:
                            key_pressed = '{0}|0'.format(key)

                    if key_pressed:
                        act = action(state='key', coords_list={'x': None, 'y': None}, keyboard_buffer=key_pressed, stage=self._stage)
                        self._stage._append(act)

    def _check_keyboard_buffer(self, interrupt=False):
        if interrupt==True or ((self._last_typed > 0) and (time.time() - self._last_typed) >= 2):
            if self._keyboard_buffer != '':
                # [Action for Keyboard takes x,y of last click and keyboard_buffer]:
                act = action(state='keyboard', coords_list={'x': self._last_int_x, 'y': self._last_int_y}, keyboard_buffer=self._keyboard_buffer, stage=self._stage)
                self._stage._append(act)

            self._keyboard_buffer=''
            self._last_typed=0

    def on_click(self, x, y, button, pressed):
        _int_x = int(x)
        _int_y = int(y)
        if pressed:
            self._last_int_x = int(x)
            self._last_int_y = int(y)

        if self._stage._record > 0:
            self._check_keyboard_buffer(interrupt=True)
            # [Capture screen on click]: (For clean drag event)
            if pressed:
                self._stage._sp.capture()
            else: # [RELEASED]:
                # [Turn off PASS_input after click]:
                if self._PASS_input:
                    self._PASS_input = False
                    return

                # [SHIFT held while clicking | Enter Password]:
                if self._hold_SHIFT:
                    self._stage._pop()
                    self._PASS_input = True
                    _pass = input('Enter password here: ')
                    act = action(state='pass', coords_list={'x': self._last_int_x, 'y': self._last_int_y}, keyboard_buffer=_pass, stage=self._stage)
                    self._stage._append(act)

                    print('Click field to resume! / Please use Submit instead of Enter')
                    return

                # [SAME = CLICK | DIFF = BOX]:
                if abs(_int_x-self._last_int_x) < 5 and abs(_int_y-self._last_int_y) < 5:
                    # [Keep track of last click / tell difference between single/double click]:
                    if self._last_click == 0:
                        self._last_click = time.time()
                        _click_cnt = 1
                    else:
                        if (time.time() - self._last_click) >= .5:
                            _click_cnt = 1
                            self._last_click = time.time()
                        else:
                            _click_cnt = 2
                            self._last_click = 0

                    # [Determine left/right click]:
                    if button==Button.left:
                        _which_click = 'left-click|{0}'.format(_click_cnt)
                    elif button==Button.right:
                        _which_click = 'right-click|{0}'.format(_click_cnt)
                    else:
                        _which_click = 'other-click|{0}'.format(_click_cnt)

                    if _click_cnt ==1:
                        act = action(state=_which_click, coords_list=[{'x': _int_x, 'y': _int_y}], stage=self._stage)
                        self._stage._append(act)
                    else:
                        # [If double-click was made, increment previous single-click]:
                        # ^(Check x,y for double-click check?)
                        _prev_act = self._stage._peek()
                        if '-click|1' in _prev_act._state:
                            _state_split = _prev_act._state.split('-')
                            _prev_act._state = '{0}-click|2'.format(_state_split[0])
                else:
                    if _int_x > self._last_int_x:
                        _which_box = 'ssim-box'
                    else:
                        _which_box = 'drag-box'
                    act = action(state=_which_box, coords_list=[{'x': self._last_int_x, 'y': self._last_int_y}, {'x': _int_x, 'y': _int_y}], stage=self._stage)
                    self._stage._append(act)

    def on_move(self, x, y):
        _int_x = int(x)
        _int_y = int(y)

        self.CHECK_MOUSE_EMERGENCY(_int_x, _int_y)
        # IF ANY MOVEMENT DURING self._stage.record==0 IS EMERGENCY??

        if self._stage._record > 0:
            self._check_keyboard_buffer()
            # ^(Flush keyboard buffer)

    def on_scroll(self, x, y, dx, dy):
        _int_x = int(x)
        _int_y = int(y)
        _int_dx = int(dx)
        _int_dy = int(dy)

        self.CHECK_MOUSE_EMERGENCY(_int_x, _int_y)

        if self._stage._record > 0:
            self._check_keyboard_buffer()
            # ^(Flush keyboard buffer)

            # [Add scroll actions]:
            if _int_dy!=0:
                act = action(state='scroll|{0}'.format(_int_dy), coords_list=[{'x': _int_x, 'y': _int_y}], stage=self._stage)
                self._stage._append(act)
            # ^ (Only add after 200 miliseconds to reduce the # of actions added?)