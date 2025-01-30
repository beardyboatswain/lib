#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from extronlib.system import ProgramLog
import lib.utils.traceServer as tracer


dbg_modes = {"no": 0, "lite": 1, "time": 2, "date": 3}


class timeStamp:
    def __init__(self, precision=3):
        self.precision = precision if precision > 0 and precision <= 6 else 3

    def time(self):
        startTimeHMS = time.strftime("%H:%M:%S")
        startTimeMS = int(round(time.time(), 3) % 1 * pow(10, 3))
        prec = str(3)
        return "{}.{:0{}}".format(startTimeHMS, startTimeMS, prec)

    def __repr__(self):
        return self.time()

    def __str__(self):
        return self.time()


class debugger:
    def __init__(self, mode=2, module="DBG", file='', program_log: bool = False):
        if type(mode) is str and mode in dbg_modes.keys():
            self.mode = dbg_modes[mode]
        elif type(mode) is int and mode in dbg_modes.values():
            self.mode = mode
        else:
            self.mode = 1
        self.module = module
        self.file = file
        self.program_log = program_log

    def print(self, dbg_string):
        if self.mode == 0:
            return
        else:
            if self.mode == 1:
                dbg_time_prefix = ""
            elif self.mode == 2:
                dbg_time_prefix = "{}".format(timeStamp())
            elif self.mode == 3:
                dbg_time_prefix = "{} {}".format(time.strftime("%Y-%m-%d"), timeStamp())
            dbg_end = ""
            dStr = dbg_time_prefix + " | " + self.module + " | " + str(dbg_string) + dbg_end
            print(dStr)
            if self.program_log:
                ProgramLog(dStr, 'info')
            return dStr

    def printStatus(self, handler):
        def printWrapped(command, value, qualifier):
            self.print('FB: C[{}] V[{}] - Q[{}]'.format(command, value, qualifier))
            handler(command, value, qualifier)
        return printWrapped


class debuggerNet(debugger):
    def __init__(self, mode=2, module="DBG", file='', program_log: bool = False):
        super().__init__(mode, module, file, program_log)

    def print(self, dbg_string):
        res = super().print(dbg_string)
        if (res):
            tracer.Print(res)


# Print Subscribe Status Update for extron library modules
def printStatus(handler):
    def printWrapped(command, value, qualifier):
        print('FB: C[{}] V[{}] - Q[{}]'.format(command, value, qualifier))
        handler(command, value, qualifier)
    return printWrapped
