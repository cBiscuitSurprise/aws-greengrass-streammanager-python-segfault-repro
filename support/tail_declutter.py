"""tail_declutter.py
declutters and colors the Greengrass V2 logs giving you access to your logs

Usage:
    python3 tail_declutter.py /greengrass/v2/logs/com.example.Component.log
"""

import re
import sys
import time


class ColorCodes:
    INFO = "\033[94m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    ENDC = "\033[0m"


def get_line_level(line: str, last_level: str):
    level_expression = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(,\d*)\]\[(?P<level>INFO|WARNING|ERROR)\s*\]"
    level = re.search(level_expression, line)
    if level is not None and level.group("level") is not None:
        return level.group("level")
    else:
        return last_level


def color(line: str, last_level: str):
    level = get_line_level(line, last_level)

    if level == "ERROR":
        line = f"{ColorCodes.ERROR}{line}{ColorCodes.ENDC}"
    elif level == "WARNING":
        line = f"{ColorCodes.WARNING}{line}{ColorCodes.ENDC}"
    elif level == "INFO":
        line = f"{ColorCodes.INFO}{line}{ColorCodes.ENDC}"

    return (line, level)


def declutter(line: str):
    prefix_expression = (
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d*)?Z \[(?:INFO|WARN|ERROR)\] \(Copier\) .+?: (?:stdout|stderr).\s"
    )
    suffix_expression = r"\.\s*\{(?:scriptName=.*?|serviceName=.*?|currentState=.*?)+\}"
    line = re.sub(prefix_expression, "", line)
    line = re.sub(suffix_expression, "", line)
    line = re.sub("^(?!\[)", "\t", line)
    return line


def tail(file_object):
    while True:
        line = file_object.readline()
        if not line or not line.endswith("\n"):
            time.sleep(0.1)
            continue
        yield line


if __name__ == "__main__":
    level = "None"
    with open(sys.argv[1], "r") as fid:
        try:
            line_generator = tail(fid)
            for line in line_generator:
                line = declutter(line)
                line, level = color(line, level)
                print(line, end="")
        except KeyboardInterrupt:
            pass
