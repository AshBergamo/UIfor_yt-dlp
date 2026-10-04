"""Open the packaged Windows app, verify its native window, then close it."""
import ctypes
import argparse
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    if os.name != "nt":
        raise SystemExit("This check needs a Windows desktop session.")
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=root / "baixarMusicaYouTube/dist/baixar_musica_qt.exe")
    executable = parser.parse_args().executable.resolve()
    if not executable.is_file():
        raise SystemExit("Build the Windows executable first; see docs/BUILD.md.")
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    user.EnumChildWindows.argtypes = [wintypes.HWND, callback, wintypes.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.IsZoomed.argtypes = [wintypes.HWND]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    windows, owned, titles, exceptions = [], set(), set(), []

    def read_child(hwnd, _):
        value = ctypes.create_unicode_buffer(16000)
        user.GetWindowTextW(hwnd, value, 16000)
        if value.value:
            exceptions.append(value.value)
        return True

    def find(hwnd, _):
        name = ctypes.create_unicode_buffer(256)
        user.GetWindowTextW(hwnd, name, 256)
        if not name.value:
            return True
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return True
        try:
            path = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(32768)
            if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and Path(path.value).resolve() == executable.resolve():
                titles.add(name.value)
                owned.add(hwnd)
                if name.value == "UIfor_yt-dlp":
                    windows.append(hwnd)
                elif name.value == "Unhandled exception in script":
                    user.EnumChildWindows(hwnd, callback(read_child), 0)
        finally:
            kernel.CloseHandle(handle)
        return True

    # Never close an instance already being used before this smoke starts.
    user.EnumWindows(callback(find), 0)
    if owned:
        raise SystemExit("Close existing instances of this executable before running its UI check.")
    env = dict(os.environ, QT_QPA_PLATFORM="windows")
    process = subprocess.Popen([str(executable)], cwd=executable.parent, env=env)
    try:
        deadline = time.monotonic() + 60
        while not windows and time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Executable exited before opening its window")
            user.EnumWindows(callback(find), 0)
            if exceptions:
                raise RuntimeError("Packaged app error: " + "\n".join(dict.fromkeys(exceptions)))
            time.sleep(.2)
        if not windows:
            raise RuntimeError("Native app window did not open; own window titles: " + repr(sorted(titles)))
        time.sleep(1)
        result = {"title": "UIfor_yt-dlp", "maximized": bool(user.IsZoomed(windows[0])), "opened": True}
        for hwnd in windows:
            user.PostMessageW(hwnd, 0x0010, 0, 0)
        result["exit_code"] = process.wait(timeout=15)
        if result["exit_code"] != 0:
            raise RuntimeError("Executable did not exit normally")
        print(json.dumps(result))
    finally:
        for hwnd in owned:
            user.PostMessageW(hwnd, 0x0010, 0, 0)
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)


if __name__ == "__main__":
    main()
