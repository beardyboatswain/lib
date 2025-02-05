#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

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

        self.fbFunctions = list()

        self.matchSingleTieAFb = re.compile("IN([0-9]{1,2}) VIDEO OUT([0-9]{1,2})")
        self.matchSingleTieBFb = re.compile("OUT([0-9]{1,2}) VIDEO IN([0-9]{1,2})")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.addFbFunction(self.executeCallbackFunctions)

        self.refreshFbTimer = Timer(30, self.refreshTies)

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def refreshTies(self, timer: Timer, count: int):
        for iOut in range(1, self.outSize + 1):
            self.requestTie(iOut)
        self.sendFeedbackForAllOuts()

    def requestTie(self, nOut: int) -> None:
        cmd = "GET OUT{} VIDEO\x0d\x0a".format(nOut).encode('ascii')
        self.device.send(cmd)
        self.sendFeedbackForAllOuts()

    def setTie(self, nOut: int, nIn: int):
        if (1 <= nIn <= self.inSize) and (1 <= nOut <= self.outSize):
            cmd = "SET IN{} VIDEO OUT{}\x0d\x0a".format(nIn, nOut).encode('ascii')
            self.device.send(cmd)
        self.requestTie(nOut)

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        dbg.print("Run fbCallback: out<{}> - in<{}>".format(nOut, nIn))
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connect'):
            self.requestTie()
            dbg.print("Infobit Connected!")

    def rxParser(self, rxLines: str):
        dataLines = rxLines
        dbg.print("rxParser recieved lines:")
        dbg.print("Type: {}".format(type(dataLines.split("\x0d"))))
        dbg.print(dataLines.split("\x0d"))

        for rxLine in dataLines.split("\x0d"):
            dbg.print("Analise string: <{}>".format(rxLine))

            matchObjectSingleTieAFb = self.matchSingleTieAFb.search(rxLine)
            matchObjectSingleTieBFb = self.matchSingleTieBFb.search(rxLine)

            if matchObjectSingleTieAFb:
                inN = int(matchObjectSingleTieAFb.group(1))
                outN = int(matchObjectSingleTieAFb.group(2))
                self.states[outN] = inN
                self.executeCallbackFunctions(outN, inN)
            elif matchObjectSingleTieBFb:
                inN = int(matchObjectSingleTieBFb.group(2))
                outN = int(matchObjectSingleTieBFb.group(1))
                self.states[outN] = inN
                self.executeCallbackFunctions(outN, inN)
            elif (len(rxLine) == 15) and rxLine.startswith("\x7B\x7B\x11\x08") and rxLine.endswith("\x7D\x7D"):
                ties = rxLine[4:12]
                for i in range(0, len(ties)):
                    outN = i + 1
                    inN = ord(ties[i]) + 1
                    self.states[outN] = inN
                    # self.executeCallbackFunctions(outN, inN)
                self.sendFeedbackForAllOuts()
        dbg.print("Infobit State {}".format(self.states))

    def rxEventHandler(self, interface, data):
        # dbg.print("From Infobit recieved: ")
        # dbg.print(data)
        self.rxParser(data.decode())

    def sendFeedbackForAllOuts(self):
        for iOut in self.states:
            inN = self.states[iOut]
            outN = iOut
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.executeCallbackFunctions(outN, inN)
