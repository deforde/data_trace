#!/usr/bin/env python3

from os import path
import subprocess as sp
import argparse
import json
import socket
import logging
import concurrent.futures
import struct
import pickle

from matplotlib import pyplot as plt


PATH = path.dirname(path.abspath(__file__))
GDB_CMDS_FILEPATH = path.join(PATH, "gdb_cmds")
GDB_EXTENSIONS = path.join(PATH, "gdb_extensions.py")
PLOT_FILENAME = "dtrace.svg"

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
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", server_port))
        sock.sendall(struct.pack("=I", 0))


def _write_gdb_cmds_file(config: dict, server_port: int):
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
                        f'trace_data {{"id": "{ident}", "server_port": {server_port}}}\n'
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
                        f'trace_data {{"id": "{ident}", "server_port": {server_port}}}\n'
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
                    f'trace_data {{"id": "{ident}", "server_port": {server_port}}}\n'
                    "c\n"
                    "end\n"
                )
        gdb_cmds_file.write("r\n" "q\n")


parser = argparse.ArgumentParser()
parser.add_argument("config", type=str, help="config file")
args = parser.parse_args()

config = {}
with open(args.config, mode="r", encoding="utf-8") as config_file:
    config = json.load(config_file)
app_path = config["app"]
app_args = config["args"]

data = {}
with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    server_port = sock.getsockname()[1]
    logger.info("super-process server listening on port: %i", server_port)
    sock.listen(1)

    _write_gdb_cmds_file(config=config, server_port=server_port)

    executor = concurrent.futures.ProcessPoolExecutor()
    future = executor.submit(
        _subprocess,
    )

    while future.running():
        logger.debug("accepting a connection from the sub-process")
        conn, addr = sock.accept()
        with conn:
            logger.debug(
                "connection accepted from sub-process, remote endpoint: %s", addr
            )
            (payload_cnt,) = struct.unpack("=I", _recv_all(conn, 4))
            # A payload count of zero is used to indicate the end of the data stream
            if payload_cnt == 0:
                break
            for _ in range(payload_cnt):
                (payload_len,) = struct.unpack("=I", _recv_all(conn, 4))
                logger.debug("payload_len received: %i", payload_len)
                payload = bytes.decode(_recv_all(conn, payload_len), encoding="utf-8")
                logger.debug("payload received: %s", payload)
                ident, val = payload.split(":")
                if val[0] == "{":
                    vals = val[1:-1].split(",")
                    data[ident] = [float(v) for v in vals]
                else:
                    if ident not in data:
                        data[ident] = []
                    data[ident].append(float(val))
        logger.debug("disconnected from the sub-process")
logger.info("super-process server socket closed")

for key, arr in data.items():
    logger.debug("key = %s, len = %i", key, len(arr))
    logger.info("pickling data for identifier: '%s'", key)
    with open(path.join(PATH, f"dtrace_{key}.pickle"), mode="wb") as data_file:
        pickle.dump(arr, data_file)

logger.info("writing traced data plot to file: '%s'", PLOT_FILENAME)
plt.style.use("ggplot")
fig = plt.figure()
fig.set_size_inches(w=16, h=9)
for var, vals in data.items():
    plt.plot(vals, label=var)
fig.legend()
plt.savefig(path.join(PATH, PLOT_FILENAME))
