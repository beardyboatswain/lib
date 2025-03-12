#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from extronlib import event
from extronlib.system import Timer
from extronlib.ui import Button, Label
from extronlib.device import UIDevice


class SplashScreen(object):
    def __init__(self, uiHost: UIDevice, ppPageName: str, lblNoteId: int, btnSpinerId: int):
        self.uiHost = uiHost
        self.ppPageName = ppPageName
        self.lblNoteId = lblNoteId
        self.btnSpinerId = btnSpinerId

        self.lblNote = Label(self.uiHost, self.lblNoteId)
        self.btnSpiner = Button(self.uiHost, self.btnSpinerId)

        self.splashTimer = None
        self.splashTimerClose = None

    def show(self, sNote: str, sTime: int):
        self.lblNote.SetText(sNote)
        self.btnSpiner.SetState(0)
        self.uiHost.ShowPopup(self.ppPageName, sTime)
        self.splashTimer = Timer(0.7, self.__counterHandler)
        self.splashTimerClose = Timer(sTime, self._counterCloseHandler)

    def hide(self):
        self._counterCloseHandler(0, 0)

    def _counterCloseHandler(self, cntName, cntValue):
        if (self.splashTimer):
            # if (self.splashTimer.State == '*Running*'):
            self.splashTimer.Stop()
            self.splashTimerClose.Stop()
            self.uiHost.HidePopup(self.ppPageName)

    def __counterHandler(self, cntName, cntValue):
        self.btnSpiner.SetState((self.btnSpiner.State + 1) % 12)
