#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

import lib.utils.signals as signals

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixWyrestorm(VideoControlProxyMeta):
    def __init__(self, device: AutoEthernetConnection):
        super().__init__()

        self.device = device
        self.states = dict()
        self.fbFunctions = list()

        self.matchTiesFb = re.compile("MP HDMIIN([0-9]{1,2}) HDMIOUT([0-9]{1,2})")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.addFbFunction(self.executeCallbackFunctions)

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def requestTie(self, nOut=None):
        if nOut:
            self.device.send("GET MP hdmiout{}\x0d\x0a".format(nOut))
        else:
            self.device.send("GET MP all\x0d\x0a")

    def setTie(self, nOut: int, nIn: int):
        self.device.send("SET SW hdmiin{} hdmiout{}\x0d\x0a".format(nIn, nOut))
        self.requestTie(nOut=nOut)

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connect'):
            self.requestTie()
            dbg.print("Wyrestorm Connected!")

    def rxParser(self, rxLine: str):
        dataLines = rxLine
        dbg.print("rxParser recieved: {} ".format(dataLines))

        for rxLine in dataLines.splitlines():
            dbg.print("PARSE LINE: {}".format(rxLine))
            matchObjectVideoFb = self.matchTiesFb.search(rxLine)
            if matchObjectVideoFb:
                dbg.print("FOUND: {}".format(matchObjectVideoFb))
                inN = int(matchObjectVideoFb.group(1))
                outN = int(matchObjectVideoFb.group(2))
                self.states[outN] = inN
                self.executeCallbackFunctions(outN, inN)
                dbg.print("Wyrestorm: out {} - in {}".format(outN, self.states[outN]))

        dbg.print("wyrestormState {}".format(self.states))

    def rxEventHandler(self, interface, data):
        dbg.print("wyrestorm recieved: {} ".format(data.decode()))

        self.rxParser(data.decode())
