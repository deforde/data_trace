import argparse
import json
import socket
import struct
import gdb


class TraceDataCommand(gdb.Command):
    def __init__(self):
        super(TraceDataCommand, self).__init__("trace_data", gdb.COMMAND_USER)
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("desc", type=str, help="print json descriptor")

    def complete(self, text, word):
        return gdb.COMPLETE_SYMBOL

    def _decay_type(self, val):
        while val.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
            val = val.dereference()
        return val

    def invoke(self, args, from_tty):
        desc = json.loads(args)
        server_port = int(desc["server_port"])
        ident = desc["id"]
        payloads = []
        if "@" in ident:
            ident, arr_len = ident.split("@")
            val = gdb.parse_and_eval(ident)
            arr_len = gdb.parse_and_eval(arr_len)
            arr_len = int(arr_len)
            assert val.type.strip_typedefs().code == gdb.TYPE_CODE_PTR
            val = val.cast(
                gdb.parse_and_eval(
                    f"({val.type.strip_typedefs().target().name}[{arr_len}]*){ident}"
                ).type.strip_typedefs()
            ).dereference()
            payloads.append(bytes(f"{ident}:{val}", encoding="utf-8"))
        else:
            val = gdb.parse_and_eval(ident)
            val = self._decay_type(val)
            if val.type.strip_typedefs().code == gdb.TYPE_CODE_STRUCT:
                for field in val.type.strip_typedefs().fields():
                    field_val = self._decay_type(val[field.name])
                    payloads.append(bytes(f"{ident}.{field.name}:{field_val}", encoding="utf-8"))
            else:
                payloads.append(bytes(f"{ident}:{val}", encoding="utf-8"))
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as sock:
            sock.connect(("127.0.0.1", server_port))
            sock.sendall(struct.pack("=I", len(payloads)))
            for payload in payloads:
                sock.sendall(struct.pack("=I", len(payload)))
                sock.sendall(payload)


TraceDataCommand()
