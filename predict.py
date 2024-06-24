import logging
import os
import time


import requests
from main import model
from database import get_recent_test_results, set_aki_detected

from singleton.model import predict
from counter import aki_positive_predictions, pager_http_failures


LOG_PAGING = True
PAGER_URL = os.environ.get("PAGER_ADDRESS", "0.0.0.0:8441")


def run_prediction(patient_id, age, sex):
    recent_results = get_recent_test_results(patient_id, 3)
    results = [
        result["result"] for result in recent_results
    ]  # Assuming result is in the 3rd column
    dates = [
        result["date"] for result in recent_results
    ]  # Assuming date is in the 2nd column

    for _ in range(3 - len(recent_results)):
        results.insert(0, results[0])

    # Run prediction
    prediction = predict(
        model, age, sex, results[0], results[1], results[2], sum(results) / len(results)
    )

    if prediction == 1:
        set_aki_detected(patient_id, 1)
        url = "http://" + PAGER_URL + "/page"
        headers = {"Content-type": "text/plain"}

        aki_positive_predictions.inc()

        counter = 0
        while counter < 2:
            try:
                response = requests.post(
                    url, data=str(patient_id), headers=headers, timeout=1
                )
                if response.status_code == 200:
                    if LOG_PAGING:
                        logging.info(f"PAGE:{patient_id}:{dates[0]}")
                        # also save to a file
                        # with open("pages.log", "a") as f:
                        #     f.write(f"{patient_id},{dates[0]}\n")
                return
            except Exception as e:
                counter += 1
                logging.error(f"Failed to page patient: {patient_id} - {e}")
                pager_http_failures.inc()
