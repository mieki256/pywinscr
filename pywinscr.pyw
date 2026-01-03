#!/sur/bin/python3.10
# -*- mode: python; Encoding: utf-8; coding: utf-8 -*-
# Last updated: <2026/01/03 04:05:11 +0900>
"""
Windows ScreenSaver sample by Python

/s : Start fullscreen screensaver
/c : Configure
/p HWND : Preview
Not command line option : Configure

Windows11 x64 25H2 + Python 3.10.10 64bit + tkinter
+ pygame-ce 2.5.6
+ pywin32 311
+ pillow 11.3.0
+ Nuitka 2.8.9

Author : mieki256
"""

import os
import sys
import datetime
import tkinter as tk
import math
import win32gui
import win32con
import win32api
import win32security
import winerror
import win32event
import ctypes
from PIL import Image, ImageWin

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402

dbg = False

APPLI_NAME = "PyWinScrnSaver01"
VER_NUM = "0.0.1"

MOUSE_MOVE_DIST = 32

# Windows screensaver preview window size = 152 x 112 pixel
PREVIEW_IMAGE = "res/preview.png"

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
    """Show setting window by tkinter."""

    root = tk.Tk()
    root.title("Setting")
    # root.geometry("400x200")

    lbl = tk.Label(root, text=APPLI_NAME, font=("Segoe UI", 18, "bold"))
    lbl2 = tk.Label(root, text=f"ver. {VER_NUM}", font=("Segoe UI", 12, "normal"))
    lbl3 = tk.Label(
        root, text="No settings available.", font=("Segoe UI", 12, "normal")
    )
    btn = tk.Button(root, text="OK", width=10, command=root.destroy)
    lbl.pack(padx=48, pady=4)
    lbl2.pack(padx=48, pady=3)
    lbl3.pack(padx=48, pady=16)
    btn.pack(padx=24, pady=16)

    root.lift()
    root.focus_force()

    root.mainloop()
    return


def show_preview_window(parent_hwnd):
    """Show preview image window"""
    preview = PreviewWindow(parent_hwnd, resource_path(PREVIEW_IMAGE))
    if preview.hwnd is None:
        return

    win32gui.InvalidateRect(preview.hwnd, None, True)
    win32gui.UpdateWindow(preview.hwnd)
    win32gui.PumpMessages()
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


class PreviewWindow:
    """Preview window"""

    def __init__(self, parent_hwnd, image_path):
        self.parent_hwnd = parent_hwnd
        self.resized_dib = None
        self.draw_rect = (0, 0, 0, 0)
        self._prepare_high_quality_image(image_path)
        self.class_name = "PythonStaticHighQualityChild"
        self.hwnd = self._create_window()

    def _prepare_high_quality_image(self, path):
        """Cretae preview thumbnail image by Pillow"""
        try:
            rect = win32gui.GetClientRect(self.parent_hwnd)
            tgtw = rect[2] - rect[0]
            tgth = rect[3] - rect[1]

            if tgtw <= 0 or tgth <= 0:
                print("Error: Failed to obtain parent window size.")
                sys.exit(1)

            img = Image.open(path).convert("RGB")

            iw, ih = img.size
            if iw != tgtw or ih != tgth:
                resized_img = img.resize((tgtw, tgth), Image.Resampling.LANCZOS)
                self.resized_dib = ImageWin.Dib(resized_img)
            else:
                self.resized_dib = ImageWin.Dib(img)

            self.draw_rect = (0, 0, tgtw, tgth)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _create_window(self):
        """Create child window"""
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = self.class_name
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

        try:
            win32gui.RegisterClass(wc)
        except win32gui.error as e:
            if e.winerror != 1410:
                raise

        w = self.draw_rect[2]
        h = self.draw_rect[3]

        hwnd = win32gui.CreateWindowEx(
            0,
            self.class_name,
            "Child Window",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            0,
            0,
            w,
            h,
            self.parent_hwnd,
            0,
            win32api.GetModuleHandle(None),
            None,
        )

        if not hwnd:
            print("[Child] Error: Window creation failed.")
            return None

        return hwnd

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure"""
        if msg == win32con.WM_PAINT:
            hdc, ps = win32gui.BeginPaint(hwnd)
            if self.resized_dib:
                self.resized_dib.draw(hdc, self.draw_rect)
            win32gui.EndPaint(hwnd, ps)
            return 0

        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


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
