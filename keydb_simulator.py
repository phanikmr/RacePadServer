from keycodes import get_scan_code
import win32api
import win32con
import time
from os import startfile
import thread


key_state = {}
pressing_mode = True
MOVE_MSC = False
MOVE_PRV = ""


def set_mode(value):
    global pressing_mode
    pressing_mode = value


def mouse_simulator(direction, distance):
    if direction == "TP":
        thread.start_new_thread(mouse_movement, (direction, 0, -distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, -distance, 0, 0)
    elif direction == "BM":
        thread.start_new_thread(mouse_movement, (direction, 0, distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, distance, 0, 0)
    elif direction == "LT":
        thread.start_new_thread(mouse_movement, (direction, -distance, 0))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, -distance, 0, 0, 0)
    elif direction == "RT":
        thread.start_new_thread(mouse_movement, (direction, distance, 0))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, distance, 0, 0, 0)
    elif direction == "TL":
        thread.start_new_thread(mouse_movement, (direction, -distance, -distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, -distance, -distance, 0, 0)
    elif direction == "TR":
        thread.start_new_thread(mouse_movement, (direction, distance, -distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, distance, -distance, 0, 0)
    elif direction == "BL":
        thread.start_new_thread(mouse_movement, (direction, -distance, distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, -distance, distance, 0, 0)
    elif direction == "BR":
        thread.start_new_thread(mouse_movement, (direction, distance, distance))
        #win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, distance, distance, 0, 0)


def mouse_movement(direction,X , Y):
    global MOVE_MSC
    global MOVE_PRV
    while MOVE_PRV[0:2] == direction and MOVE_MSC:
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, X, Y, 0, 0)


def key_event_click(*code):
    for i in range(len(code)):
        win32api.keybd_event(code[i], get_scan_code(code[i]), 0, 0)
        time.sleep(0.1)
    time.sleep(0.1)
    for i in range(len(code)):
        win32api.keybd_event(code[i], get_scan_code(code[i]), win32con.KEYEVENTF_KEYUP, 0)


def key_event_down(code):
    global pressing_mode
    scan_code = get_scan_code(code)
    if code == 0x01:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif code == 0x02:
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    elif code == 0x03:
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
    else:
        win32api.keybd_event(code, scan_code, 0, 0)
    if pressing_mode:
        time.sleep(0.5)
        while key_state[code]:
            win32api.keybd_event(code, 0, 0, 0)
            time.sleep(0.3)
        win32api.keybd_event(code, scan_code, win32con.KEYEVENTF_KEYUP, 0)


def key_event_up(code):
    scan_code = get_scan_code(code)
    if code == 0x01:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif code == 0x02:
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif code == 0x03:
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
    else:
        win32api.keybd_event(code, scan_code, win32con.KEYEVENTF_KEYUP, 0)


def key_code_parser(code):
    if len(code) > 0:
        tag = code[len(code)-3:len(code)]
        code = code[0:len(code)-4]
        try:
            if tag == "NOM":
                tag = code[len(code)-2:len(code)]
                if tag == "UP":
                    code = code[0:len(code)-3]
                    code = int(code, 0)
                    key_state[code] = False
                    key_event_up(code)
                elif tag == "DN":
                    code = code[0:len(code)-3]
                    code = int(code, 0)
                    key_state[code] = True
                    thread.start_new_thread(key_event_down, (code,))
            elif tag == "SPL":
                tag = code[len(code)-1:len(code)]
                code = code[0:len(code)-2]
                if tag == "2":
                    x = code[0:len(code)/2]
                    y = code[len(code)/2:len(code)]
                    x = int(x, 0)
                    y = int(y, 0)
                    key_event_click(x, y)
                elif tag == "1":
                    code = int(code, 0)
                    key_event_click(code)
            elif tag == "MSC":
                global MOVE_MSC
                global MOVE_PRV
                if code[0:3] == "STR":
                    MOVE_MSC = True
                    MOVE_PRV = ""
                elif code[0:3] == "STP":
                    MOVE_MSC = False
                    MOVE_PRV = ""
                else:
                    if code != MOVE_PRV:
                        MOVE_PRV = code
                        direction = code[0:2]
                        distance = code[3:len(code)]
                        distance = int(distance, 0)
                        mouse_simulator(direction, distance)
            elif tag == "LNK":
                try:
                    startfile(code)
                except:
                    print "File Not Found"
        except :
            pass


if __name__ == "__main__":
    key_code_parser("TP_5_MSC")
    key_code_parser("0x5B_1_SPL")
    key_code_parser("0x5B0xAA_2_SPL")
    key_code_parser("34_UP_NOM")
    key_code_parser("34_DN_NOM")