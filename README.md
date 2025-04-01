# ScreenScript

A Python library for recording, playing back, and automating keyboard and mouse actions. ScreenScript allows you to create, save, and replay macro sequences for automating repetitive tasks.

## Overview

ScreenScript provides a powerful automation tool that can:

-   Playback recorded macro files (.pmr)
-   Control playback speed
-   Repeat macro sequences a specific number of times or for a set duration
-   Configure delays between repeats
-   Stop playback with customizable hotkeys

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/screenscript.git
cd screenscript
```

2. Install the required dependencies:

```bash
pip install pynput
```

## Usage

### Basic Usage

```python
from macro import play_macro

# Play a macro file with default settings
play_macro("your_macro.pmr")

# Play with custom settings
play_macro(
    "your_macro.pmr",
    speed=1.5,              # 1.5x playback speed
    repeat_times=3,         # Repeat 3 times
    delay_between_repeats=0.5,  # 0.5 second delay between repeats
    stop_key="esc"          # Use Escape key to stop playback
)
```

### Advanced Usage

For more control, you can use the `PyMacroRecordLib` class directly:

```python
from macro import PyMacroRecordLib

# Initialize the library
pmr_lib = PyMacroRecordLib()

# Configure playback
pmr_lib.set_playback_speed(1.5)
pmr_lib.set_repeat_times(3)
pmr_lib.set_delay_between_repeats(1.0)
pmr_lib.set_stop_key("f12")  # Use F12 to stop playback

# Load and play a macro
if pmr_lib.load_macro_file("your_macro.pmr"):
    pmr_lib.start_playback()

    # Wait for playback to finish
    pmr_lib.wait_for_playback_to_finish()
    print("Macro playback completed")
```

## Configuration Options

ScreenScript provides several configuration options:

| Setting               | Method                                        | Description                                           |
| --------------------- | --------------------------------------------- | ----------------------------------------------------- |
| Playback Speed        | `set_playback_speed(speed)`                   | Set the playback speed multiplier (0.1-10)            |
| Repeat Times          | `set_repeat_times(times)`                     | Set number of times to repeat the macro (1-100000000) |
| Duration              | `set_repeat_for_duration(seconds)`            | Set the macro to repeat for a specific duration       |
| Fixed Timestamp       | `set_fixed_timestamp(milliseconds)`           | Override recorded event timing with fixed intervals   |
| Scheduled Start       | `set_scheduled_start(seconds_since_midnight)` | Schedule macro to start at a specific time            |
| Delay Between Repeats | `set_delay_between_repeats(seconds)`          | Set delay between macro repetitions                   |
| Stop Key              | `set_stop_key(key_name)`                      | Set the keyboard key to stop playback                 |

## File Format

Macro files (.pmr) are JSON files containing a list of events with timestamps. Each event represents a mouse movement, click, or keyboard action.

## Limitations

-   ScreenScript may not work properly with applications that implement anti-automation measures
-   Absolute screen coordinates are used, so macros may not work correctly across different screen resolutions

## License

This project is licensed under the MIT License - see the LICENSE file for details.
