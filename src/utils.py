import time
from typing import Callable
import subprocess
import pyautogui
import math

# Display scale factor: 2 for macOS Retina, 1 for non-Retina
DISPLAY_SCALE = 2


def retry_till_false(callback, retries=3, delay=1):
    time.sleep(delay)
    condition = callback()
    for i in range(retries):
        if not condition:
            break
        time.sleep(delay)
        condition = callback()
    return condition


def do_and_verify(
    do_action: Callable[[], None],
    verify_success: Callable[[], bool],
    clean_up: Callable[[], None] = lambda: None,
    retries: int = 10,
) -> bool:
    """
    Perform an action and verify its success.
    If the verification fails, retry the action.
    """

    is_success = False
    max_retries = retries
    while not is_success and max_retries > 0:
        do_action()
        time.sleep(0.3)  # Wait a bit before verification
        is_success = verify_success()
        if is_success:
            break

        # If verification fails, clean up and retry
        clean_up()

        max_retries -= 1

    return is_success


def send_to_clipboard(text: str):
    """
    Send text to the clipboard.
    """
    subprocess.run("pbcopy", text=True, input=text)


def receive_from_clipboard() -> str:
    """
    Receive text from the clipboard.
    """
    result = subprocess.run("pbpaste", text=True, capture_output=True)
    return result.stdout


def clear_clipboard():
    """
    Clear the clipboard.
    """
    send_to_clipboard("")


def uk_to_us_date(uk_date: str) -> str:
    """
    Convert a UK date (DD/MM/YYYY) to a US date (MM/DD/YYYY).
    """
    day, month, year = uk_date.split("/")
    return f"{month}/{day}/{year}"


def find_and_click(image_path, offset_x=0, offset_y=0, button="left", confidence=0.8):
    try:
        button_location = pyautogui.locateCenterOnScreen(
            image_path, confidence=confidence
        )
        if button_location:
            pyautogui.click(
                (button_location.x + offset_x) // DISPLAY_SCALE,
                (button_location.y + offset_y) // DISPLAY_SCALE,
                button=button,
            )
            return True
        else:
            print(f"Failed to find image: {image_path}")
            return False
    except Exception as e:
        print(f"Error clicking on image '{image_path}': {e}")
        return False


def find_image_on_screen(image_path, confidence=0.8) -> bool:
    try:
        button_location = pyautogui.locateCenterOnScreen(
            image_path, confidence=confidence
        )
        return button_location is not None
    except Exception as e:
        print(f"Error finding image on screen '{image_path}': {e}")
        return False


def click(x, y, scaled=False):
    try:
        if scaled:
            pyautogui.click(x, y)
        else:
            pyautogui.click(x // DISPLAY_SCALE, y // DISPLAY_SCALE)
        return True
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return False


def group_locations(locations, distance_threshold=20):
    """
    Groups nearby coordinate locations into single points.
    It takes a list of locations (like those from pyautogui) and
    returns a filtered list where clustered detections are reduced to one.
    """
    grouped_locations = []
    for loc in locations:
        # Check if the location is too close to any already in our grouped list
        is_close_to_existing = False
        for grouped_loc in grouped_locations:
            # Calculate the Euclidean distance between the centers
            dist = math.sqrt(
                (loc[0] - grouped_loc[0]) ** 2 + (loc[1] - grouped_loc[1]) ** 2
            )
            if dist < distance_threshold:
                is_close_to_existing = True
                break

        # If it's not close to any existing point, it's a new unique location
        if not is_close_to_existing:
            grouped_locations.append(loc)

    return grouped_locations
