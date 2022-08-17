import argparse
import json
import socket
import struct
import gdb

UDP_DATA_PORT = 5555  # TODO: This is defined twice


class TraceDataCommand(gdb.Command):
    def __init__(self):
        super(TraceDataCommand, self).__init__("trace_data", gdb.COMMAND_USER)
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("desc", type=str, help="print json descriptor")

    def complete(self, text, word):
        return gdb.COMPLETE_SYMBOL

    def invoke(self, args, from_tty):
        desc = json.loads(args)
        server_port = int(desc["server_port"])
        ident = desc["id"]
        if "@" in ident:
            splits = ident.split("@")
            ident = splits[0]
            arr_len = splits[1]
            val = gdb.parse_and_eval(ident)
            arr_len = gdb.parse_and_eval(arr_len)
            arr_len = int(arr_len)
            assert val.type.code == gdb.TYPE_CODE_PTR
            val = val.cast(
                gdb.parse_and_eval(
                    f"({val.type.target().name}[{arr_len}]*){ident}"
                ).type
            ).dereference()
        else:
            val = gdb.parse_and_eval(ident)
            while val.type.code == gdb.TYPE_CODE_PTR:
                val = val.dereference()
        payload = bytes(f"{ident}:{val}", encoding="utf-8")
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
            sock.sendto(struct.pack("=I", len(payload)), ("127.0.0.1", server_port))
            sock.sendto(payload, ("127.0.0.1", server_port))


TraceDataCommand()
