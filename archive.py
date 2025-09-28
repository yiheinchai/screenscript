from screenocr import find_text_on_screen, find_text_and_return
from src import excel, epic, utils
from macro import PyMacroRecordLib
from pathlib import Path
import time

pmr_lib = PyMacroRecordLib()
pmr_lib.set_stop_key("esc")
pmr_lib.reset_main_loop_stop_request()

print(f"--- Starting Main Processing Loop ---")
print(f"Press '{pmr_lib.stop_key}' at any time to stop the script.")

for i in range(2506):
    print(f"\n======= Processing Patient Iteration {i+1}/500 =======")

    if pmr_lib.should_main_loop_stop():
        print("Stop request detected. Terminating main loop.")
        break

    try:
        patient_found = epic.find_patient()
        if not patient_found:
            excel.log_psma_pet(None)
        else:
            epic.search_psma_pet()

            no_psma_pet = utils.retry_till_false(
                lambda: find_text_on_screen(
                    "No results found for", region=(175, 375, 930, 960)
                ),
                retries=2,
                delay=0.75,
            )

            has_psma_pet = not no_psma_pet

            if has_psma_pet:
                psma_date = find_text_and_return(
                    r"\b\d{1,2}/\d{1,2}/\d{4}\b",
                    region=(782, 410, 920, 437),
                    debug_save=True,
                )

                psma_history = find_text_and_return(
                    r"\b\w+\s\d{1,2}/\d{1,2}/\d{4}\b",
                    region=(782, 410, 932, 969),
                    debug_save=True,
                )

                excel.log_psma_pet(True)
                excel.nav_up()

                if psma_date:
                    # convert date (28/4/2024) to us date (4/28/2024)
                    day, month, year = psma_date[0].split("/")
                    us_date = f"{month}/{day}/{year}"
                    print(f"PSMA Date Found: {psma_date}")
                    utils.send_to_clipboard(us_date)
                    excel.log_psma_date(True)
                    if psma_history:
                        utils.send_to_clipboard(",".join(psma_history))
                        excel.nav_up()
                        excel.log_psma_history()
                    epic.close_patient()
                    continue
                else:
                    excel.log_psma_date(False)
                    if psma_history:
                        utils.send_to_clipboard(",".join(psma_history))
                        excel.nav_up()
                        excel.log_psma_history()
                    epic.close_patient()
                    continue

            excel.log_psma_pet(False)
            epic.close_patient()

        print(f"------- Iteration {i+1} Complete -------")

    except Exception as e:
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print(f"!!! EXCEPTION in iteration {i+1}: {e}", file=sys.stderr)
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        if pmr_lib.is_playing():
            print("Attempting to stop playback engine due to error...")
            pmr_lib.playback_engine.stop_playback()
        print("Stopping main loop due to error.")
        break

print("\n--- Main Processing Loop Finished or Stopped ---")
