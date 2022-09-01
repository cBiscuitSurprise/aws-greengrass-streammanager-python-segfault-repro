import logging
import os
import time

from greengrasssdk.stream_manager import (
    InvalidRequestException,
    MessageStreamDefinition,
    Persistence,
    ReadMessagesOptions,
    StreamManagerClient,
    StrategyOnFull,
)
from greengrasssdk.stream_manager.exceptions import ConnectFailedException

logger = logging.getLogger(__name__)
logger.setLevel(5)  # TRACE

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
                    read_timeout_millis=int(100 * 1000),
                ),
            )
    except ConnectFailedException:
        logger.warning(
            f"failed to connect to Greengrass stream manager during call to `read_messages` on stream `{name}`"
        )
        return []


def loop():
    logger.info("polling stream ...")
    global __current_sequence_number
    response = read_stream(STREAM_NAME)
    logger.debug(f"found {len(response)} messages")
    for message in response:
        logger.info(message)
        if message.sequence_number >= __current_sequence_number:
            __current_sequence_number = message.sequence_number + 1


def main():
    create_stream(STREAM_NAME)

    while True:
        loop()
        time.sleep(1)
