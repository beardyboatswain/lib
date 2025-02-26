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


class MatrixTest(MatrixControlProxyMeta):
    def __init__(self,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.deviceRxConnected = 0

        self.inSize = inSize
        self.outSize = outSize
        self.states = dict()
        self.fbFunctions = list()

        self.addFbFunction(self.executeCallbackFunctions)

        self.refreshFbTimer = Timer(20, self.refreshTies)

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
        @Wait(0.1)
        def request_cmd():
            self.sendFeedbackForAllOuts()

    def setTie(self, nOut: int, nIn: int):
        dbg.print("MatrixTieCommand: out[{}] - in[{}]".format(nOut, nIn))
        @Wait(0.1)
        def send_cmd():
            self.states[nOut] = nIn
            self.requestTie(nOut=nOut)

    def getTie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)

    # def fbOutputTieStatusEventHandler(self, command, value, qualifier):
    #     dbg.print("Cmd {} - Val {} - Qal {}".format(command, value, qualifier))
    #         if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
    #             self.executeCallbackFunctions(outN, inN)

    def sendFeedbackForAllOuts(self):
        for iOut in self.states:
            inN = self.states[iOut]
            outN = iOut
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.executeCallbackFunctions(outN, inN)
