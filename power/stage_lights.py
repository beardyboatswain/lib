#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib import event
from extronlib.device import UIDevice
from extronlib.interface import SerialInterface
from extronlib.system import Timer
from extronlib.ui import Button

from lib.utils.system_init import InitModule
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from usr.dev.dev import lightshark, iPadAdm, iPadUsr

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import stage_lights_dbg
dbg = debugger(stage_lights_dbg, __name__)


class LightPowerProxy(object):
    def __init__(self, dev: AutoEthernetConnection):
        self._dev = dev
        self._dev.connect()
        self.cmdBuffer = list()
        self.sendTimer = Timer(0.3, self.sender)

    def send(self, cmd: str):
        self.cmdBuffer.append(cmd)
        self.sendTimer.Resume()

    def sender(self, timername, counter):
        if len(self.cmdBuffer) == 0:
            self.sendTimer.Stop()
        else:
            self._dev.connect()
            cmd = self.cmdBuffer.pop(0)
            self._dev.send(cmd)
            self._dev.disconnect()


class LightPower(object):
    def __init__(self, dev: LightPowerProxy, id: str, onValue: int):
        self._dev = dev
        self.id = id
        self.onValue = onValue
        self.light = "Off"
        self.tglLightBtns = list()
        self.__fbFunctions = list()

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglLightBtns.append(Button(uiHost, btnTglPowerID))

        @event(self.tglLightBtns, sStates)
        def tglLightBtnsEventHandler(btn: Button, state: str):
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
        if (self.light == "On"):
            self.setPower("Off")
        else:
            self.setPower("On")

    def setPower(self, power: str):
        self.light = power
        self._dev.send(self.id + " " + (str(self.onValue) if power == "On" else "0"))
        self.showFb()
        self.callFbFunction()

    def showFb(self):
        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if self.light == "On" else 0)

    def addFbFunction(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.__fbFunctions.append(fbCallbackFunction)
            dbg.print("FB CALLBACK ADDED: {} - {}".format(self.id, fbCallbackFunction))
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def callFbFunction(self):
        for cf in self.__fbFunctions:
            cf(self.id, self.light)


class LightPowerGroup(object):
    def __init__(self):
        self.grouplight = "Off"
        self.groups = dict()
        self.tglLightBtns = list()

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglLightBtns.append(Button(uiHost, btnTglPowerID))

        @event(self.tglLightBtns, sStates)
        def tglLightBtnsEventHandler(btn: Button, state: str):
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

    def addGroup(self, group: LightPower):
        self.groups[group.id] = {"group": group, "light": "Off"}
        self.groups[group.id]["group"].addFbFunction(self.fbFunction)

    def fbFunction(self, id: str, power: str):
        self.groups[id]["light"] = power
        dbg.print("CALLBACK: gr {} - light {}".format(id, self.groups[id]["light"]))

        allPower = True
        for iGr in self.groups:
            allPower = allPower and (self.groups[iGr]["light"] == "On")

        self.grouplight = "On" if allPower else "Off"

        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if allPower else 0)

    def tglPower(self):
        newPower = "On" if (self.grouplight == "Off") else "Off"
        for iGr in self.groups:
            self.groups[iGr]["group"].setPower(newPower)


class LightPowerGroupUser(LightPowerGroup):
    def __init__(self):
        super().__init__()

    def fbFunction(self, id: str, power: str):
        self.groups[id]["light"] = power
        dbg.print("CALLBACK USER: gr {} - light {}".format(id, self.groups[id]["light"]))

        allPower = False
        for iGr in self.groups:
            allPower = allPower or (self.groups[iGr]["light"] == "On")

        self.grouplight = "On" if allPower else "Off"

        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if allPower else 0)
