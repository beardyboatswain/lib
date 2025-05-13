#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List

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

    msg_sys_turning_on_text = {'ru': 'Сохраняйте спокойствие!\nСистема включается!',
                               'en': 'Keep calm!\nRoom system is turning on!'}
    msg_sys_turning_off_text = {'ru': 'Спасибо, что выбрали нас!\nСистема выключается.',
                                'en': 'Thank you for choosing us!\nRoom system is turning off!'}

    def __init__(self, pName: str = "System Power", lang: str = "ru"):
        self._powerState = self.stOff
        self._powerName = pName
        self._lang = lang

        self._btnTgls = list()
        self._btnOns = list()
        self._btnOffs = list()
        self._lblStates = list()
        self._lblNames = list()

        self._powerPages = dict()

        self._splashScreens: List[SplashScreen] = list()

        self._powerOnScripts = list()
        self._powerOffScripts = list()

    def addSplashScreen(self, splashScreen: SplashScreen = None):
        self._splashScreens.append(splashScreen)

    def addPageTpansitions(self, uiHost: UIDevice, powerOnPage: str = None, powerOffPage: str = None):
        self._powerPages[uiHost] = {self.stOn: powerOnPage, self.stOff: powerOffPage}

    def setMechanics(self,
                     uiHost: UIDevice,
                     btnTglID: int,
                     lblSateID: int = None,
                     lblNameID: int = None,
                     btnOnID: int = None,
                     btnOffID: int = None):

        self._btnTgls.append(Button(uiHost, btnTglID))

        @event(self._btnTgls, sStates)
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
            self._lblStates.append(Label(uiHost, lblSateID))

        if lblNameID:
            self._lblNames.append(Label(uiHost, lblNameID))
            for lbl in self._lblNames:
                lbl.SetText(self._powerName)

        if btnOnID:
            self._btnOns.append(Button(uiHost, btnOnID))

            @event(self._btnOns, sStates)
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
            self._btnOffs.append(Button(uiHost, btnOffID))

            @event(self._btnOffs, sStates)
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
        if (self._powerState == self.stOff):
            self.pwrOn()
        elif (self._powerState == self.stOn):
            self.pwrOff()

    def pwrOn(self):
        self._powerState = self.stOn
        for spl in self._splashScreens:
            spl.show(self.msg_sys_turning_on_text[self._lang], 5)
        self.updateWidgets()
        self.powerOnScriptCall()
        dbg.print("ON Power")

    def pwrOff(self):
        self._powerState = self.stOff
        for spl in self._splashScreens:
            spl.show(self.msg_sys_turning_off_text[self._lang], 5)
        self.updateWidgets()
        self.powerOffScriptCall()
        dbg.print("OFF Power")

    def updateWidgets(self):
        for ui in self._powerPages:
            if self._powerPages.get(ui).get(self._powerState):
                ui.ShowPage(self._powerPages.get(ui).get(self._powerState))

        if (self._powerState == self.stOff):
            for btn in self._btnTgls:
                btn.SetState(0)
            for btn in self._btnOns:
                btn.SetState(0)
            for btn in self._btnOffs:
                btn.SetState(2)
        elif (self._powerState == self.stOn):
            for btn in self._btnTgls:
                btn.SetState(2)
            for btn in self._btnOns:
                btn.SetState(2)
            for btn in self._btnOffs:
                btn.SetState(0)

        for lbl in self._lblStates:
            lbl.SetText(self.stNames.get(self._powerState))

    def addPowerOnScript(self, scriptMethod: Callable[[str, str], None], *args):
        self._powerOnScripts.append({"method": scriptMethod, "args": args})

    def powerOnScriptCall(self):
        for m in self._powerOnScripts:
            if m:
                m["method"](*m["args"])

    def addPowerOffScript(self, scriptMethod: Callable[[str, str], None], *args):
        self._powerOffScripts.append({"method": scriptMethod, "args": args})

    def powerOffScriptCall(self):
        for m in self._powerOffScripts:
            if m:
                m["method"](*m["args"])
