import os
import sys
import time
import json
import action
import screen_pixel
import omni_listener

# [Stage Manager to organize actions]:
class stage_manager:
    _sp = None
    _omni = None
    _record = None
    _save_npz = None
    _file_name = None
    _action_items = None

    def __init__(self, file_name, save_npz=False):
        self._action_items = []
        self._save_npz = save_npz
        self._file_name = file_name
        self._sp = screen_pixel.screen_pixel()
        self._omni = omni_listener.omni_listener(self)

    def __iter__(self):
        return action.action_iterator(self)

    def _append(self, action):
        self._action_items.append(action)
    
    def _pop(self):
        if len(self._action_items) > 0:
            return self._action_items.pop()

    def _peek(self):
        if len(self._action_items) > 0:
            return self._action_items[len(self._action_items)-1]

    def save_sequence(self, file_name=None):
        _json_seq = {}

        if file_name is None:
            file_name = input('What would you like the filename to be?: ')

        self._file_name = file_name

        # [Update json_data]:
        for act in self:
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
            act = action.action(JSON_STR={_json_act: sequence[_json_act]}, stage=self)
            self._action_items.append(act)

    def RECORD(self):
        self._record = 1
        with self._omni.mouse_listener, self._omni.keyboard_listener:
            # [Recording loop]:
            print('[Mouse/Keyboard listening! Press CTRL to stop recording]')
            while self._record > 0:
                time.sleep(1) #pass (?)

            print('[Starting Replay]: 2sec')
            time.sleep(2)

            # [Replay Actions]:
            self._replay_sequence()

            # [Saving sequence to JSON file for replay]:
            _file_name = ''
            if self._file_name is None:
                _file_name = input('[Do you wish to save replay?] (`filename.json` for yes): ')
            else:
                _file_name = self._file_name

            # [If not blank, save file]:
            if _file_name != '':
                self.save_sequence(_file_name)

            self._replay_loop_check()

    def REPLAY(self):
        self._record = 0
        if self._file_name and '.json' in self._file_name:
            self.load_sequence(self._file_name)
            self._replay_sequence()
            self._replay_loop_check()
        else:
            print('[Syntax: `python3 auto_mate.py replay filename.json`]')
            os._exit(1)

    def _replay_sequence(self):
        print('[Replaying sequence]')
        for act in self._action_items:
            act.RUN(self)

    def _replay_loop_check(self):
        # [See if user wants to continue loop]:
        _again = 1
        while _again > 0:
            _again-=1
            if _again==0:
                _again = input('[Do you wish to Replay again?] (N for no, # for loop): ')

                # [Remove tabs and escapes from command input]:
                _again = _again.replace('\x1b', '')
                _again = _again.replace('\t', '')

                # [alpha to int]:
                if _again.isalpha() or _again=='':
                    _again = 0 if (_again.lower() == 'n' or _again.lower() == 'no') else 1
                else:
                    _again = int(_again)

            if _again > 0:
                self._replay_sequence()