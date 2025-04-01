# pymacrorecord_lib/macro_playback.py
from pynput import mouse, keyboard
from pynput.keyboard import Key, Listener as KeyboardListener  # Import Listener
from pynput.mouse import Button
import time
from time import sleep
from datetime import datetime
from threading import Thread  # Import Thread
import json  # Import json for PyMacroRecordLib error handling
import os  # Import os for PyMacroRecordLib path check (optional but good)

# Dictionary to map common key names to pynput Key objects
# Extend this as needed
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

    def __init__(self, settings, stop_key=Key.esc):  # Added default stop_key
        self.mouse_control = mouse.Controller()
        self.keyboard_control = keyboard.Controller()
        self.playback = False
        self.macro_events = {"events": []}
        self.settings = settings  # User settings object (not GUI-dependent)
        self.__play_macro_thread = None
        self._stop_listener = None
        self.stop_key = stop_key  # Configurable stop key, default Esc

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
            return key_string  # Return single character
        else:
            # Try to evaluate Key.xxx (use cautiously)
            try:
                key = eval(f"Key.{key_string}", {"Key": Key})
                if isinstance(key, Key):
                    return key
            except Exception:
                pass  # Ignore if eval fails
            print(
                f"Warning: Could not parse stop key '{key_string}'. Using default: {self.stop_key}"
            )
            return self.stop_key  # Return default if parsing fails

    def set_stop_key_from_string(self, key_string):
        """Set the stop key from a string representation."""
        parsed_key = self._parse_key_string(key_string)
        self.set_stop_key(parsed_key)

    def load_macro(self, macro_data):
        """Load macro events from a dictionary (parsed JSON)"""
        self.macro_events = macro_data

    def _on_press_stop_key(self, key):
        """Callback function for the keyboard listener."""
        # Using try/except because listener might catch attribute keys like Key.shift
        try:
            # Compare the pressed key with the designated stop key
            if key == self.stop_key:
                print(f"\nStop key ({self.stop_key}) pressed. Stopping playback...")
                self.stop_playback()
                # Optional: Stop the listener itself once the key is pressed
                # return False # Returning False from callback stops the listener
        except AttributeError:
            # Handle cases where 'key' might not have comparison attributes (like special keys)
            # For simple character keys or standard Key enum values, direct comparison usually works.
            # If comparing complex/modifier keys, more specific checks might be needed.
            pass
        except Exception as e:
            print(f"Error in stop key listener callback: {e}")

    def start_playback(self):
        """Start macro playback programmatically."""
        if not self.macro_events["events"]:
            print("No macro loaded or macro is empty.")
            return
        if self.playback:
            print("Playback already in progress.")
            return
        if self.__play_macro_thread and self.__play_macro_thread.is_alive():
            print("Playback thread is already running.")  # Added check
            return

        self.playback = True

        # Start the stop key listener *before* the playback thread
        # Ensure listener is stopped before creating a new one
        if self._stop_listener:
            print("Warning: Stop listener was already active. Stopping it.")
            self._stop_listener.stop()
            self._stop_listener = None

        # Create and start the listener in a separate thread
        # Use suppress=True if you don't want the listened keys to pass through to applications
        # However, for a stop key, we usually *do* want it to be processed normally if playback *isn't* stopped
        # So, suppress=False (default) or omit it.
        try:
            self._stop_listener = KeyboardListener(on_press=self._on_press_stop_key)
            self._stop_listener.start()
            print(f"Playback started. Press '{self.stop_key}' to stop.")
        except Exception as e:
            print(
                f"Error starting keyboard listener: {e}. Playback starting without stop key."
            )
            self.playback = False  # Abort playback start if listener fails critically
            return

        # Start the playback thread
        self.__play_macro_thread = Thread(target=self.__play_events, daemon=True)
        self.__play_macro_thread.start()

    def stop_playback(self):
        """Stop macro playback programmatically."""
        if self.playback:
            self.playback = False
            print("Playback stopping...")

            # Stop the keyboard listener
            if self._stop_listener:
                try:
                    self._stop_listener.stop()
                    # self._stop_listener.join() # Optional: wait for listener thread to finish
                except Exception as e:
                    print(f"Error stopping listener: {e}")
                finally:
                    self._stop_listener = None  # Clear the listener reference

            # Optional: Wait briefly for the playback thread to potentially see the flag
            # sleep(0.1) # Adjust if needed

            # Note: We don't forcefully join or kill the __play_macro_thread here.
            # It checks the `self.playback` flag internally and should exit gracefully.
            # The thread is a daemon, so it won't prevent program exit if the main thread finishes.
            print("Playback stopped.")
        # else: # Optional: Indicate if already stopped
        #     print("Playback is not currently running.")

    def __play_events(self):
        """Internal method to execute macro events in a thread."""
        user_settings = self.settings.get_config()  # Get settings directly
        click_func = {
            "leftClickEvent": Button.left,  # Use Button enum directly
            "rightClickEvent": Button.right,
            "middleClickEvent": Button.middle,
        }
        key_to_unpress = []
        repeat_times = (
            user_settings["Playback"]["Repeat"]["Times"]
            if user_settings["Playback"]["Repeat"]["For"] == 0
            else 1
        )  # Handle 'For' later
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
                seconds_to_wait += 86400  # Schedule for tomorrow

            if seconds_to_wait > 0:
                print(f"Scheduled start: Waiting for {seconds_to_wait:.2f} seconds...")
                # Allow stopping while waiting for scheduled start
                wait_interval = 0.5  # Check stop flag periodically
                while seconds_to_wait > 0 and self.playback:
                    sleep(min(wait_interval, seconds_to_wait))
                    seconds_to_wait -= wait_interval
                if not self.playback:  # Check if stopped during wait
                    print("Playback stopped before scheduled start.")
                    self.__unpress_everything(key_to_unpress)
                    # Ensure stop_playback is called to clean up listener if stopped via key
                    if (
                        self.playback
                    ):  # Check flag again, might have been set false by stop_key
                        self.stop_playback()
                    return
                print("Scheduled time reached. Starting playback.")

        # --- Repeat Loop ---
        repeat_count = 0
        while self.playback:  # Main loop condition based on playback flag
            repeat_count += 1
            # Check duration limit
            if repeat_duration and (time.time() - start_time) >= repeat_duration:
                print(f"Repeat duration ({repeat_duration}s) reached.")
                break
            # Check 'Times' limit if duration is not set
            if not repeat_duration and repeat_count > repeat_times:
                break  # Exit loop if repeat times exceeded

            print(f"--- Starting Repeat #{repeat_count} ---")

            for event_data in self.macro_events["events"]:
                if not self.playback:  # Check playback flag before each event
                    print("Playback stopped during event execution.")
                    self.__unpress_everything(key_to_unpress)
                    # No need to call self.stop_playback() here, it was called by the trigger
                    return  # Exit the thread cleanly

                # --- Calculate Sleep Time ---
                time_sleep = event_data["timestamp"]  # Default to recorded timestamp
                if user_settings["Others"]["Fixed_timestamp"] > 0:
                    time_sleep = (
                        user_settings["Others"]["Fixed_timestamp"] / 1000.0
                    )  # Use fixed (convert ms to s)
                else:
                    # Apply speed multiplier only if not using fixed timestamp
                    speed_multiplier = user_settings["Playback"]["Speed"]
                    if speed_multiplier > 0:  # Avoid division by zero or negative speed
                        time_sleep /= speed_multiplier
                    else:
                        time_sleep = 0  # Or handle invalid speed appropriately

                # Ensure sleep time is non-negative
                time_sleep = max(0, time_sleep)

                # --- Sleep with Interrupt Check ---
                # Break long sleeps into smaller chunks to check the stop flag
                sleep_interval = 0.05  # Check every 50ms
                remaining_sleep = time_sleep
                while remaining_sleep > 0 and self.playback:
                    sleep(min(sleep_interval, remaining_sleep))
                    remaining_sleep -= sleep_interval
                if not self.playback:  # Check if stopped during sleep
                    print("Playback stopped during sleep interval.")
                    self.__unpress_everything(key_to_unpress)
                    return  # Exit thread

                # --- Execute Event ---
                event_type = event_data["type"]

                try:  # Add try-except around pynput actions
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
                                    # Safer evaluation (restrict scope)
                                    key_to_press = eval(key_str, {"Key": Key})
                                except Exception as e:
                                    print(
                                        f"Warning: Could not evaluate key '{key_str}': {e}"
                                    )
                            elif key_str in vk_nb:
                                key_to_press = vk_nb[key_str]
                            else:
                                key_to_press = (
                                    key_str  # Assume character or already parsed
                                )

                            if key_to_press is not None:
                                if event_data["pressed"]:
                                    self.keyboard_control.press(key_to_press)
                                    if key_to_press not in key_to_unpress:
                                        key_to_unpress.append(key_to_press)
                                else:
                                    self.keyboard_control.release(key_to_press)
                                    if key_to_press in key_to_unpress:
                                        # Careful removal: only remove if actually released
                                        # A better approach might track press/release counts per key
                                        # For simplicity, removing on release here:
                                        try:
                                            key_to_unpress.remove(key_to_press)
                                        except ValueError:
                                            pass  # Key might have been released already or not tracked

                except Exception as e:  # Catch errors during event execution
                    print(f"Error during playback execution (Event: {event_data}): {e}")
                    # Decide whether to stop playback on error
                    print("Stopping playback due to error.")
                    self.__unpress_everything(key_to_unpress)
                    # Ensure stop_playback is called to clean listener
                    if self.playback:  # Check flag again
                        self.stop_playback()
                    return  # Exit thread

            # --- Delay Between Repeats ---
            repeat_delay = user_settings["Playback"]["Repeat"]["Delay"]
            is_last_repeat = (not repeat_duration and repeat_count >= repeat_times) or (
                repeat_duration and (time.time() - start_time) >= repeat_duration
            )

            if self.playback and repeat_delay > 0 and not is_last_repeat:
                print(f"--- Delaying for {repeat_delay}s before next repeat ---")
                # Sleep with interrupt check for the delay
                sleep_interval = 0.1  # Check every 100ms during delay
                remaining_delay = repeat_delay
                while remaining_delay > 0 and self.playback:
                    sleep(min(sleep_interval, remaining_delay))
                    remaining_delay -= sleep_interval
                if not self.playback:  # Check if stopped during delay
                    print("Playback stopped during repeat delay.")
                    self.__unpress_everything(key_to_unpress)
                    return  # Exit thread

        # --- End of Playback ---
        print("Playback loop finished.")
        self.__unpress_everything(key_to_unpress)
        # Call stop_playback() to ensure listener is stopped and flag is cleared
        # Only call if playback wasn't already stopped externally (e.g., by stop key)
        if self.playback:
            self.stop_playback()

    def __unpress_everything(self, key_to_unpress):
        """Release all tracked pressed keys and mouse buttons."""
        print("Releasing potentially held keys/buttons...")
        # Release tracked keys
        # Create a copy for safe iteration while potentially modifying the original list (though not strictly needed here)
        keys_to_release = list(key_to_unpress)
        for key in keys_to_release:
            try:
                self.keyboard_control.release(key)
                # Optionally clear from the tracking list after successful release
                # if key in key_to_unpress: key_to_unpress.remove(key)
            except Exception as e:  # Handle potential errors during release
                # print(f"Note: Error releasing key {key}: {e}") # Verbose logging if needed
                pass
        key_to_unpress.clear()  # Clear the tracking list

        # Release standard mouse buttons defensively
        try:
            self.mouse_control.release(Button.left)
        except Exception:
            pass
        try:
            self.mouse_control.release(Button.middle)
        except Exception:
            pass
        try:
            self.mouse_control.release(Button.right)
        except Exception:
            pass
        print("Key/Button release attempt complete.")


# Assuming user_settings is in utils relative to where this script might be run from
# Adjust the import path if necessary
try:
    from utils.user_settings import UserSettings
except ImportError:
    print("Warning: Could not import UserSettings from utils. Using placeholder.")

    # Create a dummy UserSettings if the real one is not available
    class UserSettings:
        def __init__(self, _):
            # Default settings matching the structure used in MacroPlayback
            self._config = {
                "Playback": {
                    "Speed": 1.0,
                    "Repeat": {
                        "Times": 1,
                        "For": 0,  # Duration in seconds (0 = use Times)
                        "Interval": 0,  # Not directly used in playback logic shown
                        "Scheduled": 0,  # Seconds since midnight
                        "Delay": 0,  # Delay between repeats
                    },
                },
                "Others": {"Fixed_timestamp": 0},  # Milliseconds (0 = use recorded)
            }

        def get_config(self):
            return self._config

        def change_settings(self, section, sub_section, key, value):
            if key:
                self._config[section][sub_section][key] = value
            elif sub_section:
                self._config[section][sub_section] = value
            else:
                self._config[section] = value
            print(f"Setting updated: {section}/{sub_section}/{key} = {value}")


class PyMacroRecordLib:
    def __init__(self):
        # Initialize settings
        try:
            # Adjust path if needed. Assume settings file is in parent dir's 'config'
            # config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
            self.settings = UserSettings(
                None
            )  # Pass None as main_app if GUI isn't used
        except Exception as e:
            print(f"Error initializing UserSettings: {e}. Using placeholder settings.")
            self.settings = UserSettings(None)  # Fallback to placeholder

        self.playback_engine = MacroPlayback(self.settings)
        self._active = False  # Track if playback is supposed to be running

    def load_macro_file(self, file_path):
        """Load a macro file (.pmr or .json)."""
        if not os.path.exists(file_path):
            print(f"Error: Macro file not found at: {file_path}")
            return False
        try:
            with open(file_path, "r") as f:
                macro_data = json.load(f)
            # Basic validation
            if (
                not isinstance(macro_data, dict)
                or "events" not in macro_data
                or not isinstance(macro_data["events"], list)
            ):
                print(
                    f"Error: Invalid macro format in: {file_path}. Missing 'events' list."
                )
                return False
            self.playback_engine.load_macro(macro_data)
            print(f"Macro file loaded from: {file_path}")
            return True
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in: {file_path}")
            return False
        except Exception as e:
            print(f"Error loading macro file: {e}")
            return False

    def start_playback(self):
        """Start the loaded macro playback."""
        if not self.playback_engine.macro_events["events"]:
            print("Cannot start playback: No macro loaded or macro is empty.")
            return
        if self.is_playing():
            print("Playback is already running.")
            return

        self._active = True
        self.playback_engine.start_playback()
        # We don't wait here, start_playback starts threads

    def stop_playback(self):
        """Stop the macro playback if it's running."""
        if not self.is_playing():
            print("Playback is not currently active.")
            return
        self._active = False
        self.playback_engine.stop_playback()

    def is_playing(self):
        """Check if playback is currently active."""
        # Check both the intended state (_active) and the engine's state
        return self._active and self.playback_engine.playback

    def wait_for_playback_to_finish(self, check_interval=0.2):
        """Wait until playback is no longer active."""
        if not self._active:
            # print("Playback not started, nothing to wait for.")
            return
        print("Waiting for playback to finish...")
        while self.is_playing():
            try:
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("\nWait interrupted by user (Ctrl+C). Stopping playback...")
                self.stop_playback()
                break
        print("Playback finished or was stopped.")
        self._active = False  # Ensure state is updated after waiting

    # --- Configuration Methods ---

    def set_stop_key(self, key_name):
        """Set the keyboard key to stop playback (e.g., 'esc', 'f12', 'q')."""
        self.playback_engine.set_stop_key_from_string(key_name)

    def set_playback_speed(self, speed):
        """Set the playback speed (multiplier)."""
        if 0.1 <= speed <= 10:  # Match original speed range
            self.settings.change_settings("Playback", "Speed", None, float(speed))
            print(f"Playback speed set to: {speed}")
        else:
            print("Error: Playback speed must be between 0.1 and 10.")

    def set_repeat_times(self, times):
        """Set the number of times to repeat the macro (use if duration is 0)."""
        times = int(times)
        if 1 <= times <= 100000000:  # Match original range
            self.settings.change_settings("Playback", "Repeat", "Times", times)
            # Ensure 'For' (duration) is off if setting 'Times'
            if self.settings.get_config()["Playback"]["Repeat"]["For"] != 0:
                self.settings.change_settings("Playback", "Repeat", "For", 0)
                print("Note: Repeat duration automatically set to 0.")
            print(f"Repeat times set to: {times}")
        else:
            print("Error: Repeat times must be between 1 and 100000000.")

    def set_repeat_for_duration(self, duration_sec):
        """Set the macro to repeat for a specific duration in seconds (0 to disable)."""
        duration_sec = float(duration_sec)
        if 0 <= duration_sec <= 86400 * 7:  # Allow up to a week, adjust as needed
            self.settings.change_settings("Playback", "Repeat", "For", duration_sec)
            # Ensure 'Times' is effectively ignored if duration is set
            if (
                duration_sec > 0
                and self.settings.get_config()["Playback"]["Repeat"]["Times"] != 1
            ):
                # We don't *need* to change Times, the logic prioritizes 'For', but we can reset it for clarity
                # self.settings.change_settings("Playback", "Repeat", "Times", 1)
                pass
            print(
                f"Repeat for duration set to: {duration_sec} seconds (0 means use 'Times')."
            )
        else:
            print("Error: Repeat duration must be between 0 and 604800 seconds.")

    def set_fixed_timestamp(self, timestamp_ms):
        """Set a fixed timestamp for all events in milliseconds (0 = use recorded)."""
        timestamp_ms = int(timestamp_ms)
        if 0 <= timestamp_ms <= 100000000:  # Match original range
            # Store as ms in settings, convert to seconds in playback logic
            self.settings.change_settings(
                "Others", "Fixed_timestamp", None, timestamp_ms
            )
            print(
                f"Fixed timestamp set to: {timestamp_ms} ms (0 means use recorded * speed)."
            )
        else:
            print("Error: Fixed timestamp must be between 0 and 100000000 ms.")

    # Interval repeat doesn't seem directly implemented in the playback loop, skipping for now
    # def set_interval_repeat(self, interval_sec): ...

    def set_scheduled_start(self, scheduled_sec_since_midnight):
        """Set scheduled start time in seconds since midnight (0 to disable)."""
        scheduled_sec_since_midnight = int(scheduled_sec_since_midnight)
        if 0 <= scheduled_sec_since_midnight <= 86400:
            self.settings.change_settings(
                "Playback", "Repeat", "Scheduled", scheduled_sec_since_midnight
            )
            print(
                f"Scheduled start set to: {scheduled_sec_since_midnight} seconds since midnight (0 = start immediately)."
            )
        else:
            print(
                "Error: Scheduled start must be between 0 and 86400 seconds since midnight."
            )

    def set_delay_between_repeats(self, delay_sec):
        """Set delay between repeats in seconds."""
        delay_sec = float(delay_sec)
        if 0 <= delay_sec <= 100000000:  # Match original range
            self.settings.change_settings("Playback", "Repeat", "Delay", delay_sec)
            print(f"Delay between repeats set to: {delay_sec} seconds.")
        else:
            print(
                "Error: Delay between repeats must be between 0 and 100000000 seconds."
            )


def play_macro(
    file_name, speed=1.0, repeat_times=1, delay_between_repeats=0.5, stop_key="esc"
):
    """
    Wrapper function to play a macro file with specified settings.

    Args:
        file_name (str): Path to the macro file
        speed (float): Playback speed multiplier
        repeat_times (int): Number of times to repeat the macro
        delay_between_repeats (float): Delay in seconds between repeats
        stop_key (str): Key to press to stop playback

    Returns:
        bool: True if playback completed successfully, False otherwise
    """
    if not os.path.exists(file_name):
        print(f"Macro file not found: {file_name}")
        return False

    pmr_lib = PyMacroRecordLib()

    # Configure playback
    pmr_lib.set_playback_speed(speed)
    pmr_lib.set_repeat_times(repeat_times)
    pmr_lib.set_delay_between_repeats(delay_between_repeats)
    pmr_lib.set_stop_key(stop_key)

    # Load and play the macro
    if pmr_lib.load_macro_file(file_name):
        print(f"Playing macro {file_name} at {speed}x speed, {repeat_times} times")
        pmr_lib.start_playback()

        # Wait for playback to finish
        pmr_lib.wait_for_playback_to_finish()
        print("Macro playback completed")
        return True
    else:
        print(f"Failed to load macro file: {file_name}")
        return False


# --- Example Usage ---
if __name__ == "__main__":
    import time  # Import time for example usage

    # --- Create a dummy macro file for testing ---
    dummy_macro_file = "checkpsmapet.pmr"
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
            {"type": "scrollEvent", "dx": 0, "dy": -2, "timestamp": 0.3},  # Scroll down
        ]
    }
    try:
        with open(dummy_macro_file, "w") as f:
            json.dump(dummy_macro_data, f, indent=4)
        print(f"Created dummy macro file: {dummy_macro_file}")
    except Exception as e:
        print(f"Error creating dummy macro file: {e}")
        dummy_macro_file = None  # Ensure we don't try to use it if creation failed

    # --- Initialize the library ---
    if dummy_macro_file:
        pmr_lib = PyMacroRecordLib()

        # --- Configure Playback ---
        print("\n--- Configuration ---")
        pmr_lib.set_playback_speed(1.5)
        pmr_lib.set_repeat_times(3)
        pmr_lib.set_delay_between_repeats(1.0)  # 1 second delay between repeats
        pmr_lib.set_stop_key("esc")  # Set Escape key to stop playback
        # pmr_lib.set_stop_key("f12") # Example: Set F12 to stop playback

        # --- Example 1: Load and play the dummy macro ---
        print(
            "\n--- Example 1: Play Macro (Press configured stop key to interrupt) ---"
        )
        if pmr_lib.load_macro_file(dummy_macro_file):
            pmr_lib.start_playback()

            # Keep the main thread alive while playback runs in background threads
            # Use wait_for_playback_to_finish for clean waiting
            pmr_lib.wait_for_playback_to_finish()

            # Or, for manual waiting loop:
            # while pmr_lib.is_playing():
            #     try:
            #         print(".", end="", flush=True)
            #         time.sleep(0.5)
            #     except KeyboardInterrupt: # Allow Ctrl+C to stop the *waiting* loop
            #         print("\nCtrl+C detected in main loop. Stopping playback...")
            #         pmr_lib.stop_playback()
            #         break
            # print("\nPlayback finished or stopped.")

        else:
            print("Failed to load macro file.")

        # --- Example 2: Demonstrate stopping programmatically ---
        # print("\n--- Example 2: Start playback and stop programmatically after 2 seconds ---")
        # if pmr_lib.load_macro_file(dummy_macro_file):
        #     pmr_lib.set_repeat_times(10) # Make it run longer
        #     pmr_lib.set_delay_between_repeats(0.1)
        #     pmr_lib.set_stop_key("f1") # Change stop key just for demo
        #
        #     pmr_lib.start_playback()
        #     print("Playback started. Will stop in 2 seconds...")
        #     time.sleep(2)
        #     pmr_lib.stop_playback()
        #     print("Programmatic stop requested.")
        #     # Wait a moment to ensure threads clean up
        #     time.sleep(0.5)

        # --- Clean up dummy file ---
        try:
            os.remove(dummy_macro_file)
            print(f"Cleaned up dummy macro file: {dummy_macro_file}")
        except Exception as e:
            print(f"Error removing dummy macro file: {e}")

    print("\nAll examples completed.")
