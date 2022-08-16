import argparse
import json
import gdb

DTRACE_LINE_PREFIX = "DTRACE: "

class TraceDataCommand(gdb.Command):
    def __init__(self):
        super(TraceDataCommand, self).__init__(
            "trace_data", gdb.COMMAND_USER
        )
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("desc", type=str, help="print json descriptor")

    def complete(self, text, word):
        return gdb.COMPLETE_SYMBOL

    def invoke(self, args, from_tty):
        desc = json.loads(args)
        ident = desc["id"]
        if "@" in ident:
            splits = ident.split("@")
            ident = splits[0]
            len = splits[1]
            val = gdb.parse_and_eval(ident)
            len = gdb.parse_and_eval(len)
            len = int(len)
            assert val.type.code == gdb.TYPE_CODE_PTR
            val = val.cast(gdb.parse_and_eval(f"({val.type.target().name}[{len}]*){ident}").type).dereference()
            print(f"{DTRACE_LINE_PREFIX}{ident} = {val}")
            return
        val = gdb.parse_and_eval(ident)
        while val.type.code == gdb.TYPE_CODE_PTR:
            val = val.dereference()
        print(f"{DTRACE_LINE_PREFIX}{ident} = {val}")


TraceDataCommand()
