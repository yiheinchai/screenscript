# --- START OF FILE macro.py ---

# pymacrorecord_lib/macro_playback.py
from pynput import mouse, keyboard
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button
import time
from time import sleep
from datetime import datetime
from threading import (
    Thread,
    RLock,
)  # Import RLock for thread safety if needed (added precaution)
import json
import os

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
    "win": Key.cmd,  # Alias for windows/command key
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
    # 'home': Key.home, 'end': Key.end, 'insert': Key.insert,
    "caps_lock": Key.caps_lock,
    # Add other keys if required
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


class MacroPlayback:
    """Core playback logic extracted from the GUI Macro class"""

    def __init__(self, settings, stop_key=Key.esc):
        self.mouse_control = mouse.Controller()
        self.keyboard_control = keyboard.Controller()
        self.playback = False
        self.macro_events = {"events": []}
        self.settings = settings
        self.__play_macro_thread = None
        self._stop_listener = None
        self.stop_key = stop_key
        self._lock = (
            RLock()
        )  # Lock for thread safety on shared state like self.playback

    def set_stop_key(self, key):
        """Set the key used to stop playback."""
        self.stop_key = key
        print(f"Stop key set to: {key}")

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
                f"Warning: Could not parse stop key '{key_string}'. Using default: {self.stop_key}"
            )
            return self.stop_key

    def set_stop_key_from_string(self, key_string):
        """Set the stop key from a string representation."""
        parsed_key = self._parse_key_string(key_string)
        self.set_stop_key(parsed_key)

    def load_macro(self, macro_data):
        """Load macro events from a dictionary (parsed JSON)"""
        self.macro_events = macro_data

    def _on_press_stop_key(self, key):
        """Callback function for the keyboard listener."""
        try:
            if key == self.stop_key:
                print(
                    f"\nStop key ({self.stop_key}) pressed. Attempting to stop playback..."
                )
                # Use the lock to ensure stop_playback is called safely
                # Call stop_playback in a separate thread to avoid blocking the listener thread
                Thread(target=self.stop_playback, daemon=True).start()
                # Optionally stop the listener itself immediately if desired
                # return False # Returning False stops the listener thread
        except AttributeError:
            pass
        except Exception as e:
            print(f"Error in stop key listener callback: {e}")

    def start_playback(self):
        """Start macro playback programmatically."""
        with self._lock:  # Ensure thread-safe check/set of playback flag
            if not self.macro_events["events"]:
                print("No macro loaded or macro is empty.")
                return False
            if self.playback:
                print("Playback already in progress.")
                return False
            if self.__play_macro_thread and self.__play_macro_thread.is_alive():
                print(
                    "Playback thread is already running (previous run not fully stopped?)."
                )
                return False  # Prevent starting if thread already exists

            self.playback = True  # Set flag *before* starting threads

        # --- Stop Listener Management ---
        # Stop existing listener *before* starting a new one
        if self._stop_listener and self._stop_listener.is_alive():
            print("Stopping existing keyboard listener...")
            try:
                self._stop_listener.stop()
                # Give listener thread a moment to stop
                # self._stop_listener.join(timeout=0.5) # Optional join with timeout
            except Exception as e:
                print(f"Error stopping previous listener: {e}")
            finally:
                self._stop_listener = None

        # Start the stop key listener
        try:
            # Use suppress=False so the stop key might still work in other apps if needed
            self._stop_listener = KeyboardListener(
                on_press=self._on_press_stop_key, daemon=True
            )
            self._stop_listener.start()
            print(f"Playback starting. Press '{self.stop_key}' to stop.")
        except Exception as e:
            print(f"Error starting keyboard listener: {e}. Playback aborted.")
            with self._lock:
                self.playback = False  # Reset flag if listener fails
            return False  # Indicate failure

        # --- Playback Thread ---
        # Ensure previous thread object is cleared if it finished/died
        self.__play_macro_thread = None
        self.__play_macro_thread = Thread(target=self.__play_events, daemon=True)
        self.__play_macro_thread.start()
        return True  # Indicate success

    def stop_playback(self):
        """Stop macro playback programmatically. Thread-safe."""
        print("Stop playback requested...")
        should_stop_listener = False
        with self._lock:
            if not self.playback:
                print("Playback is not currently marked as active.")
                return  # Already stopped or stopping

            print("Setting playback flag to False.")
            self.playback = False  # Set flag to signal the playback thread
            should_stop_listener = True  # Mark listener to be stopped outside the lock

        # Stop the keyboard listener *after* releasing the lock
        if should_stop_listener and self._stop_listener:
            print("Stopping keyboard listener...")
            listener_to_stop = self._stop_listener  # Copy reference
            self._stop_listener = None  # Clear the instance variable quickly
            try:
                listener_to_stop.stop()
                # listener_to_stop.join(timeout=0.5) # Optional join
                print("Keyboard listener stop requested.")
            except Exception as e:
                print(f"Error stopping listener: {e}")

        # Note: We don't forcefully join the __play_macro_thread here.
        # It checks the `self.playback` flag internally and should exit.
        # Being a daemon thread helps ensure it doesn't block program exit.
        print("Playback stop process initiated.")

    def __play_events(self):
        """Internal method to execute macro events in a thread."""
        # --- Initialization before loop ---
        user_settings = self.settings.get_config()
        click_func = {
            "leftClickEvent": Button.left,
            "rightClickEvent": Button.right,
            "middleClickEvent": Button.middle,
        }
        key_to_unpress = []  # Tracks keys pressed *within this playback run*
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
                    with self._lock:  # Check playback flag safely
                        if not self.playback:
                            break
                    sleep(min(wait_interval, seconds_to_wait))
                    seconds_to_wait -= wait_interval

                with self._lock:  # Final check before proceeding
                    if not self.playback:
                        print("Playback stopped before scheduled start.")
                        self.__unpress_everything(key_to_unpress)
                        # No need to call stop_playback again, it was triggered externally
                        return  # Exit thread

                print("Scheduled time reached. Starting playback.")

        # --- Repeat Loop ---
        repeat_count = 0
        loop_running = True
        while loop_running:
            # --- Check Stop Condition AT START of loop iteration ---
            with self._lock:
                if not self.playback:
                    print("Playback flag is false at start of repeat loop.")
                    loop_running = False
                    break  # Exit the while loop

            repeat_count += 1
            # Check duration limit
            if repeat_duration and (time.time() - start_time) >= repeat_duration:
                print(f"Repeat duration ({repeat_duration}s) reached.")
                loop_running = False
                break
            # Check 'Times' limit if duration is not set
            if not repeat_duration and repeat_count > repeat_times:
                print(f"Repeat times ({repeat_times}) reached.")
                loop_running = False
                break

            print(f"--- Starting Repeat #{repeat_count} ---")

            # --- Event Loop ---
            for event_data in self.macro_events["events"]:
                # --- Check Stop Condition BEFORE EACH event ---
                with self._lock:
                    if not self.playback:
                        print("Playback stopped during event execution.")
                        loop_running = False
                        break  # Exit the inner for loop

                # Calculate Sleep Time (apply fixed or speed multiplier)
                time_sleep = event_data["timestamp"]
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
                    with self._lock:  # Check playback flag safely during sleep
                        if not self.playback:
                            break
                    sleep(min(sleep_interval, remaining_sleep))
                    remaining_sleep -= sleep_interval

                with self._lock:  # Final check after sleep before event execution
                    if not self.playback:
                        print("Playback stopped during sleep interval.")
                        loop_running = False
                        break  # Exit the inner for loop

                # --- Execute Event ---
                if not loop_running:
                    break  # Already decided to stop

                event_type = event_data["type"]
                try:
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
                                        f"Warning: Could not evaluate key '{key_str}': {e}"
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
                                            pass  # Ignore if already removed
                except Exception as e:
                    print(f"Error during playback execution (Event: {event_data}): {e}")
                    print("Stopping playback due to error.")
                    loop_running = False  # Signal to exit loops
                    # Trigger the main stop mechanism to ensure cleanup
                    Thread(target=self.stop_playback, daemon=True).start()
                    break  # Exit inner for loop

            # --- Check Stop Condition AFTER event loop ---
            if not loop_running:
                break  # Exit the outer while loop

            # --- Delay Between Repeats ---
            repeat_delay = user_settings["Playback"]["Repeat"]["Delay"]
            is_last_repeat = (not repeat_duration and repeat_count >= repeat_times) or (
                repeat_duration and (time.time() - start_time) >= repeat_duration
            )

            if repeat_delay > 0 and not is_last_repeat:
                print(f"--- Delaying for {repeat_delay}s before next repeat ---")
                sleep_interval = 0.1
                remaining_delay = repeat_delay
                while remaining_delay > 0:
                    with self._lock:  # Check stop flag during delay
                        if not self.playback:
                            break
                    sleep(min(sleep_interval, remaining_delay))
                    remaining_delay -= sleep_interval

                with self._lock:  # Final check after delay
                    if not self.playback:
                        print("Playback stopped during repeat delay.")
                        loop_running = False
                        # No break needed here, loop condition will handle it

        # --- End of Playback ---
        print("Playback loop finished or was stopped.")
        self.__unpress_everything(
            key_to_unpress
        )  # Release keys pressed during this run

        # Ensure playback flag is false and listener is handled by calling stop_playback
        # This is important if the loop finished naturally (not via stop key/error)
        print("Ensuring final cleanup...")
        # Call stop_playback again to ensure listener is stopped if loop finished naturally
        # Check the flag *before* calling stop to avoid redundant messages if already stopped
        stop_needed = False
        with self._lock:
            if self.playback:  # If it wasn't set to False by stop_key/error
                stop_needed = True
        if stop_needed:
            self.stop_playback()  # This will set self.playback=False and stop listener

        print("Playback thread terminating.")

    def __unpress_everything(self, key_to_unpress):
        """Release keys tracked *during this specific playback run*."""
        print(f"Releasing {len(key_to_unpress)} potentially held keys...")
        # Release tracked keys
        keys_released_count = 0
        # Iterate over a copy in case of modification issues (though remove should handle it)
        for key in list(key_to_unpress):
            try:
                self.keyboard_control.release(key)
                keys_released_count += 1
                # Keep track of keys actually pressed during this run, attempt removal
                try:
                    key_to_unpress.remove(key)
                except ValueError:
                    pass  # Already removed, shouldn't happen if iterating list copy but safe
            except Exception as e:
                # print(f"Note: Error releasing key {key}: {e}") # Optional verbose log
                pass
        print(f"Attempted release for {keys_released_count} keys.")
        # It's generally safer *not* to blindly release mouse buttons here,
        # as the macro should have handled releases. Blind releases might
        # interfere if the user manually holds a button.


# --- Dummy UserSettings (Keep as is or import your actual class) ---
try:
    from utils.user_settings import UserSettings
except ImportError:
    print("Warning: Could not import UserSettings from utils. Using placeholder.")

    class UserSettings:
        # ... (Keep the dummy UserSettings class definition as before) ...
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
            self._lock = RLock()  # Add lock for settings access if needed

        def get_config(self):
            with self._lock:  # Use lock if settings could be read/written concurrently
                # Return a deep copy if necessary to prevent modification? For now, return direct dict.
                return self._config

        def change_settings(self, section, sub_section, key, value):
            with self._lock:  # Lock during modification
                try:
                    if key:
                        self._config[section][sub_section][key] = value
                    elif sub_section:
                        self._config[section][sub_section] = value
                    else:
                        self._config[section] = value
                    # print(f"Setting updated: {section}/{sub_section}/{key} = {value}") # Less verbose
                except KeyError:
                    print(f"Error: Invalid setting path {section}/{sub_section}/{key}")


# --- PyMacroRecordLib as Singleton ---
class PyMacroRecordLib:
    _instance = None
    _lock = RLock()  # Class level lock for thread-safe singleton instantiation

    def __new__(cls, *args, **kwargs):
        # Double-checked locking for thread safety
        if cls._instance is None:
            with cls._lock:
                # Check again inside the lock in case another thread created it
                # while the first thread was waiting for the lock
                if cls._instance is None:
                    print("Creating new PyMacroRecordLib singleton instance.")
                    cls._instance = super().__new__(cls)
                    # Mark as uninitialized *before* calling __init__
                    cls._instance._initialized = False
        # else:
        # print("Returning existing PyMacroRecordLib singleton instance.") # Can be noisy
        return cls._instance

    def __init__(self):
        """
        Initialize the singleton instance *only once*.
        Subsequent calls to PyMacroRecordLib() will return the existing
        instance, and this __init__ will detect it's already initialized.
        """
        # Prevent re-initialization using an instance flag
        if getattr(self, "_initialized", False):
            # print("Singleton already initialized.") # Can be noisy
            return

        print("Initializing PyMacroRecordLib singleton...")
        with self._lock:  # Protect initialization attributes
            # Initialize settings
            try:
                self.settings = UserSettings(None)
            except Exception as e:
                print(
                    f"Error initializing UserSettings: {e}. Using placeholder settings."
                )
                self.settings = UserSettings(None)  # Fallback

            # Initialize playback engine *once*
            self.playback_engine = MacroPlayback(self.settings)
            self._active = False  # Track intended playback state

            # Mark as initialized *after* all initialization is done
            self._initialized = True
            print("Singleton initialization complete.")

    # --- Core Methods (operate on the single playback_engine) ---

    def load_macro_file(self, file_path):
        """Load a macro file (.pmr or .json)."""
        if not os.path.exists(file_path):
            print(f"Error: Macro file not found at: {file_path}")
            return False
        try:
            with open(file_path, "r") as f:
                macro_data = json.load(f)
            if (
                not isinstance(macro_data, dict)
                or "events" not in macro_data
                or not isinstance(macro_data["events"], list)
            ):
                print(f"Error: Invalid macro format in: {file_path}.")
                return False
            # Load into the single playback engine
            self.playback_engine.load_macro(macro_data)
            print(f"Macro file loaded into singleton engine from: {file_path}")
            return True
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in: {file_path}")
            return False
        except Exception as e:
            print(f"Error loading macro file: {e}")
            return False

    def start_playback(self):
        """Start the loaded macro playback using the singleton engine."""
        # Check intended state first
        if self._active:
            print("Playback start requested, but already marked as active.")
            # Optionally check engine state too: if not self.playback_engine.playback: ...
            return

        print("Attempting to start playback via singleton engine...")
        # Call the engine's start method
        success = self.playback_engine.start_playback()
        if success:
            self._active = True  # Mark as active only if engine start was successful
            print("Playback successfully started.")
        else:
            self._active = False  # Ensure state reflects failed start
            print("Playback failed to start.")

    def stop_playback(self):
        """Stop the macro playback if it's running using the singleton engine."""
        # Check intended state first
        if not self._active:
            print("Stop playback requested, but not marked as active.")
            # Optionally check engine state too: if self.playback_engine.playback: ...
            # return # Maybe don't return, allow stopping engine even if _active is false?

        print("Attempting to stop playback via singleton engine...")
        # Call the engine's stop method
        self.playback_engine.stop_playback()
        self._active = False  # Always mark as inactive after requesting stop
        print("Playback stop requested.")

    def is_playing(self):
        """Check if playback is currently active via the singleton engine."""
        # Primarily rely on the engine's actual state flag
        engine_playing = self.playback_engine.playback
        # Optionally sync the internal _active flag if needed, though engine's flag is more real-time
        # self._active = engine_playing
        return engine_playing

    def wait_for_playback_to_finish(self, check_interval=0.2):
        """Wait until playback (via singleton engine) is no longer active."""
        # Check engine state directly
        if not self.playback_engine.playback and not self._active:
            # print("Playback not running, nothing to wait for.")
            return

        print("Waiting for playback to finish...")
        while self.playback_engine.playback:  # Check the engine's flag
            try:
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("\nWait interrupted by user (Ctrl+C). Requesting stop...")
                self.stop_playback()  # Use the proper stop method
                break  # Exit wait loop

        print("Playback finished or was stopped.")
        self._active = False  # Ensure state reflects finished/stopped playback

    # --- Configuration Methods (modify settings on the single instance) ---

    def set_stop_key(self, key_name):
        """Set the keyboard key to stop playback (e.g., 'esc', 'f12', 'q')."""
        self.playback_engine.set_stop_key_from_string(key_name)

    def set_playback_speed(self, speed):
        """Set the playback speed (multiplier)."""
        if 0.1 <= speed <= 10:
            self.settings.change_settings("Playback", "Speed", None, float(speed))
            # print(f"Playback speed set to: {speed}") # Less verbose
        else:
            print("Error: Playback speed must be between 0.1 and 10.")

    def set_repeat_times(self, times):
        """Set the number of times to repeat the macro (use if duration is 0)."""
        times = int(times)
        if 1 <= times <= 100000000:
            self.settings.change_settings("Playback", "Repeat", "Times", times)
            if self.settings.get_config()["Playback"]["Repeat"]["For"] != 0:
                self.settings.change_settings("Playback", "Repeat", "For", 0)
                # print("Note: Repeat duration automatically set to 0.")
            # print(f"Repeat times set to: {times}")
        else:
            print("Error: Repeat times must be between 1 and 100000000.")

    def set_repeat_for_duration(self, duration_sec):
        """Set the macro to repeat for a specific duration in seconds (0 to disable)."""
        duration_sec = float(duration_sec)
        if 0 <= duration_sec <= 86400 * 7:
            self.settings.change_settings("Playback", "Repeat", "For", duration_sec)
            # print(f"Repeat for duration set to: {duration_sec} seconds (0 means use 'Times').")
        else:
            print("Error: Repeat duration must be between 0 and 604800 seconds.")

    def set_fixed_timestamp(self, timestamp_ms):
        """Set a fixed timestamp for all events in milliseconds (0 = use recorded)."""
        timestamp_ms = int(timestamp_ms)
        if 0 <= timestamp_ms <= 100000000:
            self.settings.change_settings(
                "Others", "Fixed_timestamp", None, timestamp_ms
            )
            # print(f"Fixed timestamp set to: {timestamp_ms} ms (0 means use recorded * speed).")
        else:
            print("Error: Fixed timestamp must be between 0 and 100000000 ms.")

    def set_scheduled_start(self, scheduled_sec_since_midnight):
        """Set scheduled start time in seconds since midnight (0 to disable)."""
        scheduled_sec_since_midnight = int(scheduled_sec_since_midnight)
        if 0 <= scheduled_sec_since_midnight <= 86400:
            self.settings.change_settings(
                "Playback", "Repeat", "Scheduled", scheduled_sec_since_midnight
            )
            # print(f"Scheduled start set to: {scheduled_sec_since_midnight} seconds since midnight.")
        else:
            print("Error: Scheduled start must be between 0 and 86400.")

    def set_delay_between_repeats(self, delay_sec):
        """Set delay between repeats in seconds."""
        delay_sec = float(delay_sec)
        if 0 <= delay_sec <= 100000000:
            self.settings.change_settings("Playback", "Repeat", "Delay", delay_sec)
            # print(f"Delay between repeats set to: {delay_sec} seconds.")
        else:
            print("Error: Delay must be between 0 and 100000000 seconds.")


# --- Wrapper Function (play_macro) ---
# This function now uses the singleton implicitly
def play_macro(
    file_name, speed=1.0, repeat_times=1, delay_between_repeats=0.5, stop_key="esc"
):
    """
    Wrapper function to play a macro file using the singleton PyMacroRecordLib instance.
    """
    if not os.path.exists(file_name):
        print(f"Macro file not found: {file_name}")
        return False

    # Get the singleton instance
    pmr_lib = PyMacroRecordLib()  # This will always return the *same* instance

    # Configure playback settings on the singleton instance for this specific call
    pmr_lib.set_playback_speed(speed)
    pmr_lib.set_repeat_times(repeat_times)
    pmr_lib.set_delay_between_repeats(delay_between_repeats)
    pmr_lib.set_stop_key(stop_key)  # Set/confirm stop key

    # Load and play the macro using the singleton instance
    if pmr_lib.load_macro_file(file_name):
        print(f"Playing macro '{os.path.basename(file_name)}' via singleton...")
        pmr_lib.start_playback()

        # Wait for playback to finish using the singleton's wait method
        pmr_lib.wait_for_playback_to_finish()
        # print("Macro playback completed via singleton.") # wait_for... prints messages
        return True
    else:
        print(f"Failed to load macro file: {file_name}")
        return False


# --- Example Usage (remains the same) ---
if __name__ == "__main__":
    import time

    # --- Create a dummy macro file for testing ---
    dummy_macro_file = "checkpsmapet.pmr"
    # ... (keep dummy_macro_data definition as before) ...
    dummy_macro_data = {
        "events": [
            {"type": "cursorMove", "x": 100, "y": 100, "timestamp": 0.5},
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
            {"type": "keyboardEvent", "key": "a", "pressed": True, "timestamp": 0.2},
            {"type": "keyboardEvent", "key": "a", "pressed": False, "timestamp": 0.1},
            {"type": "cursorMove", "x": 300, "y": 300, "timestamp": 0.5},
            {
                "type": "keyboardEvent",
                "key": "Key.enter",
                "pressed": True,
                "timestamp": 0.2,
            },
            {
                "type": "keyboardEvent",
                "key": "Key.enter",
                "pressed": False,
                "timestamp": 0.1,
            },
            {"type": "scrollEvent", "dx": 0, "dy": -2, "timestamp": 0.3},
        ]
    }
    try:
        with open(dummy_macro_file, "w") as f:
            json.dump(dummy_macro_data, f, indent=4)
        print(f"Created dummy macro file: {dummy_macro_file}")
    except Exception as e:
        print(f"Error creating dummy macro file: {e}")
        dummy_macro_file = None

    if dummy_macro_file:
        # --- Initialize the library (implicitly gets singleton) ---
        print("\n--- Initializing/Getting Singleton Instance ---")
        # First call implicitly creates/initializes the singleton
        pmr_lib_1 = PyMacroRecordLib()
        print(f"Instance 1 ID: {id(pmr_lib_1)}")

        # --- Configure Playback (operates on the single instance) ---
        print("\n--- Configuration ---")
        pmr_lib_1.set_playback_speed(1.5)
        pmr_lib_1.set_repeat_times(3)
        pmr_lib_1.set_delay_between_repeats(1.0)
        pmr_lib_1.set_stop_key("esc")

        # --- Demonstrate Singleton ---
        print("\n--- Getting Singleton Instance Again ---")
        # Second call returns the *same* instance
        pmr_lib_2 = PyMacroRecordLib()
        print(f"Instance 2 ID: {id(pmr_lib_2)}")
        print(f"Instances are the same: {id(pmr_lib_1) == id(pmr_lib_2)}")
        # Settings are persistent on the singleton
        print(
            f"Speed on instance 2: {pmr_lib_2.settings.get_config()['Playback']['Speed']}"
        )

        # --- Example 1: Play Macro using the wrapper function ---
        # The wrapper function `play_macro` will internally get the same singleton instance
        print("\n--- Example 1: Play Macro via Wrapper (Press Esc to interrupt) ---")
        play_macro(
            dummy_macro_file,
            speed=1.0,
            repeat_times=2,
            delay_between_repeats=0.5,
            stop_key="f1",
        )  # Override settings for this call

        print("\n--- Example 2: Play Macro directly using instance methods ---")
        # You can still use the instance directly if preferred
        pmr_lib_1.set_playback_speed(2.0)  # Change speed again
        pmr_lib_1.set_repeat_times(1)
        pmr_lib_1.set_stop_key("esc")  # Back to Esc
        if pmr_lib_1.load_macro_file(dummy_macro_file):
            pmr_lib_1.start_playback()
            pmr_lib_1.wait_for_playback_to_finish()

        # --- Clean up dummy file ---
        try:
            os.remove(dummy_macro_file)
            print(f"Cleaned up dummy macro file: {dummy_macro_file}")
        except Exception as e:
            print(f"Error removing dummy macro file: {e}")

    print("\nAll examples completed.")

# --- END OF FILE macro.py ---
