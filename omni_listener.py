import os
import time
from action import action
import pynput.mouse as ms
import pynput.keyboard as kb
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Controller

class omni_listener():
    # [CONTROLLERS]:
    _kb_ctrl = None
    _ms_ctrl = None

    # [MOUSE GLOBALS]:
    _click_int_x = None
    _click_int_y = None

    # [KEYBOARD GLOBALS]:
    _typed_last = 0
    _keyboard_buffer = ''
    _hold_ESC = False
    _hold_ALT = False
    _hold_TAB = False
    _hold_CMD = False
    _hold_CTRL = False
    _hold_SHIFT = False
    _CMD_input = False

    # [GLOBALS]:
    _record = 1
    _stage = None

    def __init__(self, stage=None):
        self._stage = stage
        self._kb_ctrl = kb.Controller()
        self._ms_ctrl = ms.Controller()
        self._ms_button = ms.Button

        self.mouse_listener = ms.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = kb.Listener(on_press=self.on_press, on_release=self.on_release)
        # ^(non-blocking mouse/keyboard listener)

    # [Mouse position at 0,0 is emergency exit condition]:
    def CHECK_MOUSE_EMERGENCY(self, _int_x, _int_y):
        if _int_x == 0 and _int_y == 0:
            print('[MOUSE_PANIC_EXIT]')
            os._exit(1)

    # [SHIFT+ESC is emergency exit condition]:
    def CHECK_KEYBOARD_EMERGENCY(self):
        if self._hold_ESC and self._hold_SHIFT:
            print('[KEYBOARD_PANIC_EXIT]')
            os._exit(1)

    def on_press(self, key):
        if self._record > 0:
            # [CMD_input for passwords, etc]:
            if self._CMD_input:
                return

            self.check_keyboard_buffer()

            try:
                _key = key.char
                if self._typed_last == 0:
                    self._typed_last = time.time()

                self._keyboard_buffer+=key.char
                self._typed_last = time.time()
            except AttributeError:
                # [Pass-through on other special characters]: 
                #print('special key {0} pressed'.format(key))
                # ^DEBUGG

                _pass_thru = False

                # HANDLE_SPECIAL_KEYS()

                # [If SHIFT is pressed]:
                if key == kb.Key.shift:
                    self._hold_SHIFT = True

                # [if backspace, pop last character from buffer]:
                if key == kb.Key.backspace:
                    if len(self._keyboard_buffer) > 0:
                        self._keyboard_buffer = self._keyboard_buffer[:-1]
                    else: # [Otherwise add as special character for replay?]:
                        act = action(state='key', coords_list={'x': self._click_int_x, 'y': self._click_int_y}, keyboard_buffer=key, stage=self._stage)
                        self._stage.append(act)

                # [Add space for spacebar xD]:
                if key == kb.Key.space:
                    self._keyboard_buffer+=' '

                # [If ALT key pressed]:
                if key == kb.Key.alt:
                    self._hold_ALT = True

                # [If CMD key pressed]:
                if key == kb.Key.cmd:
                    self._hold_CMD = True

                # [If TAB key pressed]:
                if key == kb.Key.tab:
                    self._hold_TAB = True
                    self.check_keyboard_buffer(interrupt=True)

                    _hold_ALT_CMD = False
                    if sys.platform == 'darwin':
                        _hold_ALT_CMD = self._hold_CMD
                    else:
                        _hold_ALT_CMD = self._hold_ALT

                    # [Ignore alt-tab]: (?)
                    if _hold_ALT_CMD:
                        pass
                    else: # [Add TAB key]:
                        _pass_thru = True

                # [If ESC key pressed]:
                if key == kb.Key.esc:
                    self._hold_ESC = True
                    self._record = 0
                    print('[Listeners "stopped"]')

                # [If CTRL key pressed]:
                if key == kb.Key.ctrl:
                    self._hold_CTRL = True

                # [If ENTER key pressed]:
                if key == kb.Key.enter:
                    self._pass_thru = True

                # [If ARROW key pressed]:
                if key == kb.Key.up:
                    self._pass_thru = True
                if key == kb.Key.down:
                    self._pass_thru = True
                if key == kb.Key.left:
                    self._pass_thru = True
                if key == kb.Key.right:
                    self._pass_thru = True

                if _pass_thru:
                    self.check_keyboard_buffer(interrupt=True)
                    act = action(state='key', coords_list={'x': self._click_int_x, 'y': self._click_int_y}, keyboard_buffer=key, stage=self._stage)
                    self._stage.append(act)

                self.CHECK_KEYBOARD_EMERGENCY()

    def on_release(self, key):
        if self._record > 0:
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

    def check_keyboard_buffer(self, interrupt=False):
        if interrupt==True or ((self._typed_last > 0) and (time.time() - self._typed_last) >= 2):
            if self._keyboard_buffer != '':
                # [Action for Keyboard takes x,y of last click and keyboard_buffer]:
                act = action(state='keyboard', coords_list={'x': self._click_int_x, 'y': self._click_int_y}, keyboard_buffer=self._keyboard_buffer, stage=self._stage)
                self._stage.append(act)

            self._keyboard_buffer=''
            self._typed_last=0

    def on_click(self, x, y, button, pressed):
        _int_x = int(x)
        _int_y = int(y)

        if self._record > 0:
            self.check_keyboard_buffer(interrupt=True)

            if pressed:
                self._click_int_x = int(x)
                self._click_int_y = int(y)

                # [Capture screen on click]: (For clean drag event)
                self._stage._sp.capture()
            else: # [RELEASED]:
                # [Turn off CMD_input after click]:
                if self._CMD_input:
                    self._CMD_input = False
                    return

                # [SHIFT held while clicking | Enter Password]:
                if self._hold_SHIFT:
                    self._CMD_input = True
                    _pass = input('Enter password here: ')
                    act = action(state='pass', coords_list={'x': self._click_int_x, 'y': self._click_int_y}, keyboard_buffer=_pass, stage=self._stage)
                    self._stage.append(act)

                    print('Click field to resume! / Please use Submit instead of Enter')
                    return

                # [SAME = CLICK | DIFF = BOX]:
                if abs(_int_x-self._click_int_x) < 5 and abs(_int_y-self._click_int_y) < 5:
                    act = action(state='click', coords_list=[{'x': _int_x, 'y': _int_y}], stage=self._stage)
                    self._stage.append(act)
                else:
                    act = action(state='box', coords_list=[{'x': self._click_int_x, 'y': self._click_int_y}, {'x': _int_x, 'y': _int_y}], stage=self._stage)
                    self._stage.append(act)

    def on_move(self, x, y):
        #global _record
        _int_x = int(x)
        _int_y = int(y)

        self.CHECK_MOUSE_EMERGENCY(_int_x, _int_y)

        if self._record > 0:
            self.check_keyboard_buffer()
            # ^(Flush keyboard buffer)