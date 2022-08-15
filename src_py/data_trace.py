#!/usr/bin/env python3

from os import path
import subprocess as sp

from matplotlib import pyplot as plt

PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
EXEC_PATH = path.join(PATH, "..", "build", "data_trace")
WATCH_VARS = ["y"]

with open(GDB_CMDS_FILEPATH, mode="w", encoding="utf-8") as gdb_cmds_file:
    gdb_cmds_file.write(
        "set logging overwrite on\n"
        "set logging redirect on\n"
        "set logging file data_trace_out.txt\n"
        "set logging enabled on\n"
        "watch y\n"
        "command\n"
        "silent\n"
        "printf \"y=%f\\n\",y\n"
        "cont\n"
        "end\n"
        "run\n"
        "quit\n"
    )

sp.run(
    [
        "gdb",
        "-x",
        GDB_CMDS_FILEPATH,
        EXEC_PATH,
    ],
    check=True,
)
