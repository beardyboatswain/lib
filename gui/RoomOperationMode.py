#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List

from extronlib import event
from extronlib.system import Wait
from extronlib.device import UIDevice
from extronlib.ui import Button

from lib.gui.SplashScreen import SplashScreen
from lib.var.states import sPressed, sReleased, sTapped, sStates

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class OperationMode(object):
    def __init__(self,
                 uiHost: UIDevice,
                 oModeName: str,
                 oModeComment: str,
                 btnModeSetID: int,
                 btnModeNameID: int,
                 btnModeCommentID: int):
        self.uiHost = uiHost
        self.oModeName = oModeName
        self.oModeComment = oModeComment
        self.btnModeSet = Button(self.uiHost, btnModeSetID)
        self.btnModeName = Button(self.uiHost, btnModeNameID)
        self.btnModeName.SetText(self.oModeName)
        self.btnModeComment = Button(self.uiHost, btnModeCommentID)
        self.btnModeComment.SetText(self.oModeComment)

        self.__callbackFunctions = list()

        @event([self.btnModeSet, self.btnModeName, self.btnModeComment], sStates)
        def btnsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                if (self.btnModeSet.State == 0):
                    self.btnModeSet.SetState(1)
                elif (self.btnModeSet.State == 2):
                    self.btnModeSet.SetState(3)
            elif (state == sTapped):
                if (self.btnModeSet.State == 0):
                    self.btnModeSet.SetState(1)
                elif (self.btnModeSet.State == 2):
                    self.btnModeSet.SetState(3)
            elif (state == sReleased):
                if (self.btnModeSet.State == 1):
                    self.btnModeSet.SetState(0)
                elif (self.btnModeSet.State == 3):
                    self.btnModeSet.SetState(2)
                self.setMode()

    def addCallbackFunction(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.__callbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def setMode(self):
        for cf in self.__callbackFunctions:
            cf(self.oModeName)

    def fbMode(self, oMode):
        if (oMode == self.oModeName):
            self.btnModeSet.SetState(2)
        else:
            self.btnModeSet.SetState(0)


class RoomOperationMode(object):
    omVCS = "Video calls and presentation"
    omCinema = "Cinema & Entertainments"
    omModes = [omVCS, omCinema]

    def __init__(self):
        self.modes = list()
        self.current = None

        self.splash_screens: List[SplashScreen] = list()

        self.__modeScripts = dict()
        for m in self.omModes:
            self.__modeScripts[m] = list()

        self.pages = dict()
        for m in self.omModes:
            self.pages[m] = list()

        self.popups = dict()
        for m in self.omModes:
            self.popups[m] = list()

    def addMode(self,
                uiHost: UIDevice,
                oModeName: str,
                oModeComment: str,
                btnModeSetID: int,
                btnModeNameID: int,
                btnModeCommentID: int):
        if (oModeName in self.omModes):
            newOpM = OperationMode(uiHost,
                                   oModeName,
                                   oModeComment,
                                   btnModeSetID,
                                   btnModeNameID,
                                   btnModeCommentID)

            newOpM.addCallbackFunction(self.setMode)
            self.modes.append(newOpM)

    def addSplashScreen(self, splash_screen: SplashScreen):
        self.splash_screens.append(splash_screen)

    def addPage(self,
                oMode: str,
                uiHost: UIDevice,
                page: str):
        self.pages[oMode].append({"ui": uiHost, "page": page})

    def addPopups(self,
                  oMode: str,
                  uiHost: UIDevice,
                  popups: list):
        for p in popups:
            self.popups[oMode].append({"ui": uiHost, "popup": p})

    def setMode(self, oMode: str):
        print("SET MODE PARAMS:")
        print(self, oMode)
        for i_splash in self.splash_screens:
            i_splash.show("Setting up room mode", 30)

        if (oMode in self.omModes):
            prevMode = self.current

            self.current = oMode
            for m in self.modes:
                m.fbMode(self.current)

            if prevMode:
                for uipopup in self.popups[prevMode]:
                    if uipopup:
                        uipopup["ui"].HidePopup(uipopup["popup"])

            for uipopup in self.popups[oMode]:
                if uipopup:
                    uipopup["ui"].ShowPopup(uipopup["popup"])

            for m in self.__modeScripts.get(oMode):
                if m:
                    m["method"](*m["args"])

            for uipage in self.pages[oMode]:
                if uipage:
                    uipage["ui"].ShowPage(uipage["page"])

        for i_splash in self.splash_screens:
            i_splash.hide()

    def addScript(self, mode: str, scriptMethod: Callable[[str, str], None], *args):
        self.__modeScripts[mode].append({"method": scriptMethod, "args": args})
