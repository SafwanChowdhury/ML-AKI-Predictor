import csv

from database import (
    upsert_patient_data,
    upsert_test_result,
)
import logging


def readHistory(fileName: str):
    try:
        # Read historical data from CSV and map it to a Python dictionary
        data = read_csv_to_map(fileName)

        # Loop through the data to upsert patient and test result information into the database
        for mrn in data:
            for test in data[mrn]:
                # Upsert patient data with a default name, DOB, and sex since the actual data is unknown
                upsert_patient_data(mrn, "Unknown", "20000101", "Unknown")
                # Upsert test result data for the patient
                upsert_test_result(mrn, test[0], float(test[1]))

        logging.info("History read successfully")
    except Exception as e:
        # Log and raise exception if reading history fails
        logging.fatal(f"Failed to read history: {e}")
        raise e


def read_csv_to_map(file_path):
    mrn_to_tests = {}
    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mrn = row["mrn"]
            tests = []
            # Iterate in reverse order to get the most recent tests first
            for i in reversed(range(31)):  # Assuming a maximum of 26 tests
                date_key = f"creatinine_date_{i}"
                result_key = f"creatinine_result_{i}"
                # Check if both date_key and result_key exist in the row and have values
                if (
                    date_key in row
                    and result_key in row
                    and row[date_key]
                    and row[result_key]
                ):
                    tests.append([row[date_key], row[result_key]])
                    if len(tests) == 3:  # Keep only the most recent 3 tests
                        break

            mrn_to_tests[mrn] = tests
    return mrn_to_tests
