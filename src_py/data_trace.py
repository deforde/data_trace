#!/usr/bin/env python3

from os import path
import subprocess as sp
import argparse
import json

from matplotlib import pyplot as plt


PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
GDB_EXTENSIONS = path.join(PATH, "gdb_extensions.py")
DATA_TRACE_OUT_FILEPATH = path.join(PATH, "data_trace_out.txt")
DTRACE_LINE_PREFIX = "DTRACE: "

parser = argparse.ArgumentParser()
parser.add_argument("config", type=str, help="config file")
args = parser.parse_args(["/home/danielforde/dev/deforde/data_trace/src_py/config.json"])

config = {}
with open(args.config, mode="r", encoding="utf-8") as config_file:
    config = json.load(config_file)
app_path = config["app"]
app_args = config["args"]

with open(GDB_CMDS_FILEPATH, mode="w", encoding="utf-8") as gdb_cmds_file:
    gdb_cmds_file.write(
        f"source {GDB_EXTENSIONS}\n"
        "set breakpoint pending on\n"
        "set print elements unlimited\n"
        "set print repeats unlimited\n"
        "set pagination off\n"
        "set logging overwrite on\n"
        "set logging redirect on\n"
        f"set logging file {DATA_TRACE_OUT_FILEPATH}\n"
        "set logging enabled on\n"
    )
    if "globals" in config:
        for global_dict in config["globals"]:
            idents = global_dict["ids"]
            for ident in idents:
                gdb_cmds_file.write(
                    f"watch {ident}\n"
                    "commands\n"
                    "silent\n"
                    f'trace_data {ident}\n'
                    "c\n"
                    "end\n"
                )
    if "locals" in config:
        for local_dict in config["locals"]:
            loc = local_dict["loc"]
            idents = local_dict["ids"]
            gdb_cmds_file.write(
                f"b {loc}\n"
                "commands\n"
                "silent\n"
            )
            for ident in idents:
                gdb_cmds_file.write(
                    f'trace_data {ident}\n'
                )
            gdb_cmds_file.write(
                "c\n"
                "end\n"
            )
    if "statics" in config:
        for static_dict in config["statics"]:
            ident = static_dict["id"]
            src_file = static_dict["file"]
            gdb_cmds_file.write(
                f"watch '{src_file}'::{ident}\n"
                "commands\n"
                "silent\n"
                f'trace_data {ident}\n'
                "c\n"
                "end\n"
            )
    gdb_cmds_file.write(
        "r\n"
        "q\n"
    )

sp.run(
    [
        "gdb",
        "-x",
        GDB_CMDS_FILEPATH,
        "--args",
        app_path,
    ] + app_args,
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
        val = splits[1].strip()
        if val[0] == "{":
            vals = val[1:-1].split(",")
            data[ident] = [float(v) for v in vals]
        else:
            if ident not in data:
                data[ident] = []
            data[ident].append(float(val))

fig = plt.figure()
fig.set_size_inches(w=16, h=9)
for var, vals in data.items():
    plt.plot(vals, label=var)
fig.legend()
plt.savefig(path.join(PATH, "dtrace.png"))
