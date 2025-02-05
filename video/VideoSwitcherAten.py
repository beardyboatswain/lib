#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib.system import Timer

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import SwitcherControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class SwitcherAtenUC3430(SwitcherControlProxyMeta):
    """
    Control Class fro Switcher Aten UC3430
    """
    def __init__(self,
                 device: AutoEthernetConnection,
                 inSize: int):
        super().__init__()

        self.device = device
        self.currentIn = 0
        self.fbFunctions = list()

        self.inSize = inSize

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.pollTimeInterval = 300
        self.refreshFbTimer = Timer(self.pollTimeInterval, self.poll)
        self.refreshFbTimer.Stop()

    def addFbCallbackFunction(self, fbCallbackFunc: Callable[[int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeCallbackFunctions(self):
        for cFunc in self.fbFunctions:
            cFunc(self.currentIn)

    def poll(self, timer: Timer, count: int) -> None:
        cmd = "read\x0d"
        self.device.send(cmd)

    def setTie(self, nIn: int, nOut: int = 1) -> None:
        if (0 <= (nIn - 1) <= (self.inSize - 1)):
            cmd = 'scene s{:02}\x0d'.format(nIn - 1)
            self.currentIn = nIn
            self.device.send(cmd)
            self.executeCallbackFunctions()

    def getTie(self) -> int:
        return self.currentIn

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.device.send("\x0d")
            dbg.print("Aten UC3430 Connected!")
            self.refreshFbTimer.Restart()
        elif (state == 'Connected'):
            self.device.send("\x0d")
            dbg.print("Aten UC3430 Connected!")

    def rxParser(self, rxLines: str):
        dataLines = rxLines

        for rxLine in dataLines.splitlines():
            dbg.print("Aten: {}".format(rxLine))

    def rxEventHandler(self, interface, data):
        self.rxParser(data.decode())
