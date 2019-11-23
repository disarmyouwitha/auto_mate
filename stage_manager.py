import os
import sys
import time
import json
import glob
import shutil # shutil.rmtree(path, ignore_errors=False, onerror=None)¶
import action
import pathlib
import threading
import screen_pixel
import omni_listener
import tkinter as tk
#from pathlib import Path
from tkinter import Tk, Frame, Menu

# [Stage Manager to organize actions]:

class main_frame(Frame):
    _stage = None
    _label = None
    _list_box = None
    _record_menu = None
    _save_handler = None
    _button_width = None
    _start_button_x = None
    _start_button_y = None
    _start_stop_button = None

    def __init__(self, master=None, stage=None):
        Frame.__init__(self, master)
        self._stage = stage
        self._button_width = 20

        self.init_menu()
        self.init_frame()

    def init_menu(self):
        self.master.title("[auto_mate]")
        self.master.geometry("500x500")

        # [Create Menu objects]:
        menu_bar = Menu(self.master)
        file_menu = Menu(menu_bar)
        record_menu = Menu(menu_bar)
        import_sub_menu = Menu(file_menu)

        # [Add file_menu objects]:
        menu_bar.add_cascade(label="File", underline=0, menu=file_menu)
        file_menu.add_cascade(label='Import', menu=import_sub_menu, underline=0)
        file_menu.add_separator()
        file_menu.add_cascade(label='Browse Files...', underline=0) # NEED TO LOOK UP HOW TO DO BROWSE FILES
        file_menu.add_separator()
        file_menu.add_command(label="Exit", underline=0, command=self.on_exit)

        '''
        # [NEAT!]: (Walk folders and add to menu) (?)
        FOLDER_DIR = '.'
        for root, dirnames, filenames in os.walk(FOLDER_DIR):
            for filename in fnmatch.filter(filenames, '*'):
                if filename[0] != '.':
                    file_matches.append(os.path.join(root, filename))
            for dirname in fnmatch.filter(dirnames, '*'):
                dir_matches.append(os.path.join(root, dirname))
        '''

        # [Add import_sub_menu objects]: 
        import_sub_menu.add_command(label="Item1")
        import_sub_menu.add_command(label="Item2")
        import_sub_menu.add_command(label="Item3")
        # ^(Todo: add ability to load in replay from folder)
        # ... (Walk current directory and add folders to menu) (?)
        # ... when you click folder, it sets that as "_CWD" and loads .json files from that folder

        # [Add record_menu objects]:
        menu_bar.add_cascade(label="Recording...", underline=0, menu=record_menu)
        record_menu.add_command(label="Start Recording", underline=0, command=self.start_stop_button) 
        record_menu.add_command(label="Save Recording", underline=0, command=self.save_button)
        record_menu.add_command(label="Replay Recording", underline=0, command=self.replay_button)
        record_menu.add_command(label="Delete Recording", underline=0, command=self.delete_button)

        # [Add Menu objects to Frame]:
        self.master.config(menu=menu_bar)
        self._record_menu = record_menu

    def init_frame(self):
        # [Set label for displaying messages]:
        self._label = tk.Label(self.master, text='[Load *.json files or Start Recording]:', width=50)
        self._label.grid(row=1)

        self._list_box = tk.Listbox(self.master, selectmode=tk.SINGLE) # Needs some work before: tk.EXTENDED
        self._list_box.grid(row=2)

        # [Fill _list_box in GUI with *.json files]:
        for file_name in glob.glob('*.json'):
            self.listbox_insert(file_name)
        # ^(Replace with os.walk(?))

        # [Toggle]: (Start Recording|Stop Recording)
        self._start_stop_button = tk.Button(self.master, text='Start Recording', width=self._button_width, command=self.start_stop_button)
        self._start_stop_button.grid(row=3)

        # [Toggle]: (Save Recording|Filename Input)
        self._save_handler = tk.Button(self.master, text='Save Recording', width=self._button_width, command=self.save_button)
        self._save_handler.grid(row=4)

        _button = tk.Button(self.master, text='Replay Recording', width=self._button_width, command=self.replay_button)
        _button.grid(row=5)

        _button = tk.Button(self.master, text='Delete Recording', width=self._button_width, command=self.delete_button)
        _button.grid(row=6)

    # [Start/stop recording mouse/keyboard actions]:
    def start_stop_button(self):
        self._list_box.select_clear(0)
        if self._stage._record==0: # off, START:
            self.set_label_text('[Mouse/Keyboard listeners started!]')
            self._record_menu.entryconfigure(0, label='Stop Recording')
            self._start_stop_button['text'] = 'Stop Recording'
            self._start_button_x = self._stage._omni._last_int_x
            self._start_button_y = self._stage._omni._last_int_y
            self._stage._record = 1
        elif self._stage._record==1: # on, STOP:
            self.set_label_text('[Mouse/Keyboard listeners stopped]')
            self._record_menu.entryconfigure(0, label='Start Recording')
            self._start_stop_button['text'] = 'Start Recording'
            self._stage._record = 0

            # [Check to see if start click is near stop click]: (so we can remove the click on start/stop)
            _diff_x = abs(self._start_button_x-self._stage._omni._last_int_x)
            _diff_y = abs(self._start_button_y-self._stage._omni._last_int_y)
            if (_diff_x < 210 or _diff_y < 30):
                print('[_pop last action: Remove click for Save/Replay Recording]')
                self._stage._pop()

            # [Copy _action_items to _action_memory and clear when stopped]:
            self._stage._action_memory = self._stage._action_items.copy()
            self._stage._action_items = []
        elif self._stage._record==-1: # replay, STOP: (clear action_list to reset replay) (?)
            self._record_menu.entryconfigure(0, label='BOOYA Button')
            self._start_stop_button['text'] = 'BOOYA Button'
            self.set_label_text('[BOOYA!]')
            self._stage._record = 0

    def save_button(self):
        self._stage._record = 0
        self.set_label_text('[Saving file]: enter the filename below!')

        # [Toggle _save_handler]: (Save Recording|Input Filename)
        _str = tk.StringVar()
        self._list_box.select_clear(0)
        _str.set("Enter: filename.json")
        self._save_handler.grid_forget()
        self._save_handler = tk.Entry(self.master, textvariable=_str, width=self._button_width+2)
        self._save_handler.grid(row=4)
        self._save_handler.bind("<Button-1>", self._save_input_click_callback)
        self._save_handler.bind("<Return>", self._save_input_enter_callback)

    def _save_input_enter_callback(event, arg):
        _file_name = event._save_handler.get()

        # [Validate filename]:
        if _file_name=='':
            return None
        if '.json' not in _file_name:
            _file_name = '{0}.json'.format(_file_name)

        # [Call save_sequence]:
        event._stage.save_sequence(file_name=_file_name)

        # [Toggle _save_handler]: (Save Recording|Input Filename)
        event._save_handler.grid_forget()
        event._save_handler = tk.Button(event.master, text='Save Recording', width=event._button_width, command=event.save_button)
        event._save_handler.grid(row=4)

        return None

    def _save_input_click_callback(*args):
        if args[0]._save_handler.get()=="Enter: filename.json":
            args[0]._save_handler.delete(0, "end")
        return None

    def _gui_replay_callback(self):
        _act = self._stage._pop(0)
        if _act != 0:
            _act.RUN(self._stage)
            self.after(200, self._gui_replay_callback)
        else:
            self.set_label_text('[Replay finished]: {0}'.format('FROM MEMORY' if self._stage._file_name is None else self._stage._file_name))

    def replay_button(self):
        if self._stage._record==0:
            self._stage.REPLAY()
            self._gui_replay_callback()

    def delete_button(self):
        (_idx, _selected) = self.listbox_selected()
        self.set_label_text('[Deleted replay]: {0}'.format(_selected))
        self.listbox_delete(_idx)
        os.remove(_selected)
        self._list_box.select_clear(0)

    def set_label_text(self, text=''):
        self._label['text'] = text.center(100)

    def listbox_insert(self, name):
        try:
            _found = False
            for _value in self._list_box.get(0, tk.END):
                if _value==name:
                    _found = True
        except:
            pass

        if _found is False:
            self._list_box.insert(tk.END, name)

    def listbox_delete(self, index):
        self._list_box.delete(index)

    def listbox_selected(self):
        for item in map(int, self._list_box.curselection()):
            _index = item

        # [Return file_name from _list_box]:
        try:
            return (_index, self._list_box.get(_index))
        except:
            return (None, None)

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
    _action_memory = None

    def __init__(self, file_name=None, save_npz=False):
        self._action_items = []
        self._action_memory = []
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
    
    def _pop(self, idx=None):
        if len(self._action_items) > 0:
            if idx is None:
                return self._action_items.pop()
            else:
                return self._action_items.pop(idx)
        return 0

    def _peek(self):
        if len(self._action_items) > 0:
            return self._action_items[len(self._action_items)-1]
        return 0

    # [Saving sequence to JSON file for replay]:
    def save_sequence(self, file_name=None):
        if file_name is not None:
            self._file_name = file_name

        if self._main_stage is None and self._file_name is None:
            self._file_name = input('[Do you wish to save replay?] (`filename.json` for yes): ')

        # STRIP ESC/TAB SEQ FROM _file_name (?)

        # [If not blank, save file]:
        if self._file_name != '':
            _json_seq = {}

            # [Update json_data]:
            for act in self._action_memory:
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
            (_idx, self._file_name) = self._main_stage.listbox_selected()

        if self._file_name is not None and self._file_name != '':
            self._action_items = []

            with open(self._file_name) as _json_seq:
                sequence = json.load(_json_seq)

            for _json_act in sequence:
                act = action.action(JSON_STR={_json_act: sequence[_json_act]}, stage=self)
                self._action_items.append(act)
        else: # if no _file_name was provided, replay from memory
            if len(self._action_items)==0:
                self._action_items = self._action_memory.copy()
            elif len(self._action_memory)==0:
                self._action_memory = self._action_items.copy()

    def GUI(self):
        root = Tk()
        with self._omni.mouse_listener, self._omni.keyboard_listener:
            self._main_stage = main_frame(master=root, stage=self)
            self._main_stage.mainloop()
            # ^(Start the main loop)

    def RECORD(self): #(blocking)
        self._record = 1
        with self._omni.mouse_listener, self._omni.keyboard_listener:
            # [Recording loop]:
            print('[Mouse/Keyboard listening! Press ESC to stop recording]')
            while self._record > 0:
                time.sleep(1) #pass (?)

            print('[Starting Replay]: 2sec')
            time.sleep(2)

            # [Save Sequence]:
            self.save_sequence()

            # [Replay Actions]:
            self._replay_sequence()

            self._replay_loop_check()

    def REPLAY(self):
        self.load_sequence()

        # [GUI handles it's own replay]:
        if self._main_stage is not None:
            self._main_stage.set_label_text('[Replay sequence]: {0}'.format('FROM MEMORY' if self._file_name is None else self._file_name))
        else:
            self._replay_sequence()
            self._replay_loop_check()

    def _replay_sequence(self):
        print('[Replay sequence]: {0}'.format('FROM MEMORY' if self._file_name is None else self._file_name))
        for act in self._action_items:
            act.RUN(self)
        print('[Replay finished]: {0}'.format('FROM MEMORY' if self._file_name is None else self._file_name))

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

