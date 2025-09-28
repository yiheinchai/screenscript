import mss
import pytesseract
from PIL import Image
import sys
import re

# --- Configuration (Optional but Recommended) ---
# On Windows, you might need to uncomment and set the correct path:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# On Linux/macOS, Tesseract is often found automatically if installed and in the system PATH.


def check_tesseract_installed():
    """Checks if the Tesseract OCR engine is accessible."""
    try:
        pytesseract.get_tesseract_version()
        # print("Tesseract is installed and accessible.") # Optional: uncomment for verbose confirmation
        return True
    except pytesseract.TesseractNotFoundError:
        print("\n--- TESSERACT ERROR ---", file=sys.stderr)
        print(
            "Tesseract OCR engine not found or not in your system's PATH.",
            file=sys.stderr,
        )
        print("Please install Tesseract for your OS:", file=sys.stderr)
        print(
            "  - Windows/macOS/Linux: https://github.com/tesseract-ocr/tesseract#installing-tesseract",
            file=sys.stderr,
        )
        print(
            "If installed but not found, you might need to set the path explicitly in the script:",
            file=sys.stderr,
        )
        print(
            "# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' # Example for Windows",
            file=sys.stderr,
        )
        print("---", file=sys.stderr)
        return False
    except Exception as e:
        print(
            f"An unexpected error occurred while checking for Tesseract: {e}",
            file=sys.stderr,
        )
        return False


def capture_and_ocr(
    target_phrase="PSMA PET",
    monitor_num=1,
    debug_save=False,
    region=None,
    use_regex=False,
):
    """
    Internal helper: Takes a screenshot of a specified monitor or region, performs OCR,
    and checks if a target phrase or regex pattern exists.

    Args:
        target_phrase (str): The text or regex pattern to search for (case-insensitive).
        monitor_num (int): The monitor number (1=primary, 2=secondary, 0=all).
        debug_save (bool): If True, saves the screenshot for debugging.
        region (tuple, optional): Region to capture as (left, top, right, bottom) coordinates.
                                    If provided, will only capture this region.
        use_regex (bool): If True, interprets target_phrase as a regex pattern.

    Returns:
        tuple: (bool, str or None)
                - bool: True if the target_phrase or regex pattern was found, False otherwise.
                - str: The full extracted text if successful, None if an error occurred
                        during screenshot or OCR.
    """
    print(
        f"Attempting to capture {'region' if region else f'monitor {monitor_num}'}..."
    )
    try:
        with mss.mss() as sct:
            # If region is specified, use it directly
            if region:
                left, top, right, bottom = region
                monitor = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top,
                }
                print(f"Capturing region: {region}")
            else:
                # Adjust monitor selection logic slightly for clarity
                monitors = sct.monitors
                if monitor_num < 0 or monitor_num >= len(monitors):
                    print(
                        f"Warning: Monitor number {monitor_num} is invalid. Available monitors: {len(monitors)} (0=all, 1=primary, ...). Falling back to monitor 1 (primary).",
                        file=sys.stderr,
                    )
                    monitor_num = 1  # Default to primary
                    if monitor_num >= len(monitors):  # If only monitor 0 (all) exists
                        monitor_num = 0

                if monitor_num == 0 and len(monitors) > 1:
                    print(
                        "Capturing all monitors combined. This might yield unexpected OCR results."
                    )
                elif monitor_num == 1 and len(monitors) > 1:
                    print("Capturing primary monitor.")
                elif monitor_num > 0:
                    print(f"Capturing monitor {monitor_num}.")
                else:  # Only monitor 0 exists
                    print("Capturing the only available monitor.")

                monitor = monitors[monitor_num]

            # Capture the screen
            sct_img = sct.grab(monitor)
            print("Screenshot captured.")

            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            if debug_save:
                try:
                    filename = "screenshot_debug.png"
                    img.save(filename)
                    print(f"Screenshot saved for debugging as {filename}")
                except Exception as save_e:
                    print(
                        f"Warning: Could not save debug screenshot: {save_e}",
                        file=sys.stderr,
                    )

    except Exception as e:
        print(f"Error taking screenshot: {e}", file=sys.stderr)
        return False, None  # Indicate failure

    print("Performing OCR...")
    try:
        # Perform OCR using pytesseract
        extracted_text = pytesseract.image_to_string(img)
        print("OCR complete.")

    except pytesseract.TesseractNotFoundError:
        # This should ideally be caught by check_tesseract_installed, but double-check
        print(
            "ERROR: Tesseract OCR engine not found or not in PATH during OCR process.",
            file=sys.stderr,
        )
        return False, None
    except Exception as e:
        print(f"Error during OCR: {e}", file=sys.stderr)
        return False, None  # Indicate failure

    print(f"Searching for '{target_phrase}' (case-insensitive)...")
    # Check if the target phrase or regex pattern exists
    if use_regex:
        try:
            found = re.search(target_phrase, extracted_text, re.IGNORECASE) is not None
        except re.error as regex_error:
            print(f"Invalid regex pattern: {regex_error}", file=sys.stderr)
            return False, None
    else:
        found = target_phrase.lower() in extracted_text.lower()

    return found, extracted_text  # Return status and full text


# --- The Wrapper Function ---
def find_text_on_screen(
    search_term,
    monitor_to_capture=1,
    save_screenshot=False,
    region=None,
    use_regex=False,
):
    """
    Captures the specified monitor's screen or region, performs OCR, and checks if
    the search_term exists anywhere on that screen.

    Args:
        search_term (str): The text phrase or regex pattern to search for (case-insensitive).
        monitor_to_capture (int): The monitor number to capture
                                    (1: primary, 2: secondary, etc., 0: all monitors).
                                    Defaults to 1 (primary). Ignored if region is specified.
        save_screenshot (bool): If True, saves the captured screenshot as
                                'screenshot_debug.png'. Defaults to False.
        region (tuple, optional): Region to capture as (left, top, right, bottom) coordinates.
                                    If provided, will only capture this region instead of the full monitor.
        use_regex (bool): If True, interprets search_term as a regex pattern.

    Returns:
        bool: True if the search_term is found, False otherwise (including
                if Tesseract is not found or errors occur during capture/OCR).
    """
    print(f"\n--- Starting screen search for: '{search_term}' ---")
    if region:
        print(f"Searching within region: {region}")

    # 1. Prerequisite check
    if not check_tesseract_installed():
        print("Search aborted because Tesseract is not available.")
        print("--- Search finished (failed) ---")
        return False

    # 2. Call the core function
    found_status, extracted_text = capture_and_ocr(
        target_phrase=search_term,
        monitor_num=monitor_to_capture,
        debug_save=save_screenshot,
        region=region,
        use_regex=use_regex,
    )

    print(
        "EXTRACTED TEXT", extracted_text
    )  # Optional: Print the extracted text for debugging

    # 3. Interpret the results
    if extracted_text is None:
        # An error occurred in capture_and_ocr before the search could happen
        print(
            f"Search for '{search_term}' failed due to an error during screen capture or OCR."
        )
        result = False
    elif found_status:
        print(f"SUCCESS: Found '{search_term}' on the screen.")
        result = True
    else:
        print(f"INFO: Did not find '{search_term}' on the screen.")
        result = False

    print("--- Screen search finished ---")
    return result


def find_text_and_return(
    regex_pattern,
    monitor_num=1,
    debug_save=False,
    region=None,
):
    """
    Captures a screenshot of a specified monitor or region, performs OCR,
    and extracts text matching a regex pattern.

    Args:
        regex_pattern (str): The regex pattern to search for and extract.
        monitor_num (int): The monitor number (1=primary, 2=secondary, 0=all).
        debug_save (bool): If True, saves the screenshot for debugging.
        region (tuple, optional): Region to capture as (left, top, right, bottom) coordinates.
                                    If provided, will only capture this region.

    Returns:
        list: A list of all matches found using the regex pattern.
              Returns an empty list if no matches are found or an error occurs.
    """
    print(
        f"Attempting to capture {'region' if region else f'monitor {monitor_num}'} for regex extraction..."
    )
    try:
        with mss.mss() as sct:
            # If region is specified, use it directly
            if region:
                left, top, right, bottom = region
                monitor = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top,
                }
                print(f"Capturing region: {region}")
            else:
                # Adjust monitor selection logic slightly for clarity
                monitors = sct.monitors
                if monitor_num < 0 or monitor_num >= len(monitors):
                    print(
                        f"Warning: Monitor number {monitor_num} is invalid. Available monitors: {len(monitors)} (0=all, 1=primary, ...). Falling back to monitor 1 (primary).",
                        file=sys.stderr,
                    )
                    monitor_num = 1  # Default to primary
                    if monitor_num >= len(monitors):  # If only monitor 0 (all) exists
                        monitor_num = 0

                if monitor_num == 0 and len(monitors) > 1:
                    print(
                        "Capturing all monitors combined. This might yield unexpected OCR results."
                    )
                elif monitor_num == 1 and len(monitors) > 1:
                    print("Capturing primary monitor.")
                elif monitor_num > 0:
                    print(f"Capturing monitor {monitor_num}.")
                else:  # Only monitor 0 exists
                    print("Capturing the only available monitor.")

                monitor = monitors[monitor_num]

            # Capture the screen
            sct_img = sct.grab(monitor)
            print("Screenshot captured.")

            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            if debug_save:
                try:
                    filename = "screenshot_debug.png"
                    img.save(filename)
                    print(f"Screenshot saved for debugging as {filename}")
                except Exception as save_e:
                    print(
                        f"Warning: Could not save debug screenshot: {save_e}",
                        file=sys.stderr,
                    )

    except Exception as e:
        print(f"Error taking screenshot: {e}", file=sys.stderr)
        return []  # Indicate failure

    print("Performing OCR...")
    try:
        # Perform OCR using pytesseract
        extracted_text = pytesseract.image_to_string(img)
        print("OCR complete.")

    except pytesseract.TesseractNotFoundError:
        # This should ideally be caught by check_tesseract_installed, but double-check
        print(
            "ERROR: Tesseract OCR engine not found or not in PATH during OCR process.",
            file=sys.stderr,
        )
        return []
    except Exception as e:
        print(f"Error during OCR: {e}", file=sys.stderr)
        return []  # Indicate failure

    print(f"Extracting text using regex pattern: '{regex_pattern}'...")
    try:
        matches = re.findall(regex_pattern, extracted_text, re.IGNORECASE)
        if matches:
            print(f"Regex matches found: {matches}")
        else:
            print("No matches found using the provided regex pattern.")
        return matches
    except re.error as regex_error:
        print(f"Invalid regex pattern: {regex_error}", file=sys.stderr)
        return []  # Indicate failure


# --- Main Execution Example ---
if __name__ == "__main__":

    # --- Example Usage ---

    # Example 1: Search for a specific term on the primary monitor
    term_to_find = "PSMA PET"
    print(f"\n>>> TEST 1: Searching for '{term_to_find}' on primary monitor.")
    if find_text_on_screen(term_to_find):  # Default monitor is 1 (primary)
        print(f">>> TEST 1 RESULT: '{term_to_find}' was FOUND.")
    else:
        print(
            f">>> TEST 1 RESULT: '{term_to_find}' was NOT FOUND or an error occurred."
        )

    # Example 2: Search for common text on the primary monitor and save screenshot
    common_term = "File"  # Often found in menus
    print(
        f"\n>>> TEST 2: Searching for '{common_term}' on primary monitor (saving screenshot)."
    )
    if find_text_on_screen(common_term, save_screenshot=True):
        print(f">>> TEST 2 RESULT: '{common_term}' was FOUND.")
    else:
        print(f">>> TEST 2 RESULT: '{common_term}' was NOT FOUND or an error occurred.")

    # Example 3: Search for something unlikely to be there
    unlikely_term = "XyzzyPlughMagicWord"
    print(f"\n>>> TEST 3: Searching for '{unlikely_term}' on primary monitor.")
    if find_text_on_screen(unlikely_term):
        print(f">>> TEST 3 RESULT: '{unlikely_term}' was FOUND (unexpectedly!).")
    else:
        print(
            f">>> TEST 3 RESULT: '{unlikely_term}' was NOT FOUND (as expected) or an error occurred."
        )

    # Example 4: Search on a secondary monitor (if you have one)
    # Change monitor_to_capture=2 if you want to test a second monitor
    # secondary_monitor_term = "Settings"
    # print(f"\n>>> TEST 4: Searching for '{secondary_monitor_term}' on monitor 2.")
    # if find_text_on_screen(secondary_monitor_term, monitor_to_capture=2):
    #      print(f">>> TEST 4 RESULT: '{secondary_monitor_term}' was FOUND on monitor 2.")
    # else:
    #      print(f">>> TEST 4 RESULT: '{secondary_monitor_term}' was NOT FOUND on monitor 2 or an error occurred.")


# def extract_table
