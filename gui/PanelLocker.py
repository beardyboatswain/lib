#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from extronlib import event
from extronlib.ui import Button
from extronlib.device import UIDevice

from lib.var.states import sStates, sPressed, sReleased


class PanelLocker(object):
    def __init__(self, uiHost: UIDevice, ppPageName: str):
        self.uiHost = uiHost
        self.ppPageName = ppPageName
        self.lockBtns = list()
        self.locked = False

    def addLockBtn(self, uiHost: UIDevice, btnLockTglId: int) -> None:
        self.lockBtns.append(Button(uiHost, btnLockTglId))

        @event(self.lockBtns, sStates)
        def lockBtnsEventHandler(btn: Button, state: str) -> None:
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
                self.__toggleState__()

    def __toggleState__(self):
        if self.locked:
            self.locked = False
            self.uiHost.HidePopup(self.ppPageName)
        else:
            self.locked = True
            self.uiHost.ShowPopup(self.ppPageName)
        self.__lockBtnsShowFb__()

    def __lockBtnsShowFb__(self):
        for iBtn in self.lockBtns:
            if self.locked:
                iBtn.SetState(2)
            else:
                iBtn.SetState(0)


class PanelLockerMulti(object):
    def __init__(self):
        self.ppLocks = list()
        self.lockBtns = list()
        self.locked = False

    def addLockPP(self, uiHost: UIDevice, ppPageName: str):
        self.ppLocks.append({'ui': uiHost, 'pp': ppPageName})

    def addLockBtn(self, uiHost: UIDevice, btnLockTglId: int) -> None:
        self.lockBtns.append(Button(uiHost, btnLockTglId))

        @event(self.lockBtns, sStates)
        def lockBtnsEventHandler(btn: Button, state: str) -> None:
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
                self.__toggleState__()

    def __toggleState__(self):
        if self.locked:
            self.locked = False
            for i_pp in self.ppLocks:
                i_pp.get('ui').HidePopup(i_pp.get('pp'))
        else:
            self.locked = True
            for i_pp in self.ppLocks:
                i_pp.get('ui').ShowPopup(i_pp.get('pp'))
        self.__lockBtnsShowFb__()

    def __lockBtnsShowFb__(self):
        for iBtn in self.lockBtns:
            if self.locked:
                iBtn.SetState(2)
            else:
                iBtn.SetState(0)
