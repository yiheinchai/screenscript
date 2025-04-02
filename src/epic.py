from macro import play_macro
from screenocr import find_text_on_screen
from pathlib import Path

BASE_PATH = "/Users/yiheinchai/Documents/Learn/screenscript/src/"


def close_patient():
    # Close the patient
    play_macro(
        Path(BASE_PATH) / "close_patient.pmr",
        speed=2,
        repeat_times=1,
    )


def close_patient_lookup():
    # Close the patient lookup
    play_macro(
        Path(BASE_PATH) / "close_patient_lookup.pmr",
        speed=2,
        repeat_times=1,
    )


def view_found_patient():
    # View the found patient
    play_macro(
        Path(BASE_PATH) / "view_found_patient.pmr",
        speed=2,
        repeat_times=1,
    )


def search_psma_pet():
    search_successful = False
    max_retries = 3
    while not search_successful and max_retries > 0:
        play_macro(
            Path(BASE_PATH) / "search_psma_pet.pmr",
            speed=2,
            repeat_times=1,
        )
        search_successful = find_text_on_screen(
            "Search results for", region=(170, 166, 342, 201)
        )
        max_retries -= 1


def find_patient():
    # Find the patient
    play_macro(
        Path(BASE_PATH) / "find_patient.pmr",
        speed=2,
        repeat_times=1,
    )

    no_patient_found = find_text_on_screen(
        "No patients were found", region=(22, 336, 909, 404)
    )

    if no_patient_found:
        # If no patients were found, close the patient
        close_patient_lookup()
        return False
    else:
        view_found_patient()
        return True
