import json
import time
import numpy
import base64
import imageio
import pyautogui
import jsonpickle

_RETINA = True
_MIRROR = False
_DEBUGG = False
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

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

class action:
    _id = 0
    _state = None
    _action_id = 0
    _ssim_score = None
    _coords_list = None
    _keyboard_buffer = None
    _control_numpy_save = None

    # [Initializer from scratch]:
    def __init__(self, state=None, coords_list=None, keyboard_buffer=None, JSON_STR=None, stage=None):
        #self._stage = stage # Copy of stage for access to screen_pixel
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
                _numpy_array = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=(2 if _RETINA else 1), nemo=stage._sp._numpy)
                self._control_numpy_save= (_numpy_array.shape, base64.b64encode(_numpy_array.tobytes()))
                self.set_ssim(stage)
            self._PRINT('Added')
        else:
            # [Should only ever be 1 key, but whatever]:
            for key in JSON_STR.keys():
                JSON_DATA = json.loads(JSON_STR[key])
                JSON_DATA = jsonpickle.decode(JSON_DATA)
                self._state = JSON_DATA.get('_state')
                self._action_id = JSON_DATA.get('_action_id')
                self._coords_list = JSON_DATA.get('_coords_list')
                self._keyboard_buffer = JSON_DATA.get('_keyboard_buffer')
                stage._sp.capture()

            if self._state == 'box':
                self._ssim_score = JSON_DATA.get('_ssim_score')
                self._control_numpy_save = JSON_DATA.get('_control_numpy_save')
            self._PRINT('Loaded')

    def set_ssim(self, stage=None):
        nemo = stage._sp._numpy
        (_control_shape, _control_64) = self._control_numpy_save
        _control_bytes = base64.b64decode(_control_64)
        _control_array = numpy.frombuffer(_control_bytes, dtype='uint8').reshape(_control_shape)
        test = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=(2 if _RETINA else 1), nemo=nemo)
        self._ssim_score  = stage._sp.check_ssim(_control_array, test)

        #if _DEBUGG:
        #    imageio.imwrite('SSIM_control.png', _control_array) ## 
        #    imageio.imwrite('SSIM_test.png', test) ## 

    def check_ssim(self, stage=None, thresh=.9):
        (_control_shape, _control_64) = self._control_numpy_save
        _control_bytes = base64.b64decode(_control_64)
        _control_array = numpy.frombuffer(_control_bytes, dtype='uint8').reshape(_control_shape)
        test = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=(2 if _RETINA else 1))
        ssim_score = stage._sp.check_ssim(_control_array, test)

        if _DEBUGG:
            imageio.imwrite('{0}_action{1}.png'.format('CONTROL', self._action_id), _control_array) ##
            imageio.imwrite('{0}_action{1}.png'.format('TEST', self._action_id), test) ##

        #print("SAVED_SSIM: {}".format(self._ssim_score))
        # ^(Can probably compared new_ssim to saved_ssim for more accurate results)

        return True if (ssim_score >= thresh) else False

    def str_to_key(self, str):
        (_class, _key) = str.split('.') 
        return getattr(sys.modules[__name__], _class)[_key]

    def RUN(self, stage):
        self._PRINT('Replay')

        # [CLICK| Click Position]: 
        # ^(Need to check click/double-click for replay)
        if self._state == 'click':
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')
            pyautogui.moveTo(_x, _y, duration=1)
            stage._omni._ms_ctrl.click(stage._omni._ms_button.left, 1) # pyautogui wont change active window (OSX)

        # [KEYBOARD| replay typing]:
        if self._state == 'keyboard':
            pyautogui.typewrite(self._keyboard_buffer, interval=.1)

        # [KEY| Special Keys]:
        if self._state == 'key':
            stage._omni._kb_ctrl.press(self.str_to_key(self._keyboard_buffer))
            stage._omni._kb_ctrl.release(self.str_to_key(self._keyboard_buffer))
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
            if self.check_ssim(stage=stage, thresh=1):
                print('[passed]')
            else:
                print('[failed]')

            # [Draw box coords specified]:
            _draw_box = False
            if _draw_box:
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
        _json_dump = json.dumps(self, default=lambda o: jsonpickle.encode(o.__dict__))
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