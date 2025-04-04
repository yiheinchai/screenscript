# --- START OF FILE main.py ---

from screenocr import find_text_on_screen
from src import excel, epic, utils  # Assuming these use play_macro internally
from macro import PyMacroRecordLib  # Import the singleton class directly

# from macro import play_macro # Don't need to import play_macro if only using singleton methods
from pathlib import Path
import time

# --- Get the Singleton Instance ---
# This also initializes it and starts the global listener if not already done
pmr_lib = PyMacroRecordLib()
pmr_lib.set_stop_key("esc")  # Ensure your desired stop key is set globally

# --- Reset Stop Flag ---
# Good practice to reset before starting a long loop
pmr_lib.reset_main_loop_stop_request()

print(f"--- Starting Main Processing Loop ---")
print(f"Press '{pmr_lib.stop_key}' at any time to stop the script.")

# --- Main Loop ---
for i in range(800):
    print(f"\n======= Processing Patient Iteration {i+1}/500 =======")

    # ****** CHECK FOR STOP REQUEST ******
    if pmr_lib.should_main_loop_stop():
        print("Stop request detected. Terminating main loop.")
        break
    # *************************************

    try:
        patient_found = epic.find_patient()  # Assuming this calls play_macro
        if not patient_found:
            excel.log_psma_pet(None)  # Assuming this calls play_macro
        else:
            epic.search_psma_pet()  # Assuming this calls play_macro

            no_psma_pet = utils.retry_till_false(
                lambda: find_text_on_screen(
                    "No results found for", region=(175, 375, 930, 960)
                ),
                retries=2,
                delay=0.75,
            )

            has_psma_pet = not no_psma_pet
            excel.log_psma_pet(has_psma_pet)  # Assuming this calls play_macro
            epic.close_patient()  # Assuming this calls play_macro

        print(f"------- Iteration {i+1} Complete -------")
        # Optional small delay
        # time.sleep(0.2)

    except Exception as e:
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print(f"!!! EXCEPTION in iteration {i+1}: {e}", file=sys.stderr)
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        # Optionally try to stop playback engine if error occurs
        if pmr_lib.is_playing():
            print("Attempting to stop playback engine due to error...")
            pmr_lib.playback_engine.stop_playback()  # Directly stop engine
        print("Stopping main loop due to error.")
        # You might want to add code here to ensure Epic is in a safe state
        break  # Stop the loop on error


# --- Outside the loop ---
print("\n--- Main Processing Loop Finished or Stopped ---")
