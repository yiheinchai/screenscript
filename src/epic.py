from macro import play_macro
from screenocr import find_text_on_screen
from pathlib import Path
from .utils import click, do_and_verify, find_and_click, find_image_on_screen
from src import utils
import pyautogui
import time

BASE_PATH = "/Users/yihein.chai/Documents/learn/screenscript/src"
ASSETS_PATH = Path(BASE_PATH).parent / "assets"


def close_patient():
    # Close the patient
    def _close_patient():
        find_and_click(str(ASSETS_PATH / "close_patient.png"))

    def verify_success():
        # Verify that the patient is closed
        patient_closed = find_image_on_screen(str(ASSETS_PATH / "homescreen.png"))
        return patient_closed

    do_and_verify(
        do_action=_close_patient,
        verify_success=verify_success,
    )

    return True


def close_patient_lookup():
    def _close_patient_lookup():
        find_and_click(str(ASSETS_PATH / "cancel.png"))

    def verify_success():
        lookup_open = find_image_on_screen(str(ASSETS_PATH / "lookup.png"))
        return not lookup_open

    result = do_and_verify(
        do_action=_close_patient_lookup,
        verify_success=verify_success,
    )
    return result


def close_break_glass():
    # Close the break-the-glass
    def _close_break_glass():
        coords = list(
            pyautogui.locateAllOnScreen(str(ASSETS_PATH / "cancel.png"), confidence=0.8)
        )

        coords = sorted(coords, key=lambda box: box.left)

        click(coords[0][0] + 50, coords[0][1] + 25)

    def verify_success():
        has_break_the_glass = find_image_on_screen(str(ASSETS_PATH / "break_glass.png"))

        return not has_break_the_glass

    result = do_and_verify(
        do_action=_close_break_glass,
        verify_success=verify_success,
    )
    return result


def view_dead_patient():
    def _view_dead_patient():
        find_and_click(str(ASSETS_PATH / "open_dead_chart.png"))

    def verify_success():
        # Verify that the patient is viewed
        patient_viewed = find_image_on_screen(str(ASSETS_PATH / "chart_review.png"))

        return patient_viewed

    result = do_and_verify(
        do_action=_view_dead_patient,
        verify_success=verify_success,
    )
    return result


def view_found_patient():
    glass_appeared = False
    patient_deceased = False

    # View the found patient
    def _view_found_patient():
        find_and_click(str(ASSETS_PATH / "accept.png"))

    def verify_success():
        nonlocal glass_appeared, patient_deceased
        # Verify that the patient is viewed
        patient_viewed = find_image_on_screen(str(ASSETS_PATH / "chart_review.png"))

        if patient_viewed:
            return True
        else:
            has_break_the_glass = find_image_on_screen(
                str(ASSETS_PATH / "break_glass.png")
            )

            if has_break_the_glass:
                close_break_glass()
                close_patient_lookup()
                glass_appeared = True
                return True

            is_patient_dead = find_image_on_screen(
                str(ASSETS_PATH / "open_dead_chart.png")
            )

            if is_patient_dead:
                patient_deceased = True
                view_dead_patient()
                return True

            # Failed to view the patient, try again
            return False

    result = do_and_verify(
        do_action=_view_found_patient,
        verify_success=verify_success,
    )

    if glass_appeared:
        return {"found": False, "deceased": False}

    return {"found": result, "deceased": patient_deceased}


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
            "Search results for", region=(177, 175, 352, 204)
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

        patient_name_appeared = find_text_on_screen(
            "Patient Name", region=(222, 382, 544, 497)
        )

        if not_searched_yet:
            return False

        no_patient_found = find_text_on_screen(
            "No patients were found", region=(0, 373, 907, 827)
        )

        if no_patient_found:
            # If no patients were found, close the patient
            close_patient_lookup()
            non_existent_patient = True
            return True

        if not patient_name_appeared:
            return False

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
        return {"found": False, "deceased": False}
    else:
        return view_found_patient()


def find_patient_clipboard(mrn):
    # Find the patient
    non_existent_patient = False

    def verify_success():
        nonlocal non_existent_patient

        not_searched_yet = find_image_on_screen(str(ASSETS_PATH / "empty_search.png"))
        patient_name_appeared = find_image_on_screen(
            str(ASSETS_PATH / "patient_found.png")
        )

        if not_searched_yet:
            return False

        no_patient_found = find_image_on_screen(
            str(ASSETS_PATH / "no_patients_found.png")
        )

        if no_patient_found:
            # If no patients were found, close the patient
            find_and_click(str(ASSETS_PATH / "cancel.png"))
            non_existent_patient = True
            return False

        if not patient_name_appeared:
            return False

        return True

    def clean_up():
        # Close the patient lookup
        close_patient_lookup()

    def _find_patient():
        find_and_click(str(ASSETS_PATH / "epic_live.png"))
        find_and_click(str(ASSETS_PATH / "patient_lookup.png"))
        time.sleep(0.5)
        pyautogui.typewrite(mrn, interval=0.1)
        find_and_click(str(ASSETS_PATH / "find_patient.png"))

    do_and_verify(
        do_action=_find_patient,
        verify_success=verify_success,
        clean_up=clean_up,
        retries=3,
    )

    if non_existent_patient:
        return {"found": False, "deceased": False}
    else:
        return view_found_patient()


def view_notes():
    def action():
        find_and_click(str(ASSETS_PATH / "notes.png"))

    def verify_success():
        # Verify that the notes were viewed
        notes_viewed = find_image_on_screen(str(ASSETS_PATH / "notes_type.png"))
        return notes_viewed

    result = do_and_verify(
        do_action=action,
        verify_success=verify_success,
    )
    return result


def view_imaging():
    def action():
        find_and_click(str(ASSETS_PATH / "imaging.png"))

    def verify_success():
        # Verify that the imaging was viewed
        imaging_viewed = find_image_on_screen(
            str(ASSETS_PATH / "imaging_performed.png")
        )
        return imaging_viewed

    result = do_and_verify(
        do_action=action,
        verify_success=verify_success,
    )
    return result


def find_icons(type, confidence=0.9):
    try:
        boxes = list(
            pyautogui.locateAllOnScreen(
                str(ASSETS_PATH / f"{type}_icon.png"), confidence=confidence
            )
        )
        icons = [(box.left + box.width // 2, box.top + box.height // 2) for box in boxes]
        icons = utils.group_locations(icons)
    except Exception as e:
        print(f"Error finding {type} icons: {e}")
        icons = []
    return icons


def find_note_icons():
    return find_icons("note")


def find_imaging_icons():
    return find_icons("imaging", confidence=0.8)


def view_note_details(coords):
    def action():
        click(coords[0], coords[1])
        # move cursor away to avoid hover effects
        pyautogui.moveTo(100, 100)

    def verify_success():
        # Verify that the note details were viewed
        note_details_viewed = find_image_on_screen(
            str(ASSETS_PATH / "notes_toolbar.png")
        )
        return note_details_viewed

    result = do_and_verify(
        do_action=action,
        verify_success=verify_success,
    )
    return result


def close_note_details():
    def action():
        find_and_click(str(ASSETS_PATH / "close_note.png"))

    def verify_success():
        # Verify that the note details were closed
        note_details_closed = not find_image_on_screen(
            str(ASSETS_PATH / "notes_toolbar.png")
        )
        return note_details_closed

    result = do_and_verify(
        do_action=action,
        verify_success=verify_success,
    )
    return result


def copy_note_contents():
    def action():
        find_and_click(
            str(ASSETS_PATH / "notes_toolbar.png"),
            offset_y=150,
            offset_x=200,
            button="right",
        )
        time.sleep(0.5)

    def verify_success():
        # Verify that the note contents were copied
        return find_image_on_screen(str(ASSETS_PATH / "copy_all.png"))

    result = do_and_verify(
        do_action=action,
        verify_success=verify_success,
    )

    if not result:
        return ""

    result = do_and_verify(
        do_action=lambda: find_and_click(str(ASSETS_PATH / "copy_all.png")),
        verify_success=lambda: len(utils.receive_from_clipboard()) > 0,
    )

    if not result:
        return ""

    return utils.receive_from_clipboard()


def scroll_to_top():
    def action():
        find_and_click(str(ASSETS_PATH / "scroll_up.png"), confidence=0.95)

    def verify_success():
        # Verify that the note details were viewed
        pyautogui.moveTo(100, 100)
        at_top = find_image_on_screen(
            str(ASSETS_PATH / "top_scroll.png"), confidence=0.95
        )
        return at_top

    has_scroll = find_image_on_screen(
        str(ASSETS_PATH / "scroll_up.png"), confidence=0.95
    )
    if not has_scroll:
        return True

    at_top = verify_success()
    if at_top:
        return True

    result = do_and_verify(do_action=action, verify_success=verify_success, retries=50)
    return result
