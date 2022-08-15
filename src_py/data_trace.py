#!/usr/bin/env python3

from os import path, remove
import subprocess as sp

from matplotlib import pyplot as plt

PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
DATA_TRACE_OUT_FILEPATH = path.join(PATH, "data_trace_out.txt")
EXEC_PATH = path.join(PATH, "..", "build", "data_trace")
DTRACE_LINE_PREFIX = "DTRACE: "
WATCH_VARS = [
    {
        "id": "x",
        "fmt": "%f",
    },
    {
        "id": "y",
        "fmt": "%f",
    },
]

with open(GDB_CMDS_FILEPATH, mode="w", encoding="utf-8") as gdb_cmds_file:
    gdb_cmds_file.write(
        "set logging overwrite on\n"
        "set logging redirect on\n"
        f"set logging file {DATA_TRACE_OUT_FILEPATH}\n"
        "set logging enabled on\n"
    )
    for watch_var_dict in WATCH_VARS:
        ident = watch_var_dict["id"]
        fmt_str = watch_var_dict["fmt"]
        gdb_cmds_file.write(
            f"watch {ident}\n"
            "command\n"
            "silent\n"
            f'printf "{DTRACE_LINE_PREFIX}{ident}={fmt_str}\\n",{ident}\n'
            "cont\n"
            "end\n"
        )
    gdb_cmds_file.write(
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

data = {}
with open(DATA_TRACE_OUT_FILEPATH, mode="r", encoding="utf-8") as dtrace_out_file:
    for line in dtrace_out_file:
        if not line.startswith(DTRACE_LINE_PREFIX):
            continue
        line = line[len(DTRACE_LINE_PREFIX):]
        splits = line.split("=")
        ident = splits[0]
        val = float(splits[1].strip())
        if ident not in data:
            data[ident] = []
        data[ident].append(val)

fig = plt.figure()
fig.set_size_inches(w=16, h=9)
for var, vals in data.items():
    plt.plot(vals, label=var)
fig.legend()
plt.savefig(path.join(PATH, "dtrace.png"))

remove(DATA_TRACE_OUT_FILEPATH)
remove(GDB_CMDS_FILEPATH)
