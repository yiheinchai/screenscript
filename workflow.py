import logging
from screenocr import find_text_on_screen
from src import excel, epic, utils
from macro import PyMacroRecordLib
from pathlib import Path
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("workflow.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def has_psma_pet(iterations=500):
    pmr_lib = PyMacroRecordLib()
    pmr_lib.set_stop_key("esc")
    pmr_lib.reset_main_loop_stop_request()

    logger.info("--- Starting Main Processing Loop ---")
    logger.info(f"Press '{pmr_lib.stop_key}' at any time to stop the script.")

    for i in range(iterations):
        logger.info(f"\n======= Processing Patient Iteration {i+1}/500 =======")

        if pmr_lib.should_main_loop_stop():
            logger.info("Stop request detected. Terminating main loop.")
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
                excel.log_psma_pet(has_psma_pet)
                epic.close_patient()

            logger.info(f"------- Iteration {i+1} Complete -------")

        except Exception as e:
            logger.error(f"\n!!! EXCEPTION in iteration {i+1}: {e}", exc_info=True)
            if pmr_lib.is_playing():
                logger.info("Attempting to stop playback engine due to error...")
                pmr_lib.playback_engine.stop_playback()
            logger.info("Stopping main loop due to error.")
            break

    logger.info("\n--- Main Processing Loop Finished or Stopped ---")
