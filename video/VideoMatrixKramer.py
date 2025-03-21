#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

from lib.utils.system_init import InitModule

import lib.utils.signals as signals

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixKramer(object):
    def __init__(self, device: AutoEthernetConnection):
        self.device = device

        self.devID = "01"
        self.kramerRxBuf = str()
        self.kramerStates = dict()

        self.fbFunctions = list()

        self.kramerMatchVideoFb = re.compile("~([0-9]{2}@)VID ([0-9]{1,2})>([0-9]{1,2})")
        self.kramerMatchTiesFb = re.compile("(([0-9]{1,2})>([0-9]{1,2}))")

        self.device.subscribe('Connected', self.kramerConnectEventHandler)
        self.device.subscribe('Disconnected', self.kramerConnectEventHandler)
        self.device.subscribe('ReceiveData', self.kramerRxEventHandler)
        self.device.connect()

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def requestTies(self):
        self.device.send("#VID? *\x0d\x0a")

    def setTie(self, nOut: int, nIn: int):
        self.device.send("#VID {}>{}\x0d\x0a".format(nIn, nOut))

    def getTie(self, nOut: int) -> int:
        return self.kramerStates.get(nOut)

    def kramerConnectEventHandler(self, interface, state):
        if (state == 'Connect'):
            self.device.send("#VID? *\x0d\x0a")
            dbg.print("It is kramer Online")

    def kramerRxParser(self, rxLine: str):
        dataLines = rxLine

        for rxLine in dataLines.splitlines():
            kramerMatchObjectVideoFb = self.kramerMatchVideoFb.search(rxLine)
            if kramerMatchObjectVideoFb:
                kramerMatchObjectTiesFb = self.kramerMatchTiesFb.findall(rxLine)
                dbg.print("Ties MatchObject: {}".format(kramerMatchObjectTiesFb))
                if kramerMatchObjectTiesFb:
                    for mO in kramerMatchObjectTiesFb:
                        self.kramerStates[int(mO[2])] = int(mO[1])
                        self.executeFbFunctions(int(mO[2]), int(mO[1]))
                    dbg.print("kramerState {}".format(self.kramerStates))

    def kramerRxEventHandler(self, interface, data):
        dbg.print("kramer recieved from [{}]: {} ".format(interface, data.decode()))

        self.kramerRxBuf += data.decode()

        while (self.kramerRxBuf.find("\x0d\x0a") > -1):
            self.kramerRxParser(self.kramerRxBuf.partition("\x0d\x0a")[0])
            self.kramerRxBuf = self.kramerRxBuf.partition("\x0d\x0a")[2]


class VideoControlProxyKramer(VideoControlProxyMeta):
    def __init__(self,
                 device: MatrixKramer):
        self._dev = device

        self._fbCallbackFunctions = list()

        self._dev.addFbFunction(self.execute_callback_functions)

    def set_tie(self, nOut: int, nIn: int):
        self._dev.setTie(nOut=nOut, nIn=nIn)

    def get_tie(self, nOut: int) -> int:
        return self._dev.getTie(nOut=nOut)

    def add_callback_functions(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self._fbCallbackFunctions.append(fbCallbackFunction)

    def execute_callback_functions(self, nOut: int, nIn: int):
        for func in self._fbCallbackFunctions:
            func(nOut, nIn)

        if (nOut == 1) and ((nIn == 5) or (nIn == 6)):
            signals.emit("*", signal="ActiveCodec", params={"codec": "zoom"})
            dbg.print("ZOOM: nOut={} - nIn={}".format(nOut, nIn))
        elif (nOut == 1) and ((nIn == 3) or ((nIn == 4))):
            signals.emit("*", signal="ActiveCodec", params={"codec": "cisco"})
            dbg.print("CISCO: nOut={} - nIn={}".format(nOut, nIn))
