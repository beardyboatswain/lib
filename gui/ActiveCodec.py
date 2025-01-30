#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod

from extronlib import event
from extronlib.ui import Button
from extronlib.device import UIDevice

from lib.var.states import sPressed, sReleased, sHeld, sTapped, sRepeated, sStates
from lib.utils.CallbackObject import CallbackObject
from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import ActiveCodec_dbg
dbg = debugger(ActiveCodec_dbg, __name__)

# если меняется кодек, то сделать перекоммутацию видео и аудио


class ActiveCodec(CallbackObject):
    def __init__(self):
        self.codecs = dict()
        self.active = None
        self._callbackMethods = list()
        self._setBtns = list()

    def addCodec(self, codecId: int, codecName: str, vidInPeople: str, vidInPresent: int):
        if codecId:
            self.codecs[codecId] = {"name": codecName, "vidInPeople": vidInPeople, "vidInPresent": vidInPresent}
            self._callbackMethods[codecId] = list()
            if (len(self.codecs) == 1):
                self.setActive(codecId)

    def addSetBtn(self, codecId: int, uiHost: UIDevice, btnId: int):
        if codecId in self.codecs.keys():
            newBtn = Button(uiHost, btnId)
            setattr(newBtn, "codecId", codecId)
            self._setBtns.append(newBtn)

        @event(self._setBtns, sStates)
        def setBtnsEventHandler(btn: Button, state: str):
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
            self.setActive(getattr(btn, 'codecId'))

        self.updateBtns()

    def addScript(self, codecId: int, scriptMethod: Callable, *args):
        if codecId in self.codecs.keys():
            self.addCallback(codecId, scriptMethod, args)

    def setActive(self, codecId: int):
        if codecId in self.codecs.keys():
            self.active = codecId
            self.updateBtns()
            self.executeCallback(codecId)

    def updateBtns(self):
        for iBtn in self._setBtns:
            if (getattr(iBtn, "codecId") == self.active):
                iBtn.SetState(2)
            else:
                iBtn.SetState(0)

    def getInputs(self) -> dict:
        """
        Returns {"people": <in number>, "presentstion": <in number>}
        where <in number> - corresponding in of Active Codec on main matrix
        """
        return {"people": self.codecs[self.active]["vidInPeople"], "presentstion": self.codecs[self.active]["vidInPresent"]}

    def getPeopleIn(self) -> int:
        return self.codecs[self.active]["vidInPeople"]

    def getPpresentIn(self) -> int:
        self.codecs[self.active]["vidInPresent"]
