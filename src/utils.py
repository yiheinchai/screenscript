import time


def retry_till_false(callback, retries=3, delay=1):
    time.sleep(delay)
    condition = callback()
    for i in range(retries):
        if not condition:
            break
        time.sleep(delay)
        condition = callback()
    return condition
