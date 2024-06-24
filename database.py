"""Description: This file contains the in-memory data stores and functions to interact with them."""

import datetime
import logging
import json

# Initialize in-memory data stores
patients = {}
test_results = {}


def dump_database(filepath):
    """
    Dump the database contents (patients and test_results) to a JSON file.

    :param filepath: Path to the file where the database should be dumped.
    """
    # Combine patients and test_results into a single dictionary for dumping
    database_dump = {"patients": patients, "test_results": test_results}

    # Write the combined dictionary to a file in JSON format
    try:
        with open(filepath, "w") as file:
            json.dump(database_dump, file, indent=4)
        logging.info(f"Database successfully dumped to {filepath}")
    except Exception as e:
        logging.error(f"Failed to dump database: {e}")


def has_test_results(patient_id):
    """Check if a patient has test results."""
    return patient_id in test_results


def load_database(filepath):
    """
    Load the database contents from a JSON file into the patients and test_results dictionaries.

    :param filepath: Path to the file from which the database should be loaded.
    """
    global patients, test_results  # Use global to modify the outer scope variables

    # Read the database from a file in JSON format
    try:
        with open(filepath, "r") as file:
            database_dump = json.load(file)
            patients = database_dump.get("patients", {})
            test_results = database_dump.get("test_results", {})
        logging.info("Database successfully loaded from {}".format(filepath))
    except Exception as e:
        logging.error(f"Failed to load database: {e}")


def patient_exists(patient_id):
    """Check if a patient exists."""
    return patient_id in patients


def convert_dob_format(dob):
    """Convert dob from 'yyyymmdd' to 'yyyy-mm-dd' format"""
    return f"{dob[:4]}-{dob[4:6]}-{dob[6:8]}"


def get_patient_info(patient_id):
    """Retrieve patient information using in-memory data structures."""
    try:
        # Check if the patient exists in the 'patients' dictionary
        if patient_id not in patients:
            return -1, -1, "", 0

        patient_info = patients[patient_id]
        # Extract required information
        age = patient_info.get("age")
        sex = patient_info.get("sex")
        aki_detected = patient_info.get("aki_detected", 0)
        return patient_id, age, sex, aki_detected

    except Exception as e:
        logging.error(f"Failed to get patient info: {e}")
        return -1, -1, "", 0


def calculate_age(dob):
    """Calculate age given dob in 'YYYY-MM-DD' format."""
    born = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def upsert_patient_data(patient_id, name, dob, sex):
    """Insert or update patient data."""
    formatted_dob = convert_dob_format(dob)
    age = calculate_age(formatted_dob)
    patients[patient_id] = {"name": name, "sex": sex, "age": age, "aki_detected": 0}


def upsert_test_result(patient_id, date, result):
    """Insert or update test result."""
    if patient_id not in test_results:
        test_results[patient_id] = []
    test_results[patient_id].append({"date": date, "result": result})


def remove_patient_data(patient_id):
    """Remove patient data."""
    if patient_id in patients:
        del patients[patient_id]
    # Also remove related test results
    if patient_id in test_results:
        del test_results[patient_id]


def get_recent_test_results(patient_id, num_results=3):
    """Get most recent test results for a patient."""
    if patient_id in test_results:
        sorted_results = sorted(
            test_results[patient_id], key=lambda x: x["date"], reverse=True
        )
        return sorted_results[:num_results]
    return []


def set_aki_detected(patient_id, aki_detected):
    """Set AKI detected status for a patient."""
    if patient_id in patients:
        patients[patient_id]["aki_detected"] = aki_detected
