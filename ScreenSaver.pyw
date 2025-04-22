import time
import os
import psutil
import pygetwindow as gw
from pynput import mouse, keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading

# --- Try importing the inputs library for gamepad support ---
try:
    import inputs
    gamepad_support_enabled = True
except ImportError:
    print("WARN: 'inputs' library not found. Gamepad monitoring disabled.")
    print("      Install it using: pip install inputs")
    gamepad_support_enabled = False
# ---

# Set the inactivity threshold (in seconds)
inactivity_threshold = 60

# Variables to track time since last activity and screensaver start time
last_activity_time = time.time()
screensaver_start_time = None
stop_threads = threading.Event() # Used to signal threads to stop

def start_screensaver():
    # Adjust this path to your screensaver executable if known
    # Common locations (check your system):
    # C:\Windows\System32\*.scr
    # C:\Windows\SysWOW64\*.scr (on 64-bit Windows for 32-bit screensavers)
    screensaver_exe = "C:\\Windows\\System32\\scrnsave.scr"  # Default blank screensaver
    # You might want to try others like "Bubbles.scr", "Mystify.scr", "Ribbons.scr"
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Starting screensaver...")
    try:
        # Using os.startfile is often more robust for launching .scr files
        os.startfile(screensaver_exe)
        # Alternative using os.system (might be needed depending on the screensaver):
        # os.system(f'"{screensaver_exe}" /s') # /s argument usually starts the screensaver directly
    except FileNotFoundError:
        print(f"ERROR: Screensaver executable not found at {screensaver_exe}")
    except Exception as e:
        print(f"ERROR: Failed to start screensaver: {e}")


def update_activity_time(*args, **kwargs):
    """Resets the last activity time."""
    global last_activity_time
    # Optional: Add logging to see which input triggered the update
    # source = "Unknown"
    # if args:
    #     if isinstance(args[0], mouse.Listener): source = "Mouse"
    #     elif isinstance(args[0], keyboard.Listener): source = "Keyboard"
    #     elif isinstance(args[0], str) and args[0] == "Gamepad": source = "Gamepad"
    # print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Activity detected ({source})")
    last_activity_time = time.time()

def is_video_playback_active():
    """Checks if known video players or YouTube in fullscreen are active."""
    video_players = {"vlc.exe", "mpc-hc.exe", "mpc-hc64.exe", "wmplayer.exe", "potplayer.exe", "potplayer64.exe", "plex media player.exe", "kodi.exe"}
    try:
        for process in psutil.process_iter(['name', 'status']):
            # Check if process name is in our list and if it's likely running actively
            if process.info['name'] and process.info['name'].lower() in video_players:
                 # Check status if available (Windows specific often)
                 if hasattr(process, 'status') and process.info['status'] == psutil.STATUS_RUNNING:
                    # Optional: Add more checks like CPU usage if needed
                    # print(f"DEBUG: Found active video player: {process.info['name']}")
                    return True
                 # Fallback if status check isn't reliable/available
                 elif not hasattr(process, 'status'):
                     # print(f"DEBUG: Found video player (status unknown): {process.info['name']}")
                     return True # Assume active if status unknown
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        # Ignore processes that ended or we can't access
        pass
    except Exception as e:
        print(f"Error checking processes: {e}")


    # Check for YouTube specifically (or other sites) in maximized browser windows
    try:
        browser_windows = gw.getWindowsWithTitle('YouTube') # Add other titles like 'Netflix', 'Prime Video' if needed
        # Check common browser processes that might host the video site
        browser_processes = {"chrome.exe", "firefox.exe", "msedge.exe", "opera.exe"}
        active_browser_pids = {p.pid for p in psutil.process_iter(['name', 'pid']) if p.info['name'] and p.info['name'].lower() in browser_processes}

        for window in browser_windows:
             # Check if the window is maximized or fullscreen and belongs to a browser process
             if (window.isMaximized or window.is_fullscreen) and window._hWnd: # Check if handle exists
                 try:
                     win_pid = gw.getWindowPID(window._hWnd) # Requires window._hWnd which might not always be there
                     if win_pid in active_browser_pids:
                        # print(f"DEBUG: Found maximized/fullscreen browser window: {window.title}")
                        return True
                 except Exception as e:
                     # Handle cases where getting PID fails
                     # print(f"DEBUG: Could not get PID for window '{window.title}': {e}")
                     # Fallback: If title matches and it's maximized, assume it might be video
                     if window.isMaximized or window.is_fullscreen:
                         return True

    except Exception as e:
        print(f"Error checking browser windows: {e}")

    return False


def is_screensaver_running():
    """Checks if the screensaver was started recently by this script."""
    # This is a simple check based on our script's state.
    # A more robust check would involve looking for actual screensaver processes,
    # but that can be complex and vary between screensavers.
    global screensaver_start_time
    if screensaver_start_time is None:
        return False
    # Consider the screensaver "running" for a short period after we start it
    # to prevent immediate re-triggering if activity happens right after.
    # Adjust this grace period (e.g., 5 seconds) if needed.
    grace_period = 5
    still_running = time.time() - screensaver_start_time < grace_period
    if not still_running:
        # Reset start time if grace period passed
        screensaver_start_time = None
    return still_running


def monitor_inactivity():
    """Main loop to check inactivity and trigger screensaver."""
    global last_activity_time, screensaver_start_time
    print("Inactivity monitor started.")
    while not stop_threads.is_set():
        try:
            idle_time = time.time() - last_activity_time
            # print(f"DEBUG: Idle time: {idle_time:.1f}s") # Uncomment for debugging

            if (idle_time > inactivity_threshold and
                    not is_video_playback_active() and
                    not is_screensaver_running()):
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Inactivity threshold ({inactivity_threshold}s) reached. Checking conditions...")
                # Double check video playback right before starting
                if not is_video_playback_active():
                    start_screensaver()
                    screensaver_start_time = time.time()
                    # Add a longer sleep after starting screensaver to avoid rapid checks
                    time.sleep(5)
                else:
                     print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Video playback detected, screensaver deferred.")
                     # Update activity time since video is playing
                     update_activity_time("VideoPlayback")


            # Sleep for a short interval before checking again
            time.sleep(1)

        except Exception as e:
            print(f"ERROR in monitor_inactivity loop: {e}")
            time.sleep(5) # Avoid rapid error loops

    print("Inactivity monitor thread stopped.")


def monitor_gamepad():
    """Monitors gamepad events and updates activity time."""
    if not gamepad_support_enabled:
        print("Gamepad monitoring thread not starting (library unavailable).")
        return

    print("Gamepad monitor started.")
    while not stop_threads.is_set():
        try:
            # This blocks until a gamepad event occurs or timeout (if specified)
            events = inputs.get_gamepad() # Can add timeout=1 argument if needed
            if events:
                # Any event from the gamepad counts as activity
                # print(f"DEBUG: Gamepad event detected: {events[0].ev_type}, {events[0].code}, {events[0].state}")
                update_activity_time("Gamepad")

        except inputs.UnpluggedError:
            print("Gamepad unplugged. Waiting for connection...")
            time.sleep(5) # Wait before checking again
        except Exception as e:
            # Catch other potential errors from the inputs library or device issues
            # Filter specific expected errors if possible (e.g., permission denied on Linux)
            if "No gamepad found" in str(e):
                 # This is common, wait silently
                 # print("No gamepad found. Waiting...") # Optional: print only once?
                 time.sleep(5)
            elif "Permission denied" in str(e):
                 print("ERROR: Permission denied accessing gamepad device. Run as admin/root or check device permissions.")
                 time.sleep(10)
            else:
                 print(f"ERROR in monitor_gamepad loop: {type(e).__name__}: {e}")
                 time.sleep(5) # Avoid rapid error loops

    print("Gamepad monitor thread stopped.")


def create_image(width, height, color1, color2):
    """Creates a simple icon image."""
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    return image

def on_quit(icon, item):
    """Callback function when 'Quit' is selected from the tray menu."""
    print("Quit requested. Stopping threads...")
    stop_threads.set() # Signal threads to stop
    if mouse_listener:
        mouse_listener.stop()
    if keyboard_listener:
        keyboard_listener.stop()
    icon.stop()
    print("Application exited.")

def setup_tray():
    """Sets up and runs the system tray icon and starts monitoring threads."""
    icon = Icon("Inactivity Monitor")
    icon.icon = create_image(64, 64, 'black', 'gray') # Slightly changed colors
    icon.title = "Inactivity Monitor"
    icon.menu = Menu(MenuItem("Quit", on_quit))

    # Start the inactivity monitoring thread
    monitor_thread = threading.Thread(target=monitor_inactivity, daemon=True)
    monitor_thread.start()

    # Start the gamepad monitoring thread only if supported
    gamepad_thread = None
    if gamepad_support_enabled:
        gamepad_thread = threading.Thread(target=monitor_gamepad, daemon=True)
        gamepad_thread.start()

    print("System tray icon running. Monitoring activity...")
    # icon.run() will block the main thread here
    icon.run()

    # --- Code after icon.run() will execute after the icon is stopped ---
    # Wait for threads to finish after stop signal (optional, good practice)
    print("Waiting for monitor threads to join...")
    monitor_thread.join(timeout=2)
    if gamepad_thread:
        gamepad_thread.join(timeout=2)
    print("Threads joined.")


# --- Main execution ---
if __name__ == "__main__":
    # Set up mouse and keyboard listeners globally
    # Add error handling in case listeners fail to start (e.g., permissions on Linux)
    mouse_listener = None
    keyboard_listener = None
    try:
        mouse_listener = mouse.Listener(on_move=update_activity_time, on_click=update_activity_time, on_scroll=update_activity_time)
        mouse_listener.start()
    except Exception as e:
        print(f"ERROR: Failed to start mouse listener: {e}")

    try:
        keyboard_listener = keyboard.Listener(on_press=update_activity_time)
        keyboard_listener.start()
    except Exception as e:
        print(f"ERROR: Failed to start keyboard listener: {e}")


    # Reset activity time once at the start
    update_activity_time("ScriptStart")

    # Start the system tray icon and monitoring loops
    setup_tray()

    # Cleanup after setup_tray() finishes (when icon is stopped)
    print("Main thread exiting.")
