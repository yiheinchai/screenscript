import time
from typing import Callable
import subprocess


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
    retries: int = 5,
) -> bool:
    """
    Perform an action and verify its success.
    If the verification fails, retry the action.
    """

    is_success = False
    max_retries = retries
    while not is_success and max_retries > 0:
        do_action()
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


def uk_to_us_date(uk_date: str) -> str:
    """
    Convert a UK date (DD/MM/YYYY) to a US date (MM/DD/YYYY).
    """
    day, month, year = uk_date.split("/")
    return f"{month}/{day}/{year}"
