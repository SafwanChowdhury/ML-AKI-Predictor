"""Module to connect to MLLP server and process incoming messages."""

import logging
import socket
import time
import os
import hl7

from database import (
    calculate_age,
    convert_dob_format,
    get_patient_info,
    has_test_results,
    upsert_patient_data,
    upsert_test_result,
)
from main import RECONNECT_ON_FAILURE
from predict import run_prediction

from counter import (
    blood_tests_received,
    messages,
    mllp_reconnections,
    blood_test_result_values,
    request_time,
    patient_admitted,
)

PREDICT_PATIENT_WITH_HISTORY = os.environ.get("PREDICT_PATIENT_WITH_HISTORY", "0")


# MLLP framing characters
MLLP_START_OF_BLOCK = 0x0B
MLLP_END_OF_BLOCK = 0x1C
MLLP_CARRIAGE_RETURN = 0x0D


def parse_hl7_message(message):
    """Parse HL7 message and return a dictionary."""
    try:
        h = hl7.parse(message)
    except:
        logging.error(f"Error parsing HL7 message: {message}")
        return "", True
    return h, False


def convert_test_result_date_format(date_str):
    """Convert date from 'yyyymmddhhmmss' to 'yyyy-mm-dd HH:MM:SS' format"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {date_str[8:10]}:{date_str[10:12]}:{date_str[12:14]}"


@request_time.time()
def process_message(message):
    """Process HL7 message and update the database."""
    logging.debug(f"Processing message: {message}")

    # check if message[0][9] exists
    if len(message) == 0 or len(message[0]) < 10:
        logging.warning(f"Message type can not be processed: {message}")
        return
    try:
        match str(message[0][9]):
            case "ADT^A01":  # new patient
                patient_name = str(message[1][5])
                patient_id = str(message[1][3])
                patient_dob = str(message[1][7])
                patient_sex = str(message[1][8])

                upsert_patient_data(
                    patient_id,
                    patient_name,
                    patient_dob,
                    patient_sex,
                )

                patient_admitted.inc()

                if has_test_results(patient_id) and PREDICT_PATIENT_WITH_HISTORY == "1":
                    logging.info(
                        f"Patient {patient_id} already has test results, running prediction."
                    )
                    formatted_dob = convert_dob_format(patient_dob)
                    age = calculate_age(formatted_dob)

                    run_prediction(patient_id, age, patient_sex)

            case "ADT^A03":  # patient update
                pass
            case "ORU^R01":  # test result
                patient_id = str(message[1][3])
                test_date = message[2][7]
                test_result = float(str(message[3][5]))

                # get patient info
                mrn, age, sex, aki_detected = get_patient_info(patient_id)

                if aki_detected == 1:
                    logging.debug(f"Patient {patient_id} already has AKI")
                    return

                # persist test results
                upsert_test_result(
                    patient_id,
                    convert_test_result_date_format(str(test_date)),
                    test_result,
                )

                # prometheus histogram
                blood_test_result_values.observe(test_result)

                if mrn == -1:
                    logging.debug(
                        f"Patient {patient_id} does not exist in the database"
                    )
                    return

                run_prediction(patient_id, age, sex)

                blood_tests_received.inc()

            case _:
                logging.warning(f"Message type can not be processed: {message}")

    except Exception as e:
        logging.error(f"Error processing message {message}: {e}")


# Function to send ACK message
def send_ack(socket):
    """Send ACK message to MLLP server."""
    ack_message = "MSH|^~\\&|||||20240129093837||ACK|||2.5\rMSA|AA"
    mllp_ack = (
        bytes(chr(MLLP_START_OF_BLOCK), "ascii")
        + ack_message.encode()
        + bytes(chr(MLLP_END_OF_BLOCK) + chr(MLLP_CARRIAGE_RETURN), "ascii")
    )
    socket.sendall(mllp_ack)


# Function to parse MLLP framed message and extract HL7 message
def parse_mllp_frame(data):
    """Parse MLLP frame and extract HL7 message."""
    if (
        data[0] != MLLP_START_OF_BLOCK
        or data[-2] != MLLP_END_OF_BLOCK
        or data[-1] != MLLP_CARRIAGE_RETURN
    ):
        return [], True
    return data[1:-2], False


def receive_message(sock):
    """Receives message and sends buffer bytes back"""
    buffer = b""
    while True:
        data = sock.recv(1024)
        if not data:
            return buffer
        buffer += data
        if b"\x1c\x0d" in buffer:
            break
    return buffer


def mllp_client():
    """Main function to connect to MLLP server and process incoming messages."""
    mllp_address = os.getenv("MLLP_ADDRESS", "127.0.0.1:8440")
    server_host, server_port = mllp_address.split(":")
    server_port = int(server_port)  # Convert port to integer
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((server_host, server_port))
                logging.info(f"Connected to MLLP server at {server_host}:{server_port}")

                buffer = b""
                while True:
                    data = receive_message(sock)
                    if not data:
                        logging.info(
                            "End of data received from MLLP server, terminating connection"
                        )
                        raise Exception("End of data received from MLLP server")

                    buffer += data
                    while b"\x0b" in buffer and b"\x1c\x0d" in buffer:
                        start = buffer.index(b"\x0b")
                        end = buffer.index(b"\x1c\x0d") + 2
                        frame = buffer[start:end]
                        buffer = buffer[end:]

                        hl7_message, error = parse_mllp_frame(frame)

                        if error:
                            logging.error(f"Error parsing MLLP frame: {frame}")
                            send_ack(sock)
                            continue

                        hl7_message, error = parse_hl7_message(hl7_message.decode())

                        if error:
                            logging.error(f"Error parsing HL7 message: {hl7_message}")
                            send_ack(sock)
                            continue

                        process_message(hl7_message)

                        # Prometheus counter
                        messages.inc()

                        send_ack(sock)

        except Exception as e:
            if RECONNECT_ON_FAILURE == "False":
                logging.error(f"Connection to MLLP failed, terminating: {e}")
                return
            logging.error(f"Connection to MLLP failed, trying after 5 seconds: {e}")
            mllp_reconnections.inc()
            time.sleep(1)
