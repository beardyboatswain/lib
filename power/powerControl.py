#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib import event, Version
from extronlib.device import UIDevice
from extronlib.ui import Button, Label

from lib.var.states import sStates, sPressed, sReleased
from lib.gui.SplashScreen import SplashScreen

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class SystemPower(object):
    stOn = "On"
    stOff = "Off"
    stNames = {stOn: "System On", stOff: "System Off"}

    def __init__(self, pName: str = "System Power",):
        self.__powerState = self.stOff
        self.__powerName = pName

        self.__btnTgls = list()
        self.__btnOns = list()
        self.__btnOffs = list()
        self.__lblStates = list()
        self.__lblNames = list()

        self.__powerPages = dict()

        self.__splashScreens = list()

        self.__powerOnScripts = list()
        self.__powerOffScripts = list()

    def addSplashScreen(self, splashScreen: SplashScreen = None):
        self.__splashScreens.append(splashScreen)

    def addPageTpansitions(self, uiHost: UIDevice, powerOnPage: str = None, powerOffPage: str = None):
        self.__powerPages[uiHost] = {self.stOn: powerOnPage, self.stOff: powerOffPage}

    def setMechanics(self,
                     uiHost: UIDevice,
                     btnTglID: int,
                     lblSateID: int = None,
                     lblNameID: int = None,
                     btnOnID: int = None,
                     btnOffID: int = None):

        self.__btnTgls.append(Button(uiHost, btnTglID))

        @event(self.__btnTgls, sStates)
        def btnTglsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    btn.SetState(1)
                elif (btn.State == 2):
                    btn.SetState(3)
            elif (state == sReleased):
                dbg.print("Btn Power tgl")
                if (btn.State == 1):
                    btn.SetState(0)
                elif (btn.State == 3):
                    btn.SetState(2)
                self.pwrToggle()

        if lblSateID:
            self.__lblStates.append(Label(uiHost, lblSateID))

        if lblNameID:
            self.__lblNames.append(Label(uiHost, lblNameID))
            for lbl in self.__lblNames:
                lbl.SetText(self.__powerName)

        if btnOnID:
            self.__btnOns.append(Button(uiHost, btnOnID))

            @event(self.__btnOns, sStates)
            def btnOnsEventHandler(btn: Button, state: str):
                if (state == sPressed):
                    if (btn.State == 0):
                        btn.SetState(1)
                    elif (btn.State == 2):
                        btn.SetState(3)
                elif (state == sReleased):
                    dbg.print("Btn Power on")
                    if (btn.State == 1):
                        btn.SetState(0)
                    elif (btn.State == 3):
                        btn.SetState(2)
                    self.pwrOn()

        if btnOffID:
            self.__btnOffs.append(Button(uiHost, btnOffID))

            @event(self.__btnOffs, sStates)
            def btnOffsEventHandler(btn: Button, state: str):
                if (state == sPressed):
                    if (btn.State == 0):
                        btn.SetState(1)
                    elif (btn.State == 2):
                        btn.SetState(3)
                elif (state == sReleased):
                    dbg.print("Btn Power on")
                    if (btn.State == 1):
                        btn.SetState(0)
                    elif (btn.State == 3):
                        btn.SetState(2)
                    self.pwrOff()

        self.updateWidgets()

    def pwrToggle(self):
        dbg.print("Toggle Power")
        if (self.__powerState == self.stOff):
            self.pwrOn()
        elif (self.__powerState == self.stOn):
            self.pwrOff()

    def pwrOn(self):
        self.__powerState = self.stOn
        for spl in self.__splashScreens:
            spl.show("Keep calm!\nRoom system is turning on!", 5)
        self.updateWidgets()
        self.powerOnScriptCall()
        dbg.print("ON Power")

    def pwrOff(self):
        self.__powerState = self.stOff
        for spl in self.__splashScreens:
            spl.show("Thank you for choosing us!\nRoom system is turning off!", 5)
        self.updateWidgets()
        self.powerOffScriptCall()
        dbg.print("OFF Power")

    def updateWidgets(self):
        for ui in self.__powerPages:
            if self.__powerPages.get(ui).get(self.__powerState):
                ui.ShowPage(self.__powerPages.get(ui).get(self.__powerState))

        if (self.__powerState == self.stOff):
            for btn in self.__btnTgls:
                btn.SetState(0)
            for btn in self.__btnOns:
                btn.SetState(0)
            for btn in self.__btnOffs:
                btn.SetState(2)
        elif (self.__powerState == self.stOn):
            for btn in self.__btnTgls:
                btn.SetState(2)
            for btn in self.__btnOns:
                btn.SetState(2)
            for btn in self.__btnOffs:
                btn.SetState(0)

        for lbl in self.__lblStates:
            lbl.SetText(self.stNames.get(self.__powerState))

    def addPowerOnScript(self, scriptMethod: Callable[[str, str], None], *args):
        self.__powerOnScripts.append({"method": scriptMethod, "args": args})

    def powerOnScriptCall(self):
        for m in self.__powerOnScripts:
            if m:
                m["method"](*m["args"])

    def addPowerOffScript(self, scriptMethod: Callable[[str, str], None], *args):
        self.__powerOffScripts.append({"method": scriptMethod, "args": args})

    def powerOffScriptCall(self):
        for m in self.__powerOffScripts:
            if m:
                m["method"](*m["args"])
