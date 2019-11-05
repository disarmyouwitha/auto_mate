import sys
import time
from pynput import mouse, keyboard

_mouse_record = True

def on_move(x, y):
    print('Pointer moved to {0}'.format(
        (x, y)))

def on_click(x, y, button, pressed):
    global _mouse_record
    print('{0} at {1}'.format(
        'Pressed' if pressed else 'Released',
        (x, y)))
    if not pressed:
        # Stop listener
        _mouse_record = False
        return False

def on_scroll(x, y, dx, dy):
    print('Scrolled {0} at {1}'.format(
        'down' if dy < 0 else 'up',
        (x, y)))



# Collect events until released
#with mouse.Listener(
#        on_move=on_move,
#        on_click=on_click,
#        on_scroll=on_scroll) as listener:
#    listener.join()

# ...or, in a non-blocking fashion:
listener = mouse.Listener(on_click=on_click)
listener.start()

while _mouse_record:
    time.sleep(1)
