#!/usr/bin/env python3
import argparse
import os
import sys
import logging
import signal
from database import dump_database, load_database
from singleton import model
from singleton.model import initModel
import mllp
from processData import readHistory
from prometheus_client import start_http_server


model = initModel()

if os.path.exists("/state"):
    logging.basicConfig(
        filename="/state/logs.log",
        filemode="a",
        format="%(asctime)s,%(msecs)d:%(name)s:%(levelname)s:%(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
else:
    logging.basicConfig(
        format="%(asctime)s,%(msecs)d:%(name)s:%(levelname)s:%(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


DATABASE_FILE = "database.json"
RECONNECT_ON_FAILURE = os.getenv("RECONNECT_ON_FAILURE", "False")
USE_DATABASE = os.getenv("USE_DATABASE", "False")


def graceful_shutdown(signal_received, frame):
    """
    Handle graceful shutdown: dump the database and exit.
    """
    logging.info("Graceful shutdown initiated.")

    # Assuming the dump_database function takes a file path where to save the dump
    if USE_DATABASE:
        dump_database(DATABASE_FILE)
    else:
        logging.info(
            "USE_DATABASE is False, not dumping the database. History will be used next time."
        )

    sys.exit(0)


def handle_env():
    """Parses environment variables. And turns them into booleans. Might look a bit strange, but it's fine."""
    global RECONNECT_ON_FAILURE, USE_DATABASE

    if RECONNECT_ON_FAILURE not in ["True", "False"]:
        RECONNECT_ON_FAILURE = "False"

    if USE_DATABASE not in ["True", "False"]:
        USE_DATABASE = "False"

    USE_DATABASE = USE_DATABASE == "True"
    RECONNECT_ON_FAILURE = RECONNECT_ON_FAILURE == "True"
    logging.info("RECONNECT_ON_FAILURE: %s", RECONNECT_ON_FAILURE)
    logging.info("USE_DATABASE: %s", USE_DATABASE)


if __name__ == "__main__":
    start_http_server(8000)
    logging.info("Connected to prometheus server on port 8080")

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # check if /state directory exists
    if not os.path.exists("/state"):
        logging.info("/state directory does not exist")
    else:
        logging.info("/state directory exists")
        # print all the files in the /state directory
        for file in os.listdir("/state"):
            logging.info("\tFile in /state: %s", file)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history",
        default="history.csv",
        help="HL7 messages to replay, in MLLP format",
    )
    parser.add_argument(
        "--database",
        default="/data/database.json",
        help="Database file to load and save",
    )
    flags = parser.parse_args()
    DATABASE_FILE = flags.database

    logging.info("Database file: %s", DATABASE_FILE)

    logging.info("Starting mainframe")
    handle_env()

    assert model is not None, "Model not initialized"

    # if DATABASE_FILE exists, load the database from it
    if USE_DATABASE and os.path.exists(DATABASE_FILE):
        load_database(DATABASE_FILE)
    else:
        # Read historical data and upsert into the database
        readHistory(flags.history)

    # Start MLLP client for handling HL7 messages
    # mllp.mllp_client()
    mllp.mllp_client()

    if USE_DATABASE:
        # Dump the database to the file
        dump_database(DATABASE_FILE)
    else:
        logging.info(
            "USE_DATABASE is False, not dumping the database. History will be used next time."
        )
    sys.exit(0)
