import os
import sys
import time
import action
import contextlib
import stage_manager
import getopt, sys


# [OSX restricts certain actions to root, pynput cant access without sudo]:
if sys.platform == 'darwin':
    if os.getuid() != 0:
        print('[If you are using OSX, please run as root: `sudo python3 auto_mate.py`]')
        os._exit(1)

# [Neat helper function for timing operations!]:
@contextlib.contextmanager
def timer(msg):
    start = time.time()
    yield
    end = time.time()
    print('%s: %.02fms'%(msg, (end-start)*1000))


# [-]: # @todo add GUI hooks for Save button
# [-]: Browser mode will open browser window for user at specified x,y and width,height so that tests can be made more consistent across computers
# [-]: OSX/Windows mode will attempt to flip ['minimize', 'restore', 'close'] x,y (within 5px of ^browser._close_x,browser._close_y) from mac to windows (or other)
# [-]: ^(Will need to record if sequence was saved on OSX/Windows,/w what modes?)(basically wrap JSON in header array /w file_name, operating_system, etc)
# [0]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
# [1]: Ability to capture Replay of actions (going through form) BUT rather than using captured keystrokes, pass in data for replay
# [2]: Tweening / Easing for neater replay?
#    > https://pyautogui.readthedocs.io/en/latest/mouse.html#tween-easing-functions
if __name__ == "__main__":
    # [Check command line arguments for mode]:
    accepted_modes = ['record', 'replay', 'gui']

    _mode = sys.argv[1]
    if _mode in accepted_modes:
        # [Check command line arguments for file_name]:
        try:
            _file_name = sys.argv[2]
        except:
            _file_name = None

        # [Set the stage, let the actors play]:
        stage = stage_manager.stage_manager(_file_name, save_npz=False)

        if _mode != 'gui':
            # [Command Line]:
            if 'record' in _mode:
                stage.RECORD()
            if 'replay' in _mode:
                stage.REPLAY()
        else:
            # [Draw simple gui]:
            stage.GUI()

    else:
        print('Syntax: python3 auto_mate.py record | python3 auto_mate.py replay filename.json')
        os._exit(1)

    print('[fin.]')
