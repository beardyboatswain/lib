#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
import threading

from extronlib.system import Timer, Wait

from lib.utils.system_init import InitModule
import lib.utils.signals as signals
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixInfobitHxxHAW(VideoControlProxyMeta):
    """
    Control Class fro Infobit iMatrix H44HAW-H88HAW
    """
    """
    cmd:
    7B 7B 01 02 [input] [output] [chksum] 7D 7D
    input:
    1 - 00
    2 - 01
    3 - 02
    4 - 03
    5 - 04
    6 - 05
    7 - 06
    8 - 07

    output:
    1 - 00000001 - 01
    2 - 00000010 - 02
    3 - 00000100 - 04
    4 - 00001000 - 08
    5 - 00010000 - 10
    6 - 00100000 - 20
    7 - 01000000 - 40
    8 - 10000000 - 80

    chksum:
    lust byte of [F3 + input + output]

    answ:
    7B 7B 11 08 00 01 02 03 04 05 06 07 25 7D 7D
    7B 7B 11 08 [out1] [out2] [out3] [out4] [out5] [out6] [out7] [out8] [chksum] 7D 7D
    outN - coresponding input


    OR String Format:

    GET OUT4 VIDEO%0d%0a    ->  OUT4 VIDEO IN1
    SET IN1 VIDEO OUT4%0d%0a   ->    IN1 VIDEO OUT4
    """

    def __init__(self,
                 device: AutoEthernetConnection,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.device = device
        self.states = dict()
        self.inSize = inSize
        self.outSize = outSize

        self.matchSingleTieAFb = re.compile("IN([0-9]{1,2}) VIDEO OUT([0-9]{1,2})")
        self.matchSingleTieBFb = re.compile("OUT([0-9]{1,2}) VIDEO IN([0-9]{1,2})")

        self.device.subscribe('Connected', self.connect_event_handler)
        self.device.subscribe('Disconnected', self.connect_event_handler)
        self.device.subscribe('ReceiveData', self.rx_event_handler)
        self.device.connect()

        # self.add_callback_functions(self.execute_callback_functions)

        self.refreshFbTimer = Timer(60, self.refresh_ties)

    # def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
    #     if callable(fbCallbackFunc):
    #         self.fbFunctions.append(fbCallbackFunc)
    #     else:
    #         raise TypeError("Param 'callbackFb' is not Callable")

    # def executeFbFunctions(self, nOut: int, nIn: int):
    #     for cFunc in self.fbFunctions:
    #         cFunc(nOut, nIn)

    def refresh_ties(self, timer: Timer, count: int):
        for i_out in range(1, self.outSize + 1):
            self.request_tie(i_out)
        # self.send_feedback()

    def request_tie(self, n_out: int) -> None:
        cmd = "GET OUT{} VIDEO\x0d\x0a".format(n_out).encode('ascii')
        self.device.send(cmd)
        # self.send_feedback()

    def set_tie(self, n_out: int, n_in: int):
        if (1 <= n_in <= self.inSize) and (1 <= n_out <= self.outSize):
            dbg.print("Set tie: out<{}> - in<{}>".format(n_out, n_in))
            cmd = "SET IN{} VIDEO OUT{}\x0d\x0a".format(n_in, n_out).encode('ascii')
            self.device.send(cmd)
            update_state_tread = threading.Thread(target=self.update_state, args=(n_out, n_in))
            update_state_tread.start()
            # self.update_state(n_out, n_in)
        @Wait(5)
        def request_time_timer():
            request_tie_tread = threading.Thread(target=self.request_tie, args=(n_out,))
            request_tie_tread.start()
            # self.request_tie(n_out)

    def get_tie(self, n_out: int) -> int:
        return self.states.get(n_out)

    def add_callback_functions(self, fb_callback_function: Callable[[int, int], None]):
        if (callable(fb_callback_function)):
            self.callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def execute_callback_functions(self, n_out: int, n_in: int):
        dbg.print("Run fbCallback: out<{}> - in<{}>".format(n_out, n_in))
        for func in self.callback_functions:
            func(n_out, n_in)

    def connect_event_handler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connect'):
            self.request_tie()
            dbg.print("Infobit Connected!")

    def update_state(self, n_out: int, n_in: int):
        if (self.states.get(n_out) == n_in):
            return
        else:
            self.states[n_out] = n_in
            self.send_feedback(n_out)
            self.execute_callback_functions(n_out, self.states[n_out])
        
    def rx_parser(self, rxLines: str):
        dataLines = rxLines
        # dbg.print("rxParser recieved lines:")
        # dbg.print("Type: {}".format(type(dataLines.split("\x0d"))))
        # dbg.print(dataLines.split("\x0d"))

        for rxLine in dataLines.split("\x0d"):
            dbg.print("Analise string: <{}>".format(rxLine))

            matchObjectSingleTieAFb = self.matchSingleTieAFb.search(rxLine)
            matchObjectSingleTieBFb = self.matchSingleTieBFb.search(rxLine)

            if matchObjectSingleTieAFb:
                n_in = int(matchObjectSingleTieAFb.group(1))
                n_out = int(matchObjectSingleTieAFb.group(2))
                self.update_state(n_out, n_in)
            elif matchObjectSingleTieBFb:
                n_in = int(matchObjectSingleTieBFb.group(2))
                n_out = int(matchObjectSingleTieBFb.group(1))
                self.update_state(n_out, n_in)
            elif (len(rxLine) == 15) and rxLine.startswith("\x7B\x7B\x11\x08") and rxLine.endswith("\x7D\x7D"):
                ties = rxLine[4:12]
                for i in range(0, len(ties)):
                    n_out = i + 1
                    n_in = ord(ties[i]) + 1
                    self.update_state(n_out, n_in)


    def rx_event_handler(self, interface, data):
        # dbg.print("From Infobit recieved: ")
        # dbg.print(data)
        self.rx_parser(data.decode())

    def send_feedback(self, n_out: int = None):
        if n_out:
            n_in = self.states[n_out]
            if (0 <= n_in <= self.inSize) and (0 < n_out <= self.outSize):
                self.execute_callback_functions(n_out, n_in)
        else:
            for i_out in self.states.keys():
                n_in = self.states[i_out]
                if (0 <= n_in <= self.inSize) and (0 < n_out <= self.outSize):
                    self.execute_callback_functions(n_out, n_in)
