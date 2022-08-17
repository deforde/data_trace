#!/usr/bin/env python3

from os import path
import subprocess as sp
import argparse
import json
import socket
import logging
import concurrent.futures
import struct

from matplotlib import pyplot as plt


PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
GDB_EXTENSIONS = path.join(PATH, "gdb_extensions.py")
UDP_DATA_PORT = 5555  # TODO: This is defined twice
SYNC_COUNTER_MAX = 32767  # TODO: This is defined twice

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)


def _recv_all(sock: socket.socket, size: int) -> bytes:
    remaining = size
    data = bytes()
    while remaining > 0:
        rx_data = sock.recv(remaining)
        remaining -= len(rx_data)
        data += rx_data
    return data


def _subprocess():
    logger.info("running gdb")
    sp.run(
        [
            "gdb",
            "-x",
            GDB_CMDS_FILEPATH,
            "--args",
            app_path,
        ]
        + app_args,
        check=True,
    )
    logger.info("gdb complete")
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
        sock.sendto(struct.pack("=II", 0, 0), ("127.0.0.1", UDP_DATA_PORT))


parser = argparse.ArgumentParser()
parser.add_argument("config", type=str, help="config file")
args = parser.parse_args(
    ["/home/danielforde/dev/deforde/data_trace/src_py/config.json"]
)

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
    )
    if "globals" in config:
        for global_dict in config["globals"]:
            idents = global_dict["ids"]
            for ident in idents:
                gdb_cmds_file.write(
                    f"watch {ident}\n"
                    "commands\n"
                    "silent\n"
                    f'trace_data {{"id": "{ident}", "server_port": {UDP_DATA_PORT}}}\n'
                    "c\n"
                    "end\n"
                )
    if "locals" in config:
        for local_dict in config["locals"]:
            loc = local_dict["loc"]
            idents = local_dict["ids"]
            gdb_cmds_file.write(f"b {loc}\n" "commands\n" "silent\n")
            for ident in idents:
                gdb_cmds_file.write(
                    f'trace_data {{"id": "{ident}", "server_port": {UDP_DATA_PORT}}}\n'
                )
            gdb_cmds_file.write("c\n" "end\n")
    if "statics" in config:
        for static_dict in config["statics"]:
            ident = static_dict["id"]
            src_file = static_dict["file"]
            gdb_cmds_file.write(
                f"watch '{src_file}'::{ident}\n"
                "commands\n"
                "silent\n"
                f'trace_data {{"id": "{ident}", "server_port": {UDP_DATA_PORT}}}\n'
                "c\n"
                "end\n"
            )
    gdb_cmds_file.write("r\n" "q\n")

data = {}
with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
    sock.bind(("127.0.0.1", UDP_DATA_PORT))

    executor = concurrent.futures.ProcessPoolExecutor()
    future = executor.submit(
        _subprocess,
    )

    exp_sync_counter = 0
    while future.running():
        sync_counter, payload_len = struct.unpack("=II", _recv_all(sock, 8))
        # A payload length of zero is used to indicate the end of the data stream
        if payload_len == 0:
            break
        if sync_counter != exp_sync_counter:
            logger.error(
                "received unexpected sync_counter, expected: %i, got: %i, probable data loss",
                exp_sync_counter,
                sync_counter,
            )
        exp_sync_counter = (sync_counter + 1) % SYNC_COUNTER_MAX
        logger.debug("payload_len received: %i", payload_len)
        payload = bytes.decode(_recv_all(sock, payload_len), encoding="utf-8")
        logger.debug("payload received: %s", payload)
        ident, val = payload.split(":")
        if val[0] == "{":
            vals = val[1:-1].split(",")
            data[ident] = [float(v) for v in vals]
        else:
            if ident not in data:
                data[ident] = []
            data[ident].append(float(val))
logger.info("super-process server socket closed")

plt.style.use("ggplot")
fig = plt.figure()
fig.set_size_inches(w=16, h=9)
for var, vals in data.items():
    plt.plot(vals, label=var)
fig.legend()
plt.savefig(path.join(PATH, "dtrace.svg"))
