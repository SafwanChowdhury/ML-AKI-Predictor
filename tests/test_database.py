import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch

from datetime import date
import database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Setup a known state before each test
        database.patients.clear()
        database.test_results.clear()
        database.upsert_patient_data("1", "John Doe", "19800101", "M")

    def test_patient_exists(self):
        self.assertTrue(database.patient_exists("1"))
        self.assertFalse(database.patient_exists("2"))

    def test_convert_dob_format(self):
        self.assertEqual(database.convert_dob_format("19800101"), "1980-01-01")

    @patch("datetime.date")
    def test_calculate_age(self, mock_date):
        mock_date.today.return_value = date(2024, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self.assertEqual(database.calculate_age("1980-01-01"), 44)

    def test_upsert_patient_data_and_get_patient_info(self):
        database.upsert_patient_data("2", "Jane Doe", "19900202", "F")
        patient_id, age, sex, aki_detected = database.get_patient_info("2")
        self.assertEqual(patient_id, "2")
        self.assertEqual(sex, "F")
        # Assuming the current year is 2024, and mocking is not applied here
        # self.assertEqual(age, expected_age)  # Age depends on the current date
        self.assertEqual(aki_detected, 0)

    def test_remove_patient_data(self):
        database.remove_patient_data("1")
        self.assertFalse(database.patient_exists("1"))

    def test_upsert_test_result(self):
        # Insert a new test result and verify
        database.upsert_test_result("1", "20240101", "Positive")
        results = database.get_recent_test_results("1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], "20240101")
        self.assertEqual(results[0]["result"], "Positive")

        # Insert another test result and verify both are present
        database.upsert_test_result("1", "20240102", "Negative")
        results = database.get_recent_test_results("1")
        self.assertEqual(len(results), 2)

    def test_get_recent_test_results(self):
        # Setup by inserting multiple test results
        dates_results = [
            ("20240101", "Positive"),
            ("20240102", "Negative"),
            ("20240103", "Pending"),
        ]
        for date, result in dates_results:
            database.upsert_test_result("1", date, result)

        # Get the most recent 2 test results
        recent_results = database.get_recent_test_results("1", 2)
        self.assertEqual(len(recent_results), 2)
        self.assertEqual(recent_results[0]["date"], "20240103")
        self.assertEqual(recent_results[1]["date"], "20240102")

    def test_setaki_detected(self):
        # Initially, aki_detected should be 0
        _, _, _, aki_detected = database.get_patient_info("1")
        self.assertEqual(aki_detected, 0)

        # Set AKI detected and verify
        database.set_aki_detected("1", 1)
        _, _, _, aki_detected = database.get_patient_info("1")
        self.assertEqual(aki_detected, 1)

        # Test setting AKI detected to a non-existent patient
        database.set_aki_detected("nonexistent", 1)
        # This should not raise an error; behavior depends on function's intended handling of such cases

    def test_remove_patient_data_completeness(self):
        # Ensure related test results are also removed
        database.upsert_test_result("1", "20240101", "Positive")
        self.assertTrue(database.get_recent_test_results("1"))  # Should not be empty

        database.remove_patient_data("1")
        self.assertFalse(database.patient_exists("1"))
        self.assertEqual(database.get_recent_test_results("1"), [])  # Should be empty

    @patch("datetime.date")
    def test_upsert_patient_data_age_calculation(self, mock_date):
        mock_date.today.return_value = date(2024, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        database.upsert_patient_data("3", "Alice Wonderland", "20100101", "F")
        _, age, _, _ = database.get_patient_info("3")
        self.assertEqual(
            age, 14
        )  # Assuming the current year is 2024 for consistency in the example


if __name__ == "__main__":
    unittest.main()
