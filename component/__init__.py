import logging
import os
from sys import stdout
from threading import Thread
import time

from greengrasssdk.stream_manager import (
    InvalidRequestException,
    MessageStreamDefinition,
    Persistence,
    ReadMessagesOptions,
    StreamManagerClient,
    StrategyOnFull,
)
from greengrasssdk.stream_manager.exceptions import (
    ConnectFailedException,
    NotEnoughMessagesException,
)

root_logger = logging.getLogger()
root_logger.setLevel(5)

logger = logging.getLogger(__name__)
logger.setLevel(5)  # TRACE
handler = logging.StreamHandler(stream=stdout)
logger.addHandler(handler)


READ_TIMEOUT_MILLS = float(os.environ.get("READ_TIMEOUT_MILLS", "100"))
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "1"))
STREAM_NAME = os.environ.get("STREAM_NAME", "repro.stream")
__current_sequence_number = 0


def create_stream(name: str):
    config = {
        "name": name,
        "max_size": int(0.05 * 1e9),  # 50MB
        "time_to_live_millis": 600000,  # 10 minutes
        "strategy_on_full": StrategyOnFull.OverwriteOldestData,
        "persistence": Persistence.File,
        "flush_on_write": False,
    }

    try:
        with StreamManagerClient(logger=logger) as client:
            try:
                return client.create_message_stream(MessageStreamDefinition(**config))
            except InvalidRequestException as e:
                if "stream already exists" in e.message:
                    logger.info(
                        f"stream, '{name}', already exists in call to `create_new_stream`"
                    )
                else:
                    raise e
    except ConnectFailedException:
        logger.warning(
            f"failed to connect to Greengrass stream manager during call to `create_new_stream` for {name}"
        )
        return None


def list_streams():
    try:
        with StreamManagerClient(logger=logger) as client:
            return client.list_streams()
    except ConnectFailedException:
        logger.warning(
            f"failed to connect to Greengrass stream manager during call to `list_streams`"
        )
        return []


def read_stream(name: str):
    global __current_sequence_number
    try:
        with StreamManagerClient(logger=logger) as client:
            return client.read_messages(
                stream_name=name,
                options=ReadMessagesOptions(
                    desired_start_sequence_number=__current_sequence_number,
                    min_message_count=1,
                    max_message_count=10,
                    read_timeout_millis=int(READ_TIMEOUT_MILLS),
                ),
            )
    except ConnectFailedException:
        logger.warning(
            f"failed to connect to Greengrass stream manager during call to `read_messages` on stream `{name}`"
        )
        return []
    except NotEnoughMessagesException:
        logger.debug(f"no messages in call to `read_messages` on stream `{name}`")
        return []


def append_message(stream_name: str, payload: bytes):
    with StreamManagerClient(logger=logger) as client:
        return client.append_message(stream_name=stream_name, data=payload)


def loop():
    logger.info("polling stream ...")
    global __current_sequence_number

    for _ in range(5):
        append_message(STREAM_NAME, b"abc123")

    response = list_streams()
    logger.debug(f"found {len(response)} streams")
    response = read_stream(STREAM_NAME)
    logger.debug(f"found {len(response)} messages")
    for message in response:
        logger.info(message)
        if message.sequence_number >= __current_sequence_number:
            __current_sequence_number = message.sequence_number + 1


def task():
    while True:
        loop()
        time.sleep(POLL_INTERVAL)


def main():
    create_stream(STREAM_NAME)

    thread_1 = Thread(target=task)
    thread_2 = Thread(target=task)
    thread_3 = Thread(target=task)

    thread_1.start()
    thread_2.start()
    thread_3.start()

    while True:
        time.sleep(1)
