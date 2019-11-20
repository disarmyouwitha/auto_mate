import os
import sys
import time
import json
import glob
import action
import threading
import screen_pixel
import omni_listener
import tkinter as tk
from tkinter import Tk, Frame, Menu

# [Stage Manager to organize actions]:

class main_frame(Frame):
    stage = None
    _start_button_x = None
    _start_button_y = None

    def __init__(self, master=None, stage=None):
        Frame.__init__(self, master)
        self.label = tk.Label(self, text='not running')
        self.label.pack()

        self.listbox = tk.Listbox(self)
        self.listbox.pack()

        self.button = tk.Button(self, text='Start Recording', command=self.start_button)
        self.button.pack(pady=15)
        self.pack()

        self.button = tk.Button(self, text='Save Recording', command=self.stop_button)
        self.button.pack(pady=15)
        self.pack()

        self.button = tk.Button(self, text='Replay Recording', command=self.replay_button)
        self.button.pack(pady=15)
        self.pack()

        self.stage = stage
        self.initUI()

    def initUI(self):
        self.master.title("Automate")
        self.master.geometry("500x500")

        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        # [NEAT!]:
        filemenu = Menu(menubar)
        submenu = Menu(filemenu)
        submenu.add_command(label="Item1")
        submenu.add_command(label="Item2")
        submenu.add_command(label="Item3")

        # @todo add ability to load in replay from folder
        filemenu.add_cascade(label='Import', menu=submenu, underline=0)

        filemenu.add_separator()

        filemenu.add_command(label="Exit", underline=0, command=self.on_exit)
        menubar.add_cascade(label="File", underline=0, menu=filemenu)

    # [Start recording mouse/keyboard actions]:
    def start_button(self):
        print('[Mouse/Keyboard listening! Press ESC to stop recording]')
        self._start_button_x = self.stage._omni._last_int_x
        self._start_button_y = self.stage._omni._last_int_y
        self.set_label_text('running')
        self.stage._record = 1

    # [Stop]: (and Save?)
    def stop_button(self):
        self.stage._record = 0
        self.set_label_text('not running')

        if self._start_button_y:
            _diff_x = abs(self._start_button_x-self.stage._omni._last_int_x)
            _diff_y = abs(self._start_button_y-self.stage._omni._last_int_y)

            if (_diff_x < 150 or _diff_y < 100):
                print('[pop action and remove click on stop]')
                self.stage._pop()

        # [Saving sequence for replay]:
        self.stage.save_sequence()

    def replay_button(self):
        self.set_label_text('Replay')
        self.stage.REPLAY()

    def set_label_text(self, text=''):
        self.label['text'] = text

    def listbox_insert(self, item):
        self.listbox.insert(tk.END, item)

    def listbox_selected(self):
        for item in map(int, self.listbox.curselection()):
                _index = item

        # [Return file_name from listbox]:
        try:
            return self.listbox.get(_index)
        except:
            return None

    def on_exit(self):
        self.quit()


class stage_manager:
    _sp = None
    _record = 0
    _omni = None
    _save_npz = None
    _file_name = None
    _main_stage = None
    _action_items = None

    def __init__(self, file_name=None, save_npz=False):
        self._action_items = []
        self._save_npz = save_npz
        self._file_name = file_name
        self._sp = screen_pixel.screen_pixel()
        self._omni = omni_listener.omni_listener(self)

        # [Get screen info]: (Can Wrap action_items[] with header in save_sequence so we can use this info for replay normalization(?))
        (_os, _resolution, _retina) = self._sp._get_screen_info()
        self._OS = _os
        self._RETINA = _retina
        self._RESOLUTION = _resolution
        print('_OS: {0}'.format(_os))
        print('_RETINA: {0}'.format(_retina))
        print('_RESOLUTION: {0}'.format(_resolution))

    def __iter__(self):
        return action.action_iterator(self)

    def _append(self, action):
        self._action_items.append(action)
    
    def _pop(self):
        if len(self._action_items) > 0:
            return self._action_items.pop()
        return 0

    def _peek(self):
        if len(self._action_items) > 0:
            return self._action_items[len(self._action_items)-1]
        return 0

    # [Saving sequence to JSON file for replay]:
    def save_sequence(self):
        #if self._main_stage is None: # (?)
        if self._file_name is None:
            self._file_name = input('[Do you wish to save replay?] (`filename.json` for yes): ')

        # STRIP ESC/TAB SEQ FROM _file_name (?)

        # [If not blank, save file]:
        if self._file_name != '':
            _json_seq = {}

            # [Update json_data]:
            for act in self:
                _json_seq.update(act._JSON())

            print('[Saved sequence for replay]: {0}'.format(self._file_name))
            with open(self._file_name, 'w+') as fp:
                json.dump(_json_seq, fp)

            # [Add to list in GUI]:
            self._main_stage.listbox_insert(self._file_name)

    def load_sequence(self):
        if self._main_stage is None:
            if self._file_name is None:
                self._file_name = input('What file would you like to replay?: (blank for last replay)')
        else: # GUI:
            self._file_name = self._main_stage.listbox_selected()

        # HANDLE IF NO FILE NAME WAS PROVIDED: LOAD FROM STAGE.ACTION_LIST
        if self._file_name != '':
            print('[Loading replay file]: {0}'.format(self._file_name))
            self._action_items = []

            with open(self._file_name) as _json_seq:
                sequence = json.load(_json_seq)

            for _json_act in sequence:
                act = action.action(JSON_STR={_json_act: sequence[_json_act]}, stage=self)
                self._action_items.append(act)
        else:
            print('[Loading replay from memory]')

    def GUI(self):
        root = Tk()
        with self._omni.mouse_listener, self._omni.keyboard_listener:
            self._main_stage = main_frame(master=root, stage=self)

            # [Fill listbox in GUI with *.json files]:
            for file_name in glob.glob('*.json'):
                self._main_stage.listbox_insert(file_name)

            # [Start the main loop]:
            self._main_stage.mainloop()

    def RECORD(self): #(blocking)
        self._record = 1
        with self._omni.mouse_listener, self._omni.keyboard_listener:
            # [Recording loop]:
            print('[Mouse/Keyboard listening! Press ESC to stop recording]')
            while self._record > 0:
                time.sleep(1) #pass (?)

            print('[Starting Replay]: 2sec')
            time.sleep(2)

            # [Replay Actions]:
            self._replay_sequence()

            # [Save Sequence]:
            self.save_sequence()

            self._replay_loop_check()

    def REPLAY(self):
        self._record = 0
        self.load_sequence()
        self._replay_sequence()
        if self._main_stage is None:
            self._replay_loop_check()

    def _replay_sequence(self):
        print('[Replaying sequence]')
        for act in self._action_items:
            act.RUN(self)
        print('[Replaying finished]')

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

