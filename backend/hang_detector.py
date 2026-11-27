
import ctypes
from ctypes import wintypes
import psutil
import platform


# This module requires Windows
if platform.system() != "Windows":
    raise OSError("Hang detection currently supports Windows only.")


# Access Windows User32 API
user32 = ctypes.WinDLL("user32", use_last_error=True)

# Define Windows API function signatures
EnumWindows = user32.EnumWindows
EnumWindows.restype = wintypes.BOOL

IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.argtypes = [wintypes.HWND]
IsWindowVisible.restype = wintypes.BOOL

GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextLengthW.argtypes = [wintypes.HWND]
GetWindowTextLengthW.restype = ctypes.c_int

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [
    wintypes.HWND,
    wintypes.LPWSTR,
    ctypes.c_int
]
GetWindowTextW.restype = ctypes.c_int

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD)
]
GetWindowThreadProcessId.restype = wintypes.DWORD

IsHungAppWindow = user32.IsHungAppWindow
IsHungAppWindow.argtypes = [wintypes.HWND]
IsHungAppWindow.restype = wintypes.BOOL


# Callback type used by EnumWindows
WNDENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.LPARAM
)


send_timeout = user32.SendMessageTimeoutW
send_timeout.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                         wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
send_timeout.restype = ctypes.c_ssize_t


def get_application_windows():

    windows = []

    def callback(hwnd, lParam):

        # Ignore invisible windows
        if not IsWindowVisible(hwnd):
            return True

        # Get window title
        length = GetWindowTextLengthW(hwnd)

        if length == 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, title_buffer, length + 1)

        window_title = title_buffer.value

        # Get process ID associated with window
        pid = wintypes.DWORD()

        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        if pid.value == 0:
            return True

        # Check whether Windows considers window hung
        is_hung = bool(IsHungAppWindow(hwnd))

        try:
            proc = psutil.Process(pid.value)
            process_name = proc.name()
            born = proc.create_time()

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "Unknown"
            born = 0

        status = "NOT RESPONDING" if is_hung else "RESPONDING"
        if not is_hung:
            reply = ctypes.c_size_t()
            if not send_timeout(hwnd, 0, 0, 0, 2, 120, ctypes.byref(reply)):
                status = "UNKNOWN"
        windows.append({
            "born": born, "hwnd": hwnd,
            "pid": pid.value,
            "process_name": process_name,
            "window_title": window_title,
            "status": status
        })

        return True

    # Keep callback alive during enumeration
    window_callback = WNDENUMPROC(callback)

    if not EnumWindows(window_callback, 0):
        raise ctypes.WinError(ctypes.get_last_error())

    return windows


def display_hang_report(windows):

    print("\n" + "=" * 90)
    print("             APPLICATION HANG DETECTION REPORT")
    print("=" * 90)

    print(
        f"{'PID':<10}"
        f"{'PROCESS':<25}"
        f"{'WINDOW TITLE':<35}"
        f"{'STATUS':<20}"
    )

    print("-" * 90)

    hung_count = 0

    for window in windows:

        print(
            f"{window['pid']:<10}"
            f"{window['process_name'][:23]:<25}"
            f"{window['window_title'][:33]:<35}"
            f"{window['status']:<20}"
        )

        if window["status"] == "NOT RESPONDING":
            hung_count += 1

    print("=" * 90)

    print(f"Total application windows: {len(windows)}")
    print(f"Unresponsive windows: {hung_count}")
    print(f"Responsive windows: {len(windows) - hung_count}")


if __name__ == "__main__":

    print("Scanning application windows...")

    windows = get_application_windows()

    display_hang_report(windows)
