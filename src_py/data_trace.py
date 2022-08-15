#!/usr/bin/env python3

from os import path, remove
import subprocess as sp
import argparse
import json

from matplotlib import pyplot as plt


PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
DATA_TRACE_OUT_FILEPATH = path.join(PATH, "data_trace_out.txt")
DTRACE_LINE_PREFIX = "DTRACE: "

parser = argparse.ArgumentParser()
parser.add_argument("config", type=str, help="config file")
args = parser.parse_args(["/home/danielforde/dev/deforde/data_trace/src_py/config.json"])

config = {}
with open(args.config, mode="r", encoding="utf-8") as config_file:
    config = json.load(config_file)
app_path = config["app"]
watch_vars = config["watch"]

with open(GDB_CMDS_FILEPATH, mode="w", encoding="utf-8") as gdb_cmds_file:
    gdb_cmds_file.write(
        "set logging overwrite on\n"
        "set logging redirect on\n"
        f"set logging file {DATA_TRACE_OUT_FILEPATH}\n"
        "set logging enabled on\n"
    )
    for watch_var_dict in watch_vars:
        ident = watch_var_dict["id"]
        fmt_str = watch_var_dict["fmt"]
        kind = watch_var_dict["kind"]
        if kind == "global":
            gdb_cmds_file.write(
                f"watch {ident}\n"
            )
        elif kind == "local":
            loc = watch_var_dict["loc"]
            gdb_cmds_file.write(
                f"break {loc}\n"
            )
        gdb_cmds_file.write(
            f"commands\n"
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
        app_path,
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

# remove(DATA_TRACE_OUT_FILEPATH)
# remove(GDB_CMDS_FILEPATH)
