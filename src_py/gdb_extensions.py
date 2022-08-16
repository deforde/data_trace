import argparse

DTRACE_LINE_PREFIX = "DTRACE: "

class TraceDataCommand(gdb.Command):
    def __init__(self):
        super(TraceDataCommand, self).__init__(
            "trace_data", gdb.COMMAND_USER
        )
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("desc", type=str, help="print json descriptor")

    def interpret_val(self, val):
        if val.type.code == gdb.TYPE_CODE_PTR:
            return self.interpret_val(val.dereference())
        return val

    def complete(self, text, word):
        return gdb.COMPLETE_SYMBOL

    def invoke(self, args, from_tty):
        ident = args
        val = gdb.parse_and_eval(args)
        val = self.interpret_val(val)
        print(f"{DTRACE_LINE_PREFIX}{ident} = {val}")

TraceDataCommand()
