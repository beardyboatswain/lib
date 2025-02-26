#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
import time

from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import Timer, Wait

from lib.drv.gs.extr_matrix_XTPIICrossPointSeries_v1_12_0_1 import EthernetClass
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection, AutoServerConnection
from lib.video.VideoControlProxyMeta import MatrixControlProxyMeta


from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixXTP(MatrixControlProxyMeta):
    def __init__(self,
                 device: EthernetClass,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.device = device

        self.deviceRxConnected = 0

        self.inSize = inSize
        self.outSize = outSize
        self.states = dict()
        self.fbFunctions = list()

        self.device.SubscribeStatus('ConnectionStatus', None, self.ConnectEventHandler)

        self.device.SubscribeStatus("OutputTieStatus", None, self.fbOutputTieStatusEventHandler)
        self.device.Connect()

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
        self.requestTie()

    def requestTie(self, nOut: int = None):
        dbg.print("requestTies")
        if nOut:
            self.device.Send("{}!\x0d\x0a".format(nOut))
        else:
            for iOut in range(1, self.outSize + 1):
                self.device.Send("{}!\x0d\x0a".format(iOut))
        self.sendFeedbackForAllOuts()

    def setTie(self, nOut: int, nIn: int):
        self.device.Set("MatrixTieCommand", None, {'Input': str(nIn), 'Output': str(nOut), "Tie Type": "Audio/Video"})
        self.requestTie(nOut=nOut)

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    def ConnectEventHandler(self, command, value, qualifier):
        dbg.print("Connection Handler: XTP {}".format(value))

    def fbOutputTieStatusEventHandler(self, command, value, qualifier):
        dbg.print("Cmd {} - Val {} - Qal {}".format(command, value, qualifier))
        if (command == "OutputTieStatus"):
            inN = int(value)
            outN = int(qualifier['Output'])
            self.states[outN] = inN
            dbg.print("Matix State: {}".format(self.states))
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.executeCallbackFunctions(outN, inN)

    def sendFeedbackForAllOuts(self):
        for iOut in self.states:
            inN = self.states[iOut]
            outN = iOut
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.executeCallbackFunctions(outN, inN)
