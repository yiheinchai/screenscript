# --- START OF FILE macro.py ---

from pynput import mouse, keyboard
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button
import time
from time import sleep
from datetime import datetime
from threading import Thread, RLock
import json
import os
import sys  # Import sys for stderr

# ... (Keep KEY_NAME_MAP and vk_nb dictionaries as they are) ...
KEY_NAME_MAP = {
    "esc": Key.esc,
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "shift": Key.shift,
    "cmd": Key.cmd,
    "win": Key.cmd,
    "space": Key.space,
    "enter": Key.enter,
    "tab": Key.tab,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "page_up": Key.page_up,
    "page_down": Key.page_down,
    "caps_lock": Key.caps_lock,
}
vk_nb = {
    "<96>": "0",
    "<97>": "1",
    "<98>": "2",
    "<99>": "3",
    "<100>": "4",
    "<101>": "5",
    "<102>": "6",
    "<103>": "7",
    "<104>": "8",
    "<105>": "9",
    "<65437>": "5",
    "<110>": ".",
}


# --- MacroPlayback Class (Listener Logic Removed) ---
class MacroPlayback:
    """Core playback logic - Listener managed by PyMacroRecordLib"""

    # Remove __init__ parameters related to stop_key and listener
    def __init__(self, settings):
        self.mouse_control = mouse.Controller()
        self.keyboard_control = keyboard.Controller()
        self.playback = False
        self.macro_events = {"events": []}
        self.settings = settings
        self.__play_macro_thread = None
        # self._stop_listener = None # REMOVED
        # self.stop_key = stop_key # REMOVED
        self._lock = RLock()

    def load_macro(self, macro_data):
        """Load macro events from a dictionary (parsed JSON)"""
        self.macro_events = macro_data

    # REMOVE set_stop_key, _parse_key_string, set_stop_key_from_string methods
    # REMOVE _on_press_stop_key method

    def start_playback(self):
        """Start macro playback programmatically. Returns True on success, False otherwise."""
        with self._lock:
            if not self.macro_events["events"]:
                print("No macro loaded or macro is empty.")
                return False
            if self.playback:
                print("Playback already in progress.")
                return False
            if self.__play_macro_thread and self.__play_macro_thread.is_alive():
                print(
                    "Warning: Playback thread seems to be already running.",
                    file=sys.stderr,
                )
                # Optionally try to join/stop previous thread? Risky. Better to prevent.
                return False  # Prevent starting if thread already exists

            self.playback = True  # Set flag *before* starting threads

        # --- Playback Thread ---
        # Ensure previous thread object is cleared if it finished/died
        self.__play_macro_thread = None
        print("Starting playback thread...")
        self.__play_macro_thread = Thread(target=self.__play_events, daemon=True)
        self.__play_macro_thread.start()
        return True  # Indicate success

    def stop_playback(self):
        """Stop macro playback programmatically. Thread-safe."""
        print("Playback engine stop requested...")
        with self._lock:
            if not self.playback:
                # print("Playback engine is not currently marked as active.") # Less verbose
                return  # Already stopped or stopping

            print("Setting playback engine flag to False.")
            self.playback = False  # Set flag to signal the playback thread

        # Listener is stopped by PyMacroRecordLib now
        print("Playback engine stop process initiated.")

    def __play_events(self):
        """Internal method to execute macro events in a thread."""
        # --- Initialization before loop ---
        user_settings = self.settings.get_config()
        click_func = {
            "leftClickEvent": Button.left,
            "rightClickEvent": Button.right,
            "middleClickEvent": Button.middle,
        }
        key_to_unpress = []
        repeat_times = (
            user_settings["Playback"]["Repeat"]["Times"]
            if user_settings["Playback"]["Repeat"]["For"] == 0
            else 1
        )
        repeat_duration = (
            user_settings["Playback"]["Repeat"]["For"]
            if user_settings["Playback"]["Repeat"]["For"] > 0
            else None
        )
        start_time = time.time() if repeat_duration else None

        # --- Scheduled Start ---
        scheduled_start_sec = user_settings["Playback"]["Repeat"]["Scheduled"]
        if scheduled_start_sec > 0:
            # ... (scheduled start logic remains the same, checking self.playback) ...
            now = datetime.now()
            seconds_since_midnight = (
                now - now.replace(hour=0, minute=0, second=0, microsecond=0)
            ).total_seconds()
            seconds_to_wait = scheduled_start_sec - seconds_since_midnight
            if seconds_to_wait < 0:
                seconds_to_wait += 86400

            if seconds_to_wait > 0:
                print(f"Scheduled start: Waiting for {seconds_to_wait:.2f} seconds...")
                wait_interval = 0.5
                while seconds_to_wait > 0:
                    with self._lock:
                        if not self.playback:
                            break
                    sleep(min(wait_interval, seconds_to_wait))
                    seconds_to_wait -= wait_interval
                with self._lock:
                    if not self.playback:
                        print(
                            "Playback stopped by external request before scheduled start."
                        )
                        self.__unpress_everything(key_to_unpress)
                        return
                print("Scheduled time reached. Starting playback.")

        # --- Repeat Loop ---
        repeat_count = 0
        loop_running = True
        while loop_running:
            with self._lock:  # Check stop flag at start of loop
                if not self.playback:
                    print("Playback flag is false at start of repeat loop.")
                    loop_running = False
                    break

            repeat_count += 1
            # Check duration/times limits
            if repeat_duration and (time.time() - start_time) >= repeat_duration:
                print(f"Repeat duration ({repeat_duration}s) reached.")
                loop_running = False
                break
            if not repeat_duration and repeat_count > repeat_times:
                print(f"Repeat times ({repeat_times}) reached.")
                loop_running = False
                break

            # print(f"--- Starting Repeat #{repeat_count} ---") # Can be verbose

            # --- Event Loop ---
            for event_data in self.macro_events["events"]:
                with self._lock:  # Check stop flag before each event
                    if not self.playback:
                        print(
                            "Playback stopped by external request during event execution."
                        )
                        loop_running = False
                        break

                # Calculate Sleep Time
                time_sleep = event_data["timestamp"]
                # ... (sleep calculation logic remains the same) ...
                if user_settings["Others"]["Fixed_timestamp"] > 0:
                    time_sleep = user_settings["Others"]["Fixed_timestamp"] / 1000.0
                else:
                    speed_multiplier = user_settings["Playback"]["Speed"]
                    if speed_multiplier > 0:
                        time_sleep /= speed_multiplier
                    else:
                        time_sleep = 0
                time_sleep = max(0, time_sleep)

                # Sleep with Interrupt Check
                sleep_interval = 0.05
                remaining_sleep = time_sleep
                while remaining_sleep > 0:
                    with self._lock:  # Check stop flag during sleep
                        if not self.playback:
                            break
                    sleep(min(sleep_interval, remaining_sleep))
                    remaining_sleep -= sleep_interval
                with self._lock:  # Check again after sleep
                    if not self.playback:
                        print(
                            "Playback stopped by external request during sleep interval."
                        )
                        loop_running = False
                        break

                # --- Execute Event ---
                if not loop_running:
                    break  # Exit if stopped during sleep

                event_type = event_data["type"]
                try:
                    # ... (event execution logic remains the same) ...
                    if event_type == "cursorMove":
                        self.mouse_control.position = (event_data["x"], event_data["y"])
                    elif event_type in click_func:
                        self.mouse_control.position = (event_data["x"], event_data["y"])
                        button = click_func[event_type]
                        if event_data["pressed"]:
                            self.mouse_control.press(button)
                        else:
                            self.mouse_control.release(button)
                    elif event_type == "scrollEvent":
                        self.mouse_control.scroll(event_data["dx"], event_data["dy"])
                    elif event_type == "keyboardEvent":
                        if event_data["key"] is not None:
                            key_str = event_data["key"]
                            key_to_press = None
                            if "Key." in key_str:
                                try:
                                    key_to_press = eval(key_str, {"Key": Key})
                                except Exception as e:
                                    print(
                                        f"Warning: Could not evaluate key '{key_str}': {e}",
                                        file=sys.stderr,
                                    )
                            elif key_str in vk_nb:
                                key_to_press = vk_nb[key_str]
                            else:
                                key_to_press = key_str

                            if key_to_press is not None:
                                if event_data["pressed"]:
                                    self.keyboard_control.press(key_to_press)
                                    if key_to_press not in key_to_unpress:
                                        key_to_unpress.append(key_to_press)
                                else:
                                    self.keyboard_control.release(key_to_press)
                                    if key_to_press in key_to_unpress:
                                        try:
                                            key_to_unpress.remove(key_to_press)
                                        except ValueError:
                                            pass

                except Exception as e:
                    print(
                        f"Error during playback execution (Event: {event_data}): {e}",
                        file=sys.stderr,
                    )
                    print("Stopping playback engine due to error.", file=sys.stderr)
                    loop_running = False  # Signal to exit loops
                    # Signal the engine's stop mechanism
                    Thread(target=self.stop_playback, daemon=True).start()
                    break

            # --- Check Stop Condition AFTER event loop ---
            if not loop_running:
                break

            # --- Delay Between Repeats ---
            repeat_delay = user_settings["Playback"]["Repeat"]["Delay"]
            is_last_repeat = (not repeat_duration and repeat_count >= repeat_times) or (
                repeat_duration and (time.time() - start_time) >= repeat_duration
            )

            if repeat_delay > 0 and not is_last_repeat:
                # print(f"--- Delaying for {repeat_delay}s before next repeat ---") # Verbose
                sleep_interval = 0.1
                remaining_delay = repeat_delay
                while remaining_delay > 0:
                    with self._lock:  # Check stop flag during delay
                        if not self.playback:
                            break
                    sleep(min(sleep_interval, remaining_delay))
                    remaining_delay -= sleep_interval
                with self._lock:
                    if not self.playback:
                        print(
                            "Playback stopped by external request during repeat delay."
                        )
                        loop_running = False
                        # No break needed here, loop condition handles it

        # --- End of Playback ---
        print("Playback engine loop finished or was stopped.")
        self.__unpress_everything(key_to_unpress)

        # --- Crucially: Set playback flag to False *from within the thread* when done ---
        # This indicates the thread has finished its work naturally.
        print("Playback thread marking itself as finished.")
        with self._lock:
            self.playback = False

        print("Playback thread terminating.")

    def __unpress_everything(self, key_to_unpress):
        """Release keys tracked *during this specific playback run*."""
        # ... (unpress logic remains the same) ...
        if key_to_unpress:
            print(f"Releasing {len(key_to_unpress)} potentially held keys...")
            keys_released_count = 0
            for key in list(key_to_unpress):
                try:
                    self.keyboard_control.release(key)
                    keys_released_count += 1
                    try:
                        key_to_unpress.remove(key)
                    except ValueError:
                        pass
                except Exception:
                    pass
            # print(f"Attempted release for {keys_released_count} keys.")


# --- Dummy UserSettings (Keep as is or import your actual class) ---
try:
    # from utils.user_settings import UserSettings # Use your actual path
    # Dummy class provided if import fails
    class UserSettings:
        def __init__(self, _):
            self._config = {
                "Playback": {
                    "Speed": 1.0,
                    "Repeat": {
                        "Times": 1,
                        "For": 0,
                        "Interval": 0,
                        "Scheduled": 0,
                        "Delay": 0,
                    },
                },
                "Others": {"Fixed_timestamp": 0},
            }
            self._lock = RLock()

        def get_config(self):
            with self._lock:
                return self._config

        def change_settings(self, section, sub_section, key, value):
            with self._lock:
                try:
                    if key:
                        self._config[section][sub_section][key] = value
                    elif sub_section:
                        self._config[section][sub_section] = value
                    else:
                        self._config[section] = value
                except KeyError:
                    print(
                        f"Error: Invalid setting path {section}/{sub_section}/{key}",
                        file=sys.stderr,
                    )

except ImportError:
    print("Warning: Could not import UserSettings. Using placeholder.", file=sys.stderr)
    # Define the dummy UserSettings class here if needed


# --- PyMacroRecordLib as Singleton (Modified for Global Listener) ---
class PyMacroRecordLib:
    _instance = None
    _lock = RLock()  # Lock for singleton creation

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Creating new PyMacroRecordLib singleton instance.")
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        print("Initializing PyMacroRecordLib singleton...")
        with self._lock:  # Protect initialization
            # --- Core Attributes ---
            self.settings = UserSettings(None)  # Or load your actual settings
            self.playback_engine = MacroPlayback(self.settings)
            self._active = False  # Tracks if WE intended playback to start

            # --- NEW: State for Main Loop Control ---
            self.user_requested_main_loop_stop = False
            self._main_stop_lock = RLock()  # Separate lock for this flag

            # --- NEW: Listener Attributes (moved from MacroPlayback) ---
            self._stop_listener = None
            self.stop_key = Key.esc  # Default stop key

            # --- Start the listener ONCE during singleton initialization ---
            self._start_global_listener()

            self._initialized = True
            print("Singleton initialization complete. Global listener started.")

    # --- NEW: Listener Methods (moved here) ---
    def _parse_key_string(self, key_string):
        """Helper to parse a string into a pynput Key object or character."""
        key_string = key_string.lower().strip()
        if key_string in KEY_NAME_MAP:
            return KEY_NAME_MAP[key_string]
        elif len(key_string) == 1:
            return key_string
        else:
            try:
                key = eval(f"Key.{key_string}", {"Key": Key})
                if isinstance(key, Key):
                    return key
            except Exception:
                pass
            print(
                f"Warning: Could not parse stop key '{key_string}'. Using default: {self.stop_key}",
                file=sys.stderr,
            )
            return self.stop_key

    def set_stop_key(self, key_string):
        """Set the key used to stop playback AND the main loop."""
        parsed_key = self._parse_key_string(key_string)
        if self.stop_key != parsed_key:
            self.stop_key = parsed_key
            print(f"Global stop key set to: {self.stop_key}")
            # Restart listener with the new key
            self._stop_global_listener()
            self._start_global_listener()

    def _on_press_stop_key(self, key):
        """Callback for the global keyboard listener."""
        try:
            if key == self.stop_key:
                print(f"\n>>> Global Stop Key ({self.stop_key}) pressed! <<<")

                # 1. Signal the main loop to stop
                print("Signaling main loop termination...")
                self.request_main_loop_stop()  # Use the new method

                # 2. Signal the current playback engine run to stop (if active)
                print("Requesting current macro playback engine stop...")
                # Run stop_playback in a thread to avoid blocking listener
                Thread(target=self.playback_engine.stop_playback, daemon=True).start()

        except Exception as e:
            print(f"Error in global stop key listener callback: {e}", file=sys.stderr)

    def _start_global_listener(self):
        """Starts the single global keyboard listener."""
        if self._stop_listener is not None:
            print(
                "Warning: Global listener already exists. Stopping previous one.",
                file=sys.stderr,
            )
            self._stop_global_listener()
        try:
            print(f"Starting global listener for stop key: {self.stop_key}")
            # Create as daemon so it doesn't block exit
            self._stop_listener = KeyboardListener(
                on_press=self._on_press_stop_key, daemon=True
            )
            self._stop_listener.start()
        except Exception as e:
            print(
                f"FATAL: Error starting global keyboard listener: {e}", file=sys.stderr
            )
            self._stop_listener = None  # Ensure it's None if start failed

    def _stop_global_listener(self):
        """Stops the single global keyboard listener."""
        if self._stop_listener:
            print("Stopping global listener...")
            try:
                self._stop_listener.stop()
                # self._stop_listener.join(timeout=0.5) # Optional wait
            except Exception as e:
                print(f"Error stopping global listener: {e}", file=sys.stderr)
            finally:
                self._stop_listener = None

    # --- NEW: Methods for Main Loop Control ---
    def request_main_loop_stop(self):
        """Sets the flag to indicate the main loop should stop."""
        with self._main_stop_lock:
            self.user_requested_main_loop_stop = True
            print("Main loop stop request flag SET.")

    def should_main_loop_stop(self):
        """Checks if the main loop stop has been requested."""
        with self._main_stop_lock:
            # print(f"Checking main loop stop flag: {self.user_requested_main_loop_stop}") # Debug
            return self.user_requested_main_loop_stop

    def reset_main_loop_stop_request(self):
        """Resets the flag before starting a batch run."""
        with self._main_stop_lock:
            if self.user_requested_main_loop_stop:
                print("Resetting main loop stop request flag.")
                self.user_requested_main_loop_stop = False

    # --- Core Methods (operate on the single playback_engine) ---

    def load_macro_file(self, file_path):
        """Load a macro file (.pmr or .json)."""
        # ... (load logic remains the same, uses self.playback_engine) ...
        if not os.path.exists(file_path):
            print(f"Error: Macro file not found: {file_path}", file=sys.stderr)
            return False
        try:
            with open(file_path, "r") as f:
                macro_data = json.load(f)
            if (
                not isinstance(macro_data, dict)
                or "events" not in macro_data
                or not isinstance(macro_data["events"], list)
            ):
                print(f"Error: Invalid macro format in: {file_path}.", file=sys.stderr)
                return False
            self.playback_engine.load_macro(macro_data)
            # print(f"Macro loaded: {os.path.basename(file_path)}") # Less verbose
            return True
        except Exception as e:
            print(f"Error loading macro file {file_path}: {e}", file=sys.stderr)
            return False

    def start_playback(self):
        """Start the loaded macro playback using the singleton engine."""
        if self._active:
            print(
                "Warning: Playback start requested, but already marked as active.",
                file=sys.stderr,
            )
            return  # Don't start again if we think it's running

        # Reset engine's internal flag just in case it got stuck? Risky.
        # Assume engine state is reliable.

        print("Attempting to start playback engine...")
        success = self.playback_engine.start_playback()
        if success:
            self._active = True  # Mark that we initiated a start
            print("Playback engine successfully started.")
        else:
            self._active = False
            print("Playback engine failed to start.", file=sys.stderr)

    def stop_playback(self):
        """Stop the macro playback if it's running using the singleton engine."""
        # This method is primarily for programmatic stopping, Esc uses the listener directly.
        print("Programmatic stop requested for playback engine.")
        self.playback_engine.stop_playback()
        self._active = (
            False  # Mark that we requested stop / it's no longer intended active
        )

    def is_playing(self):
        """Check if the playback engine THREAD is currently active."""
        # Check the engine's internal flag, which reflects the thread's state
        engine_is_running = self.playback_engine.playback
        # Also update our intended state flag if engine stopped by itself
        if self._active and not engine_is_running:
            # print("Syncing state: Engine stopped, marking inactive.") # Debug
            self._active = False
        return engine_is_running

    def wait_for_playback_to_finish(self, check_interval=0.2):
        """Wait until playback engine thread is no longer active."""
        if not self.is_playing():  # Use our updated is_playing()
            # print("Playback not running, nothing to wait for.") # Verbose
            return

        print("Waiting for playback engine to finish...")
        # Loop while the engine thread reports it's running
        while self.playback_engine.playback:  # Check engine flag directly here
            # --- NEW: Check for main loop stop request DURING wait ---
            if self.should_main_loop_stop():
                print("Main loop stop requested during wait. Aborting wait.")
                # Ensure playback stop is triggered again if needed
                if self.playback_engine.playback:
                    print("Re-requesting engine stop...")
                    Thread(
                        target=self.playback_engine.stop_playback, daemon=True
                    ).start()
                break  # Exit the wait loop early

            try:
                time.sleep(check_interval)
            except KeyboardInterrupt:  # Handle Ctrl+C during wait
                print("\nWait interrupted by Ctrl+C. Requesting stop...")
                self.request_main_loop_stop()  # Signal main loop too
                Thread(target=self.playback_engine.stop_playback, daemon=True).start()
                break

        # Update our active flag after waiting finishes
        self._active = False
        print("Wait finished. Playback engine stopped or main stop requested.")

    # --- Configuration Methods (remain the same, operate on self.settings) ---
    def set_playback_speed(self, speed):
        if 0.1 <= speed <= 10:
            self.settings.change_settings("Playback", "Speed", None, float(speed))
        else:
            print("Error: Playback speed must be between 0.1 and 10.", file=sys.stderr)

    # ... other configuration methods (set_repeat_times, etc.) remain the same ...
    def set_repeat_times(self, times):
        times = int(times)
        if 1 <= times <= 100000000:
            self.settings.change_settings("Playback", "Repeat", "Times", times)
            if self.settings.get_config()["Playback"]["Repeat"]["For"] != 0:
                self.settings.change_settings("Playback", "Repeat", "For", 0)
        else:
            print(
                "Error: Repeat times must be between 1 and 100000000.", file=sys.stderr
            )

    def set_repeat_for_duration(self, duration_sec):
        duration_sec = float(duration_sec)
        if 0 <= duration_sec <= 86400 * 7:
            self.settings.change_settings("Playback", "Repeat", "For", duration_sec)
        else:
            print(
                "Error: Repeat duration must be between 0 and 604800 seconds.",
                file=sys.stderr,
            )

    def set_fixed_timestamp(self, timestamp_ms):
        timestamp_ms = int(timestamp_ms)
        if 0 <= timestamp_ms <= 100000000:
            self.settings.change_settings(
                "Others", "Fixed_timestamp", None, timestamp_ms
            )
        else:
            print(
                "Error: Fixed timestamp must be between 0 and 100000000 ms.",
                file=sys.stderr,
            )

    def set_scheduled_start(self, scheduled_sec_since_midnight):
        scheduled_sec_since_midnight = int(scheduled_sec_since_midnight)
        if 0 <= scheduled_sec_since_midnight <= 86400:
            self.settings.change_settings(
                "Playback", "Repeat", "Scheduled", scheduled_sec_since_midnight
            )
        else:
            print(
                "Error: Scheduled start must be between 0 and 86400.", file=sys.stderr
            )

    def set_delay_between_repeats(self, delay_sec):
        delay_sec = float(delay_sec)
        if 0 <= delay_sec <= 100000000:
            self.settings.change_settings("Playback", "Repeat", "Delay", delay_sec)
        else:
            print(
                "Error: Delay must be between 0 and 100000000 seconds.", file=sys.stderr
            )


# --- Wrapper Function (play_macro) ---
# This function now uses the singleton implicitly and primarily configures/starts playback
def play_macro(
    file_name,
    speed=1.0,
    repeat_times=1,
    delay_between_repeats=0.5,
    # removed stop_key argument, as it's now global to the singleton
):
    """Plays a macro file using the singleton PyMacroRecordLib instance."""
    if not os.path.exists(file_name):
        print(f"Macro file not found: {file_name}", file=sys.stderr)
        return False

    pmr_lib = PyMacroRecordLib()  # Get the singleton

    # --- NEW: Check if main loop stop was already requested ---
    if pmr_lib.should_main_loop_stop():
        print(
            f"Skipping macro '{os.path.basename(file_name)}' as main loop stop is requested."
        )
        return False  # Don't even try to play if stop is already active

    # Configure playback settings for this specific call
    pmr_lib.set_playback_speed(speed)
    pmr_lib.set_repeat_times(repeat_times)
    pmr_lib.set_delay_between_repeats(delay_between_repeats)
    # pmr_lib.set_stop_key(stop_key) # REMOVED - stop key is global now

    # Load and play
    if pmr_lib.load_macro_file(file_name):
        print(f"Playing macro '{os.path.basename(file_name)}'...")
        pmr_lib.start_playback()  # Start the engine thread

        # Wait for this specific playback run to finish OR main stop request
        pmr_lib.wait_for_playback_to_finish()

        # Check AGAIN if main stop was requested DURING playback/wait
        if pmr_lib.should_main_loop_stop():
            print(
                f"Macro '{os.path.basename(file_name)}' interrupted by global stop request."
            )
            return False  # Indicate it was stopped prematurely

        print(f"Macro '{os.path.basename(file_name)}' finished.")
        return True  # Indicate successful completion
    else:
        print(f"Failed to load macro file: {file_name}", file=sys.stderr)
        return False


# --- Example Usage (Modified) ---
if __name__ == "__main__":
    import time

    # ... (dummy macro file creation remains the same) ...
    dummy_macro_file = "checkpsmapet.pmr"
    dummy_macro_data = {  # Shortened example
        "events": [
            {"type": "cursorMove", "x": 100, "y": 100, "timestamp": 0.2},
            {
                "type": "leftClickEvent",
                "x": 100,
                "y": 100,
                "pressed": True,
                "timestamp": 0.1,
            },
            {
                "type": "leftClickEvent",
                "x": 100,
                "y": 100,
                "pressed": False,
                "timestamp": 0.1,
            },
            {"type": "keyboardEvent", "key": "'H'", "pressed": True, "timestamp": 0.1},
            {"type": "keyboardEvent", "key": "'H'", "pressed": False, "timestamp": 0.1},
            {"type": "keyboardEvent", "key": "'i'", "pressed": True, "timestamp": 0.1},
            {"type": "keyboardEvent", "key": "'i'", "pressed": False, "timestamp": 0.1},
        ]
    }
    try:
        with open(dummy_macro_file, "w") as f:
            json.dump(dummy_macro_data, f, indent=4)
        print(f"Created dummy macro file: {dummy_macro_file}")
    except Exception as e:
        print(f"Error creating dummy macro file: {e}", file=sys.stderr)
        dummy_macro_file = None

    if dummy_macro_file:
        print("\n--- Getting Singleton Instance (starts listener) ---")
        pmr_lib = PyMacroRecordLib()
        pmr_lib.set_stop_key("esc")  # Set the desired global stop key

        print(
            f"\n--- Running Test Loop (Press '{pmr_lib.stop_key}' to stop everything) ---"
        )
        # Reset stop flag before starting test loop
        pmr_lib.reset_main_loop_stop_request()

        for i in range(5):  # Run a few iterations for testing
            print(f"\n--- Test Loop Iteration {i+1} ---")

            # Check for stop request at the beginning of the loop
            if pmr_lib.should_main_loop_stop():
                print("Stop requested, breaking main test loop.")
                break

            print(f"Running macro {dummy_macro_file}...")
            success = play_macro(
                dummy_macro_file, speed=1.0, repeat_times=2, delay_between_repeats=0.3
            )

            if not success and pmr_lib.should_main_loop_stop():
                print("Macro play interrupted by stop key, breaking main test loop.")
                break  # Exit loop if macro was stopped by Esc

            # Simulate other work in the loop
            if not pmr_lib.should_main_loop_stop():
                print("Doing other work...")
                time.sleep(0.5)

        print("\n--- Test Loop Finished ---")

        # --- Clean up dummy file ---
        try:
            os.remove(dummy_macro_file)
            print(f"Cleaned up dummy macro file: {dummy_macro_file}")
        except Exception as e:
            print(f"Error removing dummy macro file: {e}", file=sys.stderr)

    print("\nAll examples completed.")

# --- END OF FILE macro.py ---s
