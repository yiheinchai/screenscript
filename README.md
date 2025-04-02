# ScreenScript

`screenscript` is a Python-based automation tool designed to interact with graphical user interfaces (GUIs) through macro playback and screen text recognition (OCR). It's specifically tailored in this example to automate a repetitive workflow involving the Epic Electronic Health Record (EHR) system and logging results into an Excel spreadsheet.

The core functionality involves:

1.  Executing pre-recorded mouse and keyboard actions (macros).
2.  Reading text directly from the screen (using OCR) to verify actions or extract information.
3.  Combining these actions to perform complex tasks like searching for patient data, checking for specific results (e.g., "PSMA PET" scans), and recording findings.

## Core Features

-   **Macro Playback:** Executes sequences of mouse clicks, movements, keyboard presses stored in `.pmr` files (JSON format) using `pynput`.
-   **Screen OCR:** Uses `mss` for screen capture and `pytesseract` (interfacing with the Tesseract OCR engine) to find and read text within specified screen regions or entire monitors.
-   **Verification & Retry Logic:** Includes utilities (`do_and_verify`, `retry_till_false`) to ensure actions succeed by checking screen content via OCR, with built-in retries.
-   **Global Stop Key:** Implements a global keyboard listener (default: `Esc`) managed by a singleton `PyMacroRecordLib` instance, allowing the user to safely interrupt the automation process at any time.
-   **Modular Design:** Code is organized into modules for different concerns:
    -   `main.py`: Main execution loop orchestrating the workflow.
    -   `epic.py`: Functions specific to interacting with the Epic application UI.
    -   `excel.py`: Functions specific to interacting with Excel (likely via macros).
    -   `screenocr.py`: Screen capture and OCR functionality.
    -   `macro.py`: Macro playback engine and global listener management.
    -   `utils.py`: Helper functions for retries and verification.

## How it Works

1.  **Initialization:** The `main.py` script starts by getting an instance of the `PyMacroRecordLib` singleton. This singleton initializes the core macro playback engine and, crucially, starts a global keyboard listener thread watching for the stop key (e.g., `Esc`).
2.  **Main Loop:** The script enters a loop (e.g., iterating 800 times in the example).
3.  **Stop Check:** At the beginning of each iteration (and during macro waits), it checks if the global stop key has been pressed. If so, the loop terminates gracefully.
4.  **Epic Interaction (`epic.py`):**
    -   Calls functions like `find_patient`.
    -   These functions use `play_macro` to execute `.pmr` files containing recorded steps (e.g., clicking search buttons, typing patient info).
    -   OCR (`find_text_on_screen`) is used within `do_and_verify` or directly to confirm the state of the Epic application (e.g., "patient found", "search results displayed", "patient closed").
    -   Handles specific Epic dialogs like "Break-the-Glass".
5.  **Information Extraction:** If a patient is found, it searches for specific terms (e.g., "PSMA PET") using macros and verifies the results ("No results found for...") using OCR.
6.  **Excel Logging (`excel.py`):** Based on whether the "PSMA PET" information was found, a corresponding macro (`log_yes_psma.pmr`, `log_no_psma.pmr`, `log_none_psma.pmr`) is played to log the result in an Excel sheet.
7.  **Cleanup:** The patient record in Epic is closed using another macro (`close_patient.pmr`), again verified by OCR.
8.  **Loop Continuation:** The process repeats for the next iteration unless stopped.

## Prerequisites

1.  **Python 3:** Ensure Python 3.x is installed.
2.  **Tesseract OCR Engine:** This is **required** for `screenocr.py` to function.
    -   Installation instructions: [Tesseract Installation Guide](https://github.com/tesseract-ocr/tesseract#installing-tesseract)
    -   After installation, ensure the `tesseract` command is available in your system's PATH, or you may need to explicitly set the path within `screenocr.py`:
        ```python
        # Example for Windows, adjust the path as needed
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        ```
3.  **Python Libraries:** Install the required libraries. Create a `requirements.txt` file with the following content:
    ```txt
    pynput
    mss
    Pillow
    pytesseract
    ```
    Then install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Setup / Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd screenscript
    ```
2.  **Install Prerequisites:** Follow the steps in the [Prerequisites](#prerequisites) section (Python, Tesseract, Python libraries).
3.  **Configure Paths:**
    -   **CRITICAL:** Open `src/epic.py` and `src/excel.py`. Modify the `BASE_PATH` variable to point to the _absolute path_ of the `src` directory within _your_ cloned repository location.
    ```python
    # Example: Change this line in both files
    BASE_PATH = "/path/to/your/cloned/screenscript/src/"
    ```
4.  **Record Macros:** The `.pmr` files referenced in `epic.py` and `excel.py` (e.g., `find_patient.pmr`, `log_yes_psma.pmr`) are **not included** and **must be recorded** using a macro recording tool compatible with the JSON format used by `macro.py`. These recordings must precisely match the UI interactions needed on _your specific system_ with Epic and Excel open and positioned correctly. Place the recorded `.pmr` files inside the `src` directory (or update the paths in the code if you place them elsewhere).
5.  **Adjust Screen Regions:** The coordinates used in `find_text_on_screen` calls (e.g., `region=(480, 605, 677, 650)`) are highly dependent on screen resolution and window positioning. You will likely need to adjust these coordinates to match the locations of text elements on your screen. Use a screen coordinate tool to find the correct (left, top, right, bottom) values for each region.

## Usage

1.  Ensure the target applications (Epic, Excel) are open and positioned as expected when the macros were recorded.
2.  Navigate to the `screenscript` directory in your terminal.
3.  Run the main script:
    ```bash
    python main.py
    ```
4.  The script will start executing the workflow defined in `main.py`.
5.  **To stop the script at any time, press the `Esc` key.** The script should detect this and terminate the main loop gracefully after finishing any in-progress macro step.

## Macro Files (`.pmr`)

-   These files contain the recorded sequences of mouse and keyboard events in JSON format.
-   They are the core drivers for interacting with the GUI.
-   **They are highly specific to:**
    -   The screen resolution.
    -   The exact layout and version of the target application (Epic, Excel).
    -   The position of the application windows.
-   You need a separate macro recording tool to generate these files based on your specific environment. The `macro.py` module is primarily for _playback_.

## Important Considerations & Limitations

-   **Fragility:** GUI automation via macros is inherently fragile. Changes to the UI layout, resolution, window positions, or application updates can easily break the scripts.
-   **Hardcoded Paths:** The `BASE_PATH` needs to be set manually.
-   **Hardcoded Coordinates:** Screen regions for OCR (`region=...`) must be adjusted for your specific display setup.
-   **Timing:** The `speed` parameter in `play_macro` and internal delays might need tuning depending on system responsiveness.
-   **Error Handling:** While there's a global stop key and some basic exception handling in `main.py`, complex error recovery (e.g., unexpected pop-ups) is not implemented.
-   **Ethical Use:** Ensure you have the necessary permissions and comply with all policies when automating interactions with sensitive systems like EHRs.

## Dependencies

-   [pynput](https://pypi.org/project/pynput/): For controlling and monitoring input devices (keyboard, mouse).
-   [mss](https://pypi.org/project/mss/): For fast cross-platform screen capture.
-   [Pillow](https://pypi.org/project/Pillow/): Python Imaging Library (Fork) used for image manipulation (required by `mss` and `pytesseract`).
-   [pytesseract](https://pypi.org/project/pytesseract/): Python wrapper for Google's Tesseract-OCR Engine.
-   [Tesseract OCR](https://github.com/tesseract-ocr/tesseract): The underlying OCR engine (external dependency).

## License

MIT License
Copyright (c) [2025] [Yi Hein Chai]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
