from macro import play_macro
from screenocr import find_text_on_screen
from pathlib import Path
from .utils import do_and_verify

BASE_PATH = "/Users/yiheinchai/Documents/Learn/screenscript/src/"


def close_patient():
    # Close the patient
    def _close_patient():
        play_macro(
            Path(BASE_PATH) / "close_patient.pmr",
            speed=2,
            repeat_times=1,
        )

    def verify_success():
        # Verify that the patient is closed
        patient_closed = find_text_on_screen(
            "This list has no patients", region=(480, 605, 677, 650)
        )
        return patient_closed

    do_and_verify(
        do_action=_close_patient,
        verify_success=verify_success,
    )

    return True


def close_patient_lookup():
    def _close_patient_lookup():
        play_macro(
            Path(BASE_PATH) / "close_patient_lookup.pmr",
            speed=2,
            repeat_times=1,
        )

    def verify_success():
        lookup_open = find_text_on_screen(
            "Search for a patient", region=(16, 154, 184, 188)
        )
        return not lookup_open

    result = do_and_verify(
        do_action=_close_patient_lookup,
        verify_success=verify_success,
    )
    return result


def close_break_glass():
    # Close the break-the-glass
    def _close_break_glass():
        play_macro(
            Path(BASE_PATH) / "close_break_glass.pmr",
            speed=2,
            repeat_times=1,
        )

    def verify_success():
        has_break_the_glass = find_text_on_screen(
            "Break-the-Glass", region=(175, 240, 305, 365)
        )
        return not has_break_the_glass

    result = do_and_verify(
        do_action=_close_break_glass,
        verify_success=verify_success,
    )
    return result


def view_found_patient():
    # View the found patient
    play_macro(
        Path(BASE_PATH) / "view_found_patient.pmr",
        speed=2,
        repeat_times=1,
    )

    has_break_the_glass = find_text_on_screen(
        "Break-the-Glass", region=(175, 240, 305, 365)
    )

    if has_break_the_glass:
        close_break_glass()
        close_patient_lookup()
        return False

    return True


def search_psma_pet():
    def _search_psma_pet():
        play_macro(
            Path(BASE_PATH) / "search_psma_pet.pmr",
            speed=2,
            repeat_times=1,
        )

    def verify_success():
        # Verify that the search was successful
        search_successful = find_text_on_screen(
            "Search results for", region=(170, 166, 342, 201)
        )
        return search_successful

    do_and_verify(
        do_action=_search_psma_pet,
        verify_success=verify_success,
    )


def find_patient():
    # Find the patient
    def verify_success():
        not_searched_yet = find_text_on_screen(
            "to get started", region=(24, 374, 900, 888)
        )
        return not not_searched_yet

    def clean_up():
        # Close the patient lookup
        close_patient_lookup()

    def _find_patient():
        play_macro(
            Path(BASE_PATH) / "find_patient.pmr",
            speed=2,
            repeat_times=1,
        )

    do_and_verify(
        do_action=_find_patient,
        verify_success=verify_success,
        clean_up=clean_up,
        retries=3,
    )

    no_patient_found = find_text_on_screen(
        "No patients were found", region=(22, 336, 909, 404)
    )

    if no_patient_found:
        # If no patients were found, close the patient
        close_patient_lookup()
        return False
    else:
        view_successful = view_found_patient()
        return view_successful
