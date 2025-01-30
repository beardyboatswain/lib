#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
import time

from extronlib.interface import EthernetServerInterface
from extronlib.system import Timer, Wait

import lib.utils.signals as signals

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection, AutoServerConnection
from lib.video.VideoControl import VideoControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import VideoMatrixDgx_dbg
dbg = debugger(VideoMatrixDgx_dbg, __name__)


class MatrixDgx(VideoControlProxyMeta):
    def __init__(self,
                 deviceTx: AutoEthernetConnection,
                 deviceRx: AutoServerConnection,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.deviceTx = deviceTx
        self.deviceRx = deviceRx

        self.deviceRxConnected = 0

        self.inSize = inSize
        self.outSize = outSize
        self.states = dict()
        self.fbFunctions = list()

        self.matchTiesFb = re.compile("SWITCH-L(VIDEO|AUDIO)I([0-9]{1,2})O([0-9]{1,2})")

        self.deviceTx.subscribe('Connected', self.txConnectEventHandler)
        self.deviceTx.subscribe('Disconnected', self.txConnectEventHandler)
        self.deviceTx.subscribe('ReceiveData', self.txRecieveDataEventHandler)

        self.deviceRx.subscribe('Connected', self.rxConnectEventHandler)
        self.deviceRx.subscribe('Disconnected', self.rxConnectEventHandler)
        self.deviceRx.subscribe('ReceiveData', self.rxRecieveDataEventHandler)

        self.addFbFunction(self.executeCallbackFunctions)

        self.refreshFbTimer = Timer(60, self.refreshTies)

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def refreshTies(self, timer: Timer, count: int):
        self.requestTie()

    def requestTie(self, nOut: int = None):
        if nOut:
            self.deviceTx.send("?INPUT-VIDEO,{}".format(nOut))
            dbg.print("TO Dgx: {}".format("?INPUT-VIDEO,{}".format(nOut)))
        else:
            for iOut in range(1, self.outSize + 1):
                self.deviceTx.send("?INPUT-VIDEO,{}".format(iOut))
                dbg.print("TO Dgx: {}".format("?INPUT-VIDEO,{}".format(iOut)))

    def setTie(self, nOut: int, nIn: int):
        self.deviceTx.send("CI{}O{}".format(nIn, nOut))
        self.requestTie(nOut=nOut)

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    def txConnectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.requestTie()
            dbg.print("DgxTx Connected!")
        elif (state == 'Disconnected'):
            dbg.print("DgxTx Disconnected!")

    def rxConnectEventHandler(self, client, state):
        dbg.print("Connection Handler: {} {}".format(client, state))
        if (state == 'Connected'):
            dbg.print("DgxRx Client Connected!")
        elif (state == 'Disconnected'):
            dbg.print("DgxTx Disconnected!")

    def recieveDataParser(self, rxLine: str):
        dataLines = rxLine
        dbg.print("rxParser recieved: {} ".format(dataLines))

        for rxLine in dataLines.splitlines():
            dbg.print("PARSE LINE: {}".format(rxLine))
            matchObjectVideoFb = self.matchTiesFb.search(rxLine)
            if matchObjectVideoFb:
                dbg.print("FOUND: {}".format(matchObjectVideoFb))
                inN = int(matchObjectVideoFb.group(2))
                outN = int(matchObjectVideoFb.group(3))
                self.states[outN] = inN
                self.executeCallbackFunctions(outN, inN)
                dbg.print("Dgx: out {} - in {}".format(outN, self.states[outN]))

        dbg.print("Dgx State {}".format(self.states))

    def txRecieveDataEventHandler(self, interface, data):
        dbg.print("DgxTx recieved: {} ".format(data.decode()))
        self.recieveDataParser(data.decode())

    def rxRecieveDataEventHandler(self, interface, data):
        dbg.print("DgxRx recieved: {} ".format(data.decode()))
        self.recieveDataParser(data.decode())
