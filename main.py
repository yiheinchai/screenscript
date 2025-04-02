from screenocr import find_text_on_screen
from src import excel, epic, utils

for i in range(500):
    patient_found = epic.find_patient()
    if not patient_found:
        excel.log_psma_pet(None)
    else:
        epic.search_psma_pet()
        no_psma_pet = utils.retry_till_false(
            lambda: find_text_on_screen(
                "No results found for", region=(175, 375, 930, 960)
            )
        )
        has_psma_pet = not no_psma_pet
        excel.log_psma_pet(has_psma_pet)
        epic.close_patient()
