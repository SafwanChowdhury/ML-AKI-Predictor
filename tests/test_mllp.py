import sys
import os
import os
from unittest import mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from mllp import (
    parse_hl7_message,
    process_message,
    mllp_client,
    convert_test_result_date_format,
    send_ack,
    parse_mllp_frame,
    receive_message,
)
import mllp


class TestMllp(unittest.TestCase):

    @patch("mllp.upsert_patient_data")
    @patch("mllp.parse_hl7_message")
    def test_process_message_new_patient(self, mock_parse, mock_upsert_patient_data):
        # Mock the parse_hl7_message to return a structured message that represents a new patient ADT^A01 event
        mock_message = [
            [
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "ADT^A01",
            ],  # Ensuring it passes the len(message[0]) < 10 check
            {3: "458973", 5: "COLBY MORRIS", 7: "19740803", 8: "M"},  # Patient ID
            {7: "20240510165800"},  # Test Date
            {5: "80.30219260110158"},  # Test Result
        ]

        mock_parse.return_value = mock_message

        mllp.process_message(mock_message)

        # Assert upsert_patient_data is called with the right arguments
        mock_upsert_patient_data.assert_called_once_with(
            "458973", "COLBY MORRIS", "19740803", "M"
        )

    def test_parse_hl7_message(self):
        # Example HL7 message
        hl7_message = "MSH|^~\&|..."
        message = parse_hl7_message(hl7_message)
        # Assert some basic properties of the parsed message
        # This depends on the structure of your HL7 messages

    def test_convert_test_result_date_format(self):
        self.assertEqual(
            convert_test_result_date_format("20240101123000"), "2024-01-01 12:30:00"
        )

    @patch("socket.socket")
    def test_mllp_client(self, mock_socket):
        pass
        # Mock socket to simulate network interactions
        # You can simulate receiving HL7 messages and assert correct behavior of mllp_client, especially handling end of data

    def test_parse_mllp_frame(self):
        # Given a valid MLLP frame, test if the HL7 message is correctly extracted
        mllp_frame = (
            bytes([mllp.MLLP_START_OF_BLOCK])
            + b"HL7Message"
            + bytes([mllp.MLLP_END_OF_BLOCK, mllp.MLLP_CARRIAGE_RETURN])
        )
        self.assertEqual(parse_mllp_frame(mllp_frame), b"HL7Message")

        # Test with invalid frames as well to ensure ValueError is raised

    @patch("socket.socket")
    def test_send_ack(self, mock_socket):
        pass
        # Test send_ack to ensure the ACK message is correctly formed and sent through the socket



if __name__ == "__main__":
    unittest.main()
