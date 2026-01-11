#!/sur/bin/python3.10
# -*- mode: python; Encoding: utf-8; coding: utf-8 -*-
# Last updated: <2026/01/12 05:07:44 +0900>
"""
Windows ScreenSaver sample by Python

/s : Start fullscreen screensaver
/c:HWND : Configure
/p HWND : Preview
Not command line option : Configure

Windows11 x64 25H2 + Python 3.10.10 64bit
+ pygame-ce 2.5.6
+ pywin32 311
+ pillow 11.3.0
+ Nuitka 2.8.9

Author : mieki256
"""

import os
import sys
import time
import datetime
import math
import ctypes
import win32gui
import win32con
import win32api
import win32security
import winerror
import win32event

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


dbg = False

APPLI_NAME = "PyWinScr"
VER_NUM = "0.0.1"

MOUSE_MOVE_DIST = 32

# Windows screensaver preview window size = 152 x 112 pixel
PREVIEW_IMAGE = "res/preview.bmp"

BALL_IMAGE = "res/ball.png"

MUTEX_NAME_FULLSCR = "pywinscrnsaver01_fullscr"
MUTEX_NAME_CONFIG = "pywinscrnsaver01_config"
MUTEX_NAME_PREVIEW = "pywinscrnsaver01_preview"

cmdopt = ""

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()


def show_fullscreen_window():
    """Show fullscreen screensaver by pygame-ce."""

    import pygame  # noqa: E402

    pygame.init()

    # get current display size
    dispsize = pygame.display.get_desktop_sizes()
    disp_w, disp_h = dispsize[0]

    # initialize display
    flags = pygame.FULLSCREEN + pygame.NOFRAME + pygame.HWSURFACE + pygame.DOUBLEBUF
    screen = pygame.display.set_mode((0, 0), flags)
    pygame.display.set_caption(f"{APPLI_NAME} - Screensaver by Python")
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()

    running = True
    prev_mpos = pygame.mouse.get_pos()  # get mouse position

    # load image
    ball = pygame.image.load(resource_path(BALL_IMAGE))
    ballrect = ball.get_rect()
    ballrect.center = (disp_w / 2, disp_h / 2)
    spd = [disp_w / (3 * 60), disp_h / (4 * 60)]

    while running:
        # check key down and mouse button down
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False

        # check mouse move
        mpos = pygame.mouse.get_pos()
        dx = prev_mpos[0] - mpos[0]
        dy = prev_mpos[1] - mpos[1]
        prev_mpos = mpos
        dist = math.sqrt(dx * dx + dy * dy)
        if dist >= MOUSE_MOVE_DIST:
            running = False

        # update
        ballrect.move_ip(spd)
        if ballrect.left < 0 or ballrect.right > disp_w:
            spd[0] = -spd[0]
        if ballrect.top < 0 or ballrect.bottom > disp_h:
            spd[1] = -spd[1]

        # draw
        screen.fill((12, 24, 64))
        screen.blit(ball, ballrect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return


def show_config_window():
    """Show setting window"""

    # Displays the application name and version number in a message box
    message = f"{APPLI_NAME} ver. {VER_NUM}\n\nNo settings available."
    title = "Information"
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000000 | 0x00000040)
    return


def fullscreen_mode():
    """Fullscreen mode"""
    global cmdopt
    mtx, success = get_mutex(MUTEX_NAME_FULLSCR)
    if not success:
        write_log("%s : %s already exists. Exit." % (cmdopt, MUTEX_NAME_FULLSCR))
    else:
        write_log("%s : New process." % cmdopt)
        show_fullscreen_window()
        close_mutex(mtx)


def config_mode():
    """config mode"""
    global cmdopt
    mtx, success = get_mutex(MUTEX_NAME_CONFIG)
    if not success:
        write_log("%s : %s already exists. Exit." % (cmdopt, MUTEX_NAME_CONFIG))
    else:
        write_log("%s : New process." % cmdopt)
        show_config_window()
        close_mutex(mtx)


def preview_mode(parent_hwnd):
    """Preview mode"""
    global cmdopt
    mtx, success = get_mutex(MUTEX_NAME_PREVIEW)
    if not success:
        write_log("%s : %s already exists. Exit." % (cmdopt, MUTEX_NAME_PREVIEW))
    else:
        write_log("%s : New process. HWND = %d" % (cmdopt, parent_hwnd))

        show_preview_window(parent_hwnd)
        close_mutex(mtx)


def show_preview_window(parent_hwnd):
    """Show preview image window"""
    preview = ChildBmpWindow(parent_hwnd, resource_path(PREVIEW_IMAGE))
    if preview.hwnd:
        preview.run()

    return


def wait_for_window(hwnd, timeout=2):
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            return True
        time.sleep(0.1)

    return False


class ChildBmpWindow:
    def __init__(self, parent_hwnd, bmp_path):
        self.parent_hwnd = parent_hwnd
        self.bmp_path = bmp_path
        self.h_bmp = None
        self.class_name = "PyChildBmpWindowClass"

        wait_for_window(self.parent_hwnd)

        self.h_inst = win32api.GetModuleHandle(None)

        self._load_image()
        self.hwnd = self._create_window()

    def _load_image(self):
        if not os.path.exists(self.bmp_path):
            raise FileNotFoundError(f"Error: Not found '{self.bmp_path}'")

        # load bmp image (LR_LOADFROMFILE = 0x10)
        self.h_bmp = win32gui.LoadImage(
            0, self.bmp_path, win32con.IMAGE_BITMAP, 0, 0, win32con.LR_LOADFROMFILE
        )
        if not self.h_bmp:
            raise Exception("Error: load bmp failed.")

    def _create_window(self):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = self.h_inst
        wc.lpszClassName = self.class_name
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = 0

        try:
            win32gui.RegisterClass(wc)
        except win32gui.error as e:
            if e.winerror != 1410:
                raise

        left, top, right, bottom = win32gui.GetClientRect(self.parent_hwnd)
        width, height = right - left, bottom - top

        style = win32con.WS_CHILD | win32con.WS_VISIBLE

        hwnd = win32gui.CreateWindow(
            self.class_name,
            None,  # title
            style,
            0,
            0,
            width,
            height,
            self.parent_hwnd,
            0,
            self.h_inst,
            None,
        )

        if not hwnd:
            return None

        return hwnd

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure"""
        if msg == win32con.WM_PAINT:
            self._on_paint(hwnd)
            return 0

        elif msg == win32con.WM_DESTROY:
            if self.h_bmp:
                win32gui.DeleteObject(self.h_bmp)
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _on_paint(self, hwnd):
        """Paint window"""
        hdc, ps = win32gui.BeginPaint(hwnd)

        mem_dc = win32gui.CreateCompatibleDC(hdc)
        old_bmp = win32gui.SelectObject(mem_dc, self.h_bmp)

        # get target size
        rect = win32gui.GetClientRect(hwnd)
        w, h = rect[2], rect[3]

        win32gui.BitBlt(hdc, 0, 0, w, h, mem_dc, 0, 0, win32con.SRCCOPY)

        # cleanup
        win32gui.SelectObject(mem_dc, old_bmp)
        win32gui.DeleteDC(mem_dc)
        win32gui.EndPaint(hwnd, ps)

    def run(self):
        if self.parent_hwnd:
            wait_for_window(self.parent_hwnd)
            win32gui.InvalidateRect(self.parent_hwnd, None, True)
            win32gui.UpdateWindow(self.parent_hwnd)

        if self.hwnd:
            wait_for_window(self.hwnd)
            win32gui.InvalidateRect(self.hwnd, None, True)
            win32gui.UpdateWindow(self.hwnd)

            # message loop
            win32gui.PumpMessages()


def resource_path(filename):
    """Get resource file path."""
    if False:
        if hasattr(sys, "_MEIPASS"):
            # use PyInstaller
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.abspath(".")
    else:
        base_dir = os.path.dirname(__file__)

    return os.path.join(base_dir, filename)


def write_log(s):
    global dbg
    if dbg:
        desktop_dir = os.path.expanduser("~/Desktop")
        log_file = os.path.join(desktop_dir, "temp.log.txt")
        dt_now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write("[%s] %s\n" % (dt_now, s))


def get_mutex(name):
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.SECURITY_DESCRIPTOR.SetSecurityDescriptorDacl(True, None, False)
    mtx = win32event.CreateMutex(sa, False, name)
    err = win32api.GetLastError()
    if not mtx or err == winerror.ERROR_ALREADY_EXISTS:
        return (mtx, False)
    return (mtx, True)


def close_mutex(mtx):
    global cmdopt
    if mtx:
        # win32event.ReleaseMutex(mtx)
        # win32api.CloseHandle(mtx)
        mtx.Close()
        write_log("%s : Close mutex. Exit." % cmdopt)


def main():
    global cmdopt
    cmdopt = " ".join(sys.argv)

    if "/debug" in sys.argv:
        global dbg
        dbg = True

    if len(sys.argv) >= 2:
        # parse commandline option
        opt = sys.argv[1][0:2].lower()
        if opt == "/s":
            fullscreen_mode()
            return

        if opt == "/c":
            config_mode()
            return

        if opt == "/p":
            if len(sys.argv) >= 3:
                hwnd = int(sys.argv[2])
                preview_mode(hwnd)
                return

    config_mode()


if __name__ == "__main__":
    main()
    sys.exit()
