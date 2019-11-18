import io
import os ##
import json
import time
import numpy
import base64
import imageio
import pyautogui
import jsonpickle

_DEBUGG = False
_MIRROR = False
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
    _coords_list = None
    _keyboard_buffer = None
    _control_numpy_save = None

    def __init__(self, state=None, coords_list=None, keyboard_buffer=None, JSON_STR=None, stage=None):
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
            if 'box' in self._state:
                _RETINA = stage._sp._check_screen()
                _numpy_array = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=(2 if _RETINA else 1), nemo=stage._sp._numpy)

                # [Compress and save numpy array of image]:
                _bytes = io.BytesIO()
                numpy.savez_compressed(_bytes, a=_numpy_array)

                if stage._save_npz:
                    _file_name = '{0}_action{1}.npz'.format(('SEQ' if stage._file_name is None else stage._file_name[:-5]), self._action_id)
                    with open(_file_name, 'wb') as f:
                        f.write(_bytes.getvalue())
                    self._control_numpy_save = _file_name
                else:
                    self._control_numpy_save = _bytes.getvalue()

            self._PRINT(verb='Added')
        else:
            # [Should only ever be 1 key, but whatever]:
            for key in JSON_STR.keys():
                JSON_DATA = json.loads(JSON_STR[key])
                self._state = JSON_DATA.get('_state')
                self._action_id = JSON_DATA.get('_action_id')
                self._coords_list = JSON_DATA.get('_coords_list')
                self._keyboard_buffer = JSON_DATA.get('_keyboard_buffer')
                stage._sp.capture()

            if 'box' in self._state:
                if stage._save_npz:
                    self._control_numpy_save = '{0}_action{1}.npz'.format(('SEQ' if stage._file_name is None else stage._file_name[:-5]), self._action_id)
                else:
                    self._control_numpy_save = jsonpickle.decode(JSON_DATA.get('_control_numpy_save'))
            #self._PRINT(verb='Loaded')


    def check_ssim(self, stage=None, thresh=.9):
        if self._control_numpy_save is None:
            print('[Issue saving, no _control_numpy_save for SSIM!]')
            os._exit(1)
        if type(self._control_numpy_save) is str:
            _loaded = numpy.load(self._control_numpy_save)
        else:
            _loaded = numpy.load(io.BytesIO(self._control_numpy_save))
        _control_array = _loaded['a']

        _RETINA = stage._sp._check_screen()
        test = stage._sp.grab_rect(self._coords_list[0],self._coords_list[1], mod=(2 if _RETINA else 1))
        ssim_score = stage._sp.check_ssim(_control_array, test)

        if _DEBUGG:
            imageio.imwrite('{0}_action{1}.png'.format('CONTROL', self._action_id), _control_array) ##
            imageio.imwrite('{0}_action{1}.png'.format('TEST', self._action_id), test) ##

        if ssim_score >= thresh:
            print('[passed]: {0}'.format(ssim_score))
        else:
            print('[failed]: {0}'.format(ssim_score))

        return True if (ssim_score >= thresh) else False

    def RUN(self, stage):
        self._PRINT(verb='Replay')

        # [CLICK| Click Position]: 
        if 'click' in self._state:
            (_which_click, _num_clicks) = self._state.split('|')
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')
            pyautogui.moveTo(_x, _y, duration=1)
            stage._omni.CLICK(which_click=_which_click, num_clicks=int(_num_clicks), type_click='click')

        # [SCROLL| Move to x,y and Scroll]:
        if 'scroll' in self._state:
            (_scroll, _num_clicks) = self._state.split('|')
            _x = self._coords_list[0].get('x')
            _y = self._coords_list[0].get('y')
            pyautogui.scroll(_num_clicks, x=_x, y=_y)

        # [KEYBOARD| replay typing]:
        if self._state == 'keyboard':
            pyautogui.typewrite(self._keyboard_buffer, interval=.1)

        # [KEY| Special Keys]:
        if self._state == 'key':
            (_key_list, _pressed) = stage._omni._str_to_key(self._keyboard_buffer)
            _key= _key_list[0]

            if _pressed==1: # press
                stage._omni.PRESS(_key)
            elif _pressed==0: # release
                stage._omni.RELEASE(_key)
            elif _pressed==3: # tap
                stage._omni.PRESS(_key)
                stage._omni.RELEASE(_key)

        # [PASS| Enter password]:
        if self._state == 'pass':
            # [Move mouse && click on _x, _y]: (?)
            #_x = self._coords_list[0].get('x')
            #_y = self._coords_list[0].get('y')
            #pyautogui.click(x=_x, y=_y, button='left', clicks=1)
            pyautogui.typewrite(self._keyboard_buffer, interval=.1)

        if 'box' in self._state:
            _start_x = self._coords_list[0].get('x')
            _start_y = self._coords_list[0].get('y')
            _stop_x = self._coords_list[1].get('x')
            _stop_y = self._coords_list[1].get('y')

            # [BOX| CHECK SSIM]:
            if self._state == 'ssim-box':
                _draw_box = False
                if _draw_box:
                    # [Draw box coords specified]:
                    _diff_x = (_stop_x - _start_x)
                    _diff_y = (_stop_y - _start_y)
                    pyautogui.moveTo(_start_x, _start_y, duration=1)
                    pyautogui.moveTo((_start_x+_diff_x),_start_y, duration=1)
                    pyautogui.moveTo((_start_x+_diff_x),(_start_y+_diff_y), duration=1)
                    pyautogui.moveTo(_start_x,(_start_y+_diff_y), duration=1)
                    pyautogui.moveTo(_start_x,_start_y, duration=1)

                # [Check SSIM of box]:
                _SSIM = self.check_ssim(stage=stage, thresh=.999)

            #[BOX| DRAG BOX]:
            elif self._state == 'drag-box':
                pyautogui.moveTo(_start_x, _start_y, duration=1)
                stage._omni.CLICK(which_click='drag-click', type_click='press')
                pyautogui.moveTo(_stop_x, _stop_y, duration=1)
                stage._omni.CLICK(which_click='drag-click', type_click='release')
                time.sleep(.25) # small delay after selecting

        # [Slight delay between actions]:
        time.sleep(.25)

    # [Serializer]: (helper)
    # [jsonpickle objects with no __dict__]:
    def _serialize(self, obj):
        try:
            return obj.__dict__
        except:
            return jsonpickle.encode(obj)

    # [Serializer]:
    def _JSON(self):
        _json_dump = json.dumps(self, default=self._serialize)
        return {'action{0}'.format(self._action_id): _json_dump}

    # [Pretty Print actions]:
    def _PRINT(self, verb):
        if 'click' in self._state:
            print('{0} action{1}({2}): {3}'.format(verb, self._action_id, self._state, self._coords_list[0]))
        elif 'key' in self._state:
            print('{0} action{1}({2}): {3}'.format(verb, self._action_id, self._state, self._keyboard_buffer))
        elif 'pass' in self._state:
            print('{0} action{1}({2})'.format(verb, self._action_id, self._state))
        elif 'box' in self._state:
            for _coord in self._coords_list:
                print('{0} action{1}({2}): {3}'.format(verb, self._action_id, self._state, _coord))
        else:
            print('{0} action{1}({2}): {3}'.format(verb, self._action_id, self._state, self._coords_list[0]))