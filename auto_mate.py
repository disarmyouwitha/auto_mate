import os
import sys
import time
import action
import contextlib
import stage_manager

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


# [https://pythonhosted.org/pynput/]
# [https://pyautogui.readthedocs.io/en/latest/cheatsheet.html]
# [0]: remove tab sequences from command input (reconsider how ESC works)
# [1]: IF BOX "DRAWN BACKWARDS".. USER WAS HIGHLIGHTING TEXT FOR COPY/PASTE (don't capture/try to SSIM)
# [2]: Option to save to file/filename_string instead of b64_bytes
# [3]: MIRROR actions across screen / can set up same page on left/right screen, record on left, and replay on right.
# [4]: Ability to capture Replay of actions (going through form) BUT rather than using captured keystrokes, pass in data for replay
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

    # [Set the stage, let the actors play]:
    stage = stage_manager.stage_manager(_file_name)

    if 'record' in _mode:
        stage.RECORD()

    if 'replay' in _mode:
        stage.REPLAY()

    print('[fin.]')
