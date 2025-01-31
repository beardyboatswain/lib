#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

from extronlib import event
from extronlib.device import UIDevice
from extronlib.interface import SerialInterface
from extronlib.system import Timer
from extronlib.ui import Button

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debugger
from usr.var.debug_mode import lcd_power_dbg
dbg = debugger(lcd_power_dbg, __name__)


class LCDLGSerial(object):
    def __init__(self,
                 dev: SerialInterface):
        self.dev = dev

        self.tglPowerBtns = list()

        self.devID = "01"
        self.rxBuf = str()
        self.power = "Off"

        self.fbFunctions = list()

        self.LGMatchPowerFb = re.compile("a [0-9]{2} OK([0-9]{2})")

        @event(self.dev, "ReceiveData")
        def rxEventHandler(interface: SerialInterface, rx: str):
            dbg.print("LCD {} - Rx: {}".format(interface.Port, rx.decode()))
            self.rxBuf += rx.decode()
            self.rxParser(self.rxBuf.split("\x78"))
            self.rxBuf = ""

        self.pollTimer = Timer(10, self.pollDevice)

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglPowerBtns.append(Button(uiHost, btnTglPowerID))

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
                self.tglPower()

    def tglPower(self):
        if (self.power == "On"):
            self.setPower("Off")
        else:
            self.setPower("On")

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def pollDevice(self, timer, counter):
        self.dev.Send("ka {} ff\x0d\x0a".format(self.devID))

    def setPower(self, power: str):
        self.dev.Send("ka {} {}\x0d\x0a".format(self.devID, ("01" if power == "On" else "00")))

    def rxParser(self, rxLines: str):
        dbg.print("Parser: {}".format(rxLines))
        for rxLine in rxLines:
            dbg.print("Line: {}".format(rxLine))
            LGMatchObject = self.LGMatchPowerFb.search(rxLine)
            if LGMatchObject:
                dbg.print("RE Match!")
                powerState = LGMatchObject.group(1)
                dbg.print("Port {} - Power {}".format(self.dev.Port, powerState))
                self.power = "On" if powerState == "01" else "Off"
                self.showFb()

    def showFb(self):
        for iBtn in self.tglPowerBtns:
            iBtn.SetState(2 if self.power == "On" else 0)
