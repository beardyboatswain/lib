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
from lib.var.lib_debug_mode import VideoMatrixAten_dbg
dbg = debugger(VideoMatrixAten_dbg, __name__)


class MatrixAten(VideoControlProxyMeta):
    """
    Control Class for Aten Matrix
    """
    def __init__(self,
                 device: AutoEthernetConnection,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.device = device
        self.states = dict()
        self.fbFunctions = list()

        self.inSize = inSize
        self.outSize = outSize

        self.audioDmbdOut = None

        self.tieMatchPattern = re.compile("o([0-9]+)\si([0-9|-]+)\svideo on audio on")
        self.userMatchPattern = re.compile(".{0,}Enter Username:")
        self.passMatchPattern = re.compile("Password:")
        self.loginOkMatchPattern = re.compile("Password Successful")
        self.stopMatchPattern = re.compile("----- Device Information -----|----- Network Setting -----")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.addFbFunction(self.executeCallbackFunctions)

        # self.pollTimeInterval = 30
        # self.refreshFbTimer = Timer(self.pollTimeInterval, self.refreshTie)
        # self.refreshFbTimer.Stop()

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def requestTie(self) -> None:
        cmd = "read\x0d"
        self.device.send(cmd)
        dbg.print("READ request")

    def setTie(self, nOut: int, nIn: int):
        if (1 <= nIn <= self.inSize) and (1 <= nOut <= self.outSize):
            cmd = 'sw i{:02} o{:02}\x0d'.format(nIn, nOut)
            self.device.send(cmd)
            if (self.audioDmbdOut == nOut):
                # de-embd audio of output 3
                cmd = "sw i{:02} console audio\x0d".format(nIn)
                self.device.send(cmd)

            self.requestTie()

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def setAudioDmbdOut(self, nOut: int):
        if (1 <= nOut <= self.outSize):
            self.audioDmbdOut = nOut

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connect'):
            self.device.send("\x0d")
            dbg.print("Aten Connected!")

    def rxParser(self, rxLines: str):
        dataLines = rxLines

        for rxLine in dataLines.splitlines():
            matchObjectTieMatchPattern = self.tieMatchPattern.search(rxLine)
            if matchObjectTieMatchPattern:
                outN = int(matchObjectTieMatchPattern.group(1))
                inN = int(matchObjectTieMatchPattern.group(2))
                self.states[outN] = inN
                self.executeCallbackFunctions(outN, inN)

                if (outN == self.outSize):
                    return
                continue

            matchObjectUserMatchPattern = self.userMatchPattern.search(rxLine)
            if matchObjectUserMatchPattern:
                self.device.send(self.device.login + "\x0d")
                continue

            matchObjectPassMatchPattern = self.passMatchPattern.search(rxLine)
            if matchObjectPassMatchPattern:
                self.device.send(self.device.password + "\x0d")
                continue

            matchObjectLoginOkMatchPattern = self.loginOkMatchPattern.search(rxLine)
            if matchObjectLoginOkMatchPattern:
                self.requestTie()
                continue

            matchObjectStopMatchPattern = self.stopMatchPattern.search(rxLine)
            if matchObjectStopMatchPattern:
                return

    def rxEventHandler(self, interface, data):
        self.rxParser(data.decode())
