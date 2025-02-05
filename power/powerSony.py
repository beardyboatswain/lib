#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod

from extronlib import event
from extronlib.device import UIDevice
from extronlib.system import Timer, Wait
from extronlib.ui import Button

from lib.power.DevicePowerMeta import DevicePowerMeta

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debugger
dbg = debugger('no', __name__)


class LCDSonyEthernet(DevicePowerMeta):
    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev

        self.tglPowerBtns = list()

        self.rxBuf = str()
        self.power = "Off"

        self.fbCallbackFunctions = list()

        self.dev.subscribe('Connected', self.connectEventHandler)
        self.dev.subscribe('Disconnected', self.connectEventHandler)
        self.dev.subscribe('ReceiveData', self.rxEventHandler)

        self.dev.connect()

        self.pollTimer = Timer(10, self.pollDevice)

    def setMechanics(self, uiHost: UIDevice, btnTglPowerId: int):
        self.tglPowerBtns.append(Button(uiHost, btnTglPowerId))

        @event(self.tglPowerBtns, sStates)
        def tglPowerBtnsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    btn.SetState(1)
                elif (btn.State == 2):
                    btn.SetState(3)
            elif (state == sReleased):
                if (btn.State == 1):
                    btn.SetState(0)
                elif (btn.State == 3):
                    btn.SetState(2)
                self.tgl_power()

    def get_power(self) -> str:
        return self.power

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def add_fb_callback_function(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.fbCallbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fbCallbackFunctions:
            cFunc(self.power)

    def connectEventHandler(self, interface, state):
        dbg.print("Bravia {} in {}!".format(self.dev.ip, state))

    def pollDevice(self, timer, counter):
        # self.dev.send("POWER REQUEST")
        self.dev.send("*SEPOWR################\x0a")

    def set_power(self, power: str):
        if (power == "On"):
            self.dev.send("*SCPOWR0000000000000001\x0a")
            dbg.print("Brabia Power ON sent")
        elif (power == "Off"):
            self.dev.send("*SCPOWR0000000000000000\x0a")
            dbg.print("Bravia Power OFF sent")

    def showFb(self):
        self.execute_callback_functions()
        for iBtn in self.tglPowerBtns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rxParser(self, rxLine: str):
        dbg.print("RX lines:\n{}".format(rxLine))
        dataLines = rxLine

        for rxLine in dataLines.splitlines():
            if (rxLine.find("*SAPOWR0000000000000001") > -1):
                self.power = "On"
                self.showFb()
            elif (rxLine.find("*SAPOWR0000000000000000") > -1):
                self.power = "Off"
                self.showFb()

    def rxEventHandler(self, interface, data):
        dbg.print("Sony {} recieved: {} ".format(self.dev.ip, data.decode()))
        self.rxBuf = data.decode()
        self.rxParser(data.decode())
