#!python
# -*- mode: python; Encoding: utf-8; coding: utf-8 -*-
# Last updated: <2026/01/04 22:59:07 +0900>
"""
pywin32でウインドウを作成。
ウインドウハンドル(HWND)を子スクリプトに渡す。

Windows11 x64 25H2 + Python 3.10.10 64bit
"""

import win32gui
import win32con
import win32api
import subprocess
import sys
import os

# 起動対象となる子プロセスのスクリプト名
CHILD_PY = "pywinscr.pyw"


def wnd_proc(hwnd, msg, wparam, lparam):
    """ウインドウプロシージャ。イベントメッセージ処理関数"""

    if msg == win32con.WM_DESTROY:
        # ウィンドウ破棄時のメッセージ(WM_DESTROY)
        # メッセージループ(PumpMessages)を終了させる信号を送る
        print("[Parent] WM_DESTROY 受信。Quit を送信。")
        win32gui.PostQuitMessage(0)
        return 0

    # 自分で処理しないメッセージは、Windowsのデフォルト処理に任せる
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def create_window_and_launch_child():
    # --- 1. ウィンドウクラスの定義と登録 ---
    window_class_name = "MyPythonWindowClass"

    # ウィンドウの「型」となるクラス構造体を作成
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = wnd_proc  # 上で定義したメッセージ処理関数を紐付け
    wc.lpszClassName = window_class_name  # クラス名（ウィンドウを識別する名前）
    # 現在実行中のインスタンスハンドルを取得
    wc.hInstance = win32api.GetModuleHandle(None)
    wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)  # 背景色を白に設定

    try:
        # 定義したウィンドウクラスをOSに登録
        win32gui.RegisterClass(wc)
    except win32gui.error as e:
        # 同じクラス名が登録済み(Error code = 1410)は無視
        if e.winerror != 1410:
            raise

    # --- 2. ウィンドウの実体を作成 ---
    hwnd = win32gui.CreateWindow(
        window_class_name,  # 使用する登録済みクラス名
        "Parent Window",  # ウィンドウのタイトルバーに表示される文字列
        win32con.WS_OVERLAPPEDWINDOW,  # 一般的なウィンドウ形式（最小化・最大化・枠あり）
        win32con.CW_USEDEFAULT,  # 表示位置 X（OSにお任せ）
        win32con.CW_USEDEFAULT,  # 表示位置 Y（OSにお任せ）
        512,  # ウィンドウの幅
        288,  # ウィンドウの高さ
        0,  # 親ウィンドウのハンドル（今回は自身が親なので0）
        0,  # メニューハンドル
        wc.hInstance,  # インスタンスハンドル
        None,  # 追加の作成パラメータ
    )

    if not hwnd:
        print("[Parent] Error: ウィンドウ作成に失敗。")
        return

    # 作成したウィンドウを表示状態にする
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

    # HWND (Window Handle) は、Windows内でのこのウィンドウの固有の背番号のようなもの
    print(f"[Parent] ウインドウ生成。HWND: {hwnd}")

    # --- 3. 子プロセス起動 ---
    try:
        # 起動中のPython実行環境 (sys.executable) を使って子スクリプトを実行
        # 引数として「/p HWND」を渡す
        print(f"[Parent] {CHILD_PY} を起動...")
        _, ext = os.path.splitext(CHILD_PY)
        if ext == ".py" or ext == ".pyw":
            subprocess.Popen([sys.executable, CHILD_PY, "/p", str(hwnd)])
        elif ext == ".exe":
            subprocess.Popen([CHILD_PY, "/p", str(hwnd)])

    except Exception as e:
        print(f"子プロセス起動に失敗: {e}")

    # --- 4. メッセージループの開始 ---
    # これを実行しないとウィンドウが「応答なし」になり、すぐにプログラムが終了してしまう。
    # Windowsから送られてくる「再描画」「移動」等のメッセージを常に待ち受け wnd_procに振り分ける。
    print("[Parent] メッセージループ開始。")
    win32gui.PumpMessages()

    print("[Parent] プロセス終了。")


if __name__ == "__main__":
    create_window_and_launch_child()
