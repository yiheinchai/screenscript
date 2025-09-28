from macro import play_macro
from pathlib import Path

BASE_PATH = "/Users/yiheinchai/Documents/Learn/screenscript/src/"


def log_psma_pet(has_psma_pet):
    if has_psma_pet is None:
        play_macro(
            Path(BASE_PATH) / "log_none_psma.pmr",
            speed=1.5,
            repeat_times=1,
        )
        return

    if has_psma_pet:
        # If the patient has PSMA PET, log it
        play_macro(
            Path(BASE_PATH) / "log_yes_psma.pmr",
            speed=1.5,
            repeat_times=1,
        )
    else:
        # If the patient does not have PSMA PET, log it
        play_macro(
            Path(BASE_PATH) / "log_no_psma.pmr",
            speed=1.5,
            repeat_times=1,
        )


def log_psma_date(has_psma_date):
    if has_psma_date is None:
        play_macro(
            Path(BASE_PATH) / "log_none_psma_date.pmr",
            speed=1.5,
            repeat_times=1,
        )

    if has_psma_date:
        # If the patient has PSMA PET, log it
        play_macro(
            Path(BASE_PATH) / "log_yes_psma_date.pmr",
            speed=1.5,
            repeat_times=1,
        )
    else:
        play_macro(
            Path(BASE_PATH) / "log_no_psma_date.pmr",
            speed=1.5,
            repeat_times=1,
        )


def log_psma_history():
    play_macro(
        Path(BASE_PATH) / "log_psma_history.pmr",
        speed=1,
        repeat_times=1,
    )
    return True


def nav_up():
    play_macro(
        Path(BASE_PATH) / "excel_nav_up.pmr",
        speed=1.5,
        repeat_times=1,
    )
    return True
