import time
from typing import Callable


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
    retries: int = 3,
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
