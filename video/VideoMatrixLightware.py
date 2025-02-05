#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

import lib.utils.signals as signals

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixLightware(VideoControlProxyMeta):
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

        self.matchAllTiesFb = re.compile("pr \/MEDIA\/XP\/VIDEO.DestinationConnectionStatus=((?:I{0,1}[0-9]{1,2};){24})")
        self.matchSingleTiesFb = re.compile("I{0,1}([0-9]{1,2});")

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

    def requestTie(self):
        self.device.send("GET /MEDIA/XP/VIDEO.DestinationConnectionStatus\x0d\x0a")

    def setTie(self, nOut: int, nIn: int):
        if (nIn == 0):
            self.device.send("CALL /MEDIA/XP/VIDEO:switch(0:O{})\x0d\x0a".format(nOut))
        else:
            self.device.send("CALL /MEDIA/XP/VIDEO:switch(I{}:O{})\x0d\x0a".format(nIn, nOut))

        self.requestTie()

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
            dbg.print("Lightware Connected!")

    def rxParser(self, rxLine: str):
        dataLines = rxLine
        dbg.print("rxParser recieved: {} ".format(dataLines))

        for rxLine in dataLines.splitlines():
            matchObjectAllVideoFb = self.matchAllTiesFb.search(rxLine)
            if matchObjectAllVideoFb:
                allTiesFb = matchObjectAllVideoFb.group(1)
                matchObjectSingleVideoFb = self.matchSingleTiesFb.findall(allTiesFb)
                for outN in range(1, self.outSize + 1):
                    self.states[outN] = int(matchObjectSingleVideoFb[outN - 1])
                    inN = self.states[outN]
                    self.executeCallbackFunctions(outN, inN)
                    dbg.print("Lightware: out {} - in {}".format(outN, inN))

        dbg.print("LightwareState {}".format(self.states))

    def rxEventHandler(self, interface, data):
        dbg.print("Lightware recieved: {} ".format(data.decode()))

        self.rxParser(data.decode())
