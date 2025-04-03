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
    glass_appeared = False

    # View the found patient
    def _view_found_patient():
        play_macro(
            Path(BASE_PATH) / "view_found_patient.pmr",
            speed=2,
            repeat_times=1,
        )

    def verify_success():
        nonlocal glass_appeared
        # Verify that the patient is viewed
        patient_viewed = find_text_on_screen("Chart Re", region=(97, 205, 270, 236))

        if patient_viewed:
            return True
        else:
            has_break_the_glass = find_text_on_screen(
                "Break-the-Glass", region=(175, 240, 305, 365)
            )

            if has_break_the_glass:
                close_break_glass()
                close_patient_lookup()
                glass_appeared = True
                return True

            # Failed to view the patient, try again
            return False

    result = do_and_verify(
        do_action=_view_found_patient,
        verify_success=verify_success,
    )

    if glass_appeared:
        return False

    return result


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
    non_existent_patient = False

    def verify_success():
        nonlocal non_existent_patient

        not_searched_yet = find_text_on_screen(
            "to get started", region=(24, 374, 900, 888)
        )
        if not_searched_yet:
            return not not_searched_yet

        no_patient_found = find_text_on_screen(
            "No patients were found", region=(22, 336, 909, 404)
        )

        if no_patient_found:
            # If no patients were found, close the patient
            close_patient_lookup()
            non_existent_patient = True
            return True

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

    if non_existent_patient:
        return False
    else:
        view_successful = view_found_patient()
        return view_successful
