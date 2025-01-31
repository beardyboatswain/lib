#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib import event
from extronlib.ui import Button, Label
from extronlib.system import MESet

import lib.utils.signals as signals

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger("no", __name__)


class MEPopup:
    def __init__(self, UIDev, HeadLabelID):
        self.UIDev = UIDev
        self.PPages = dict()
        self.PPagesLabel = dict()
        self.MenuButtons = list()
        self.MenuButtonsME = None
        self.HeadLabel = Label(self.UIDev, HeadLabelID)
        self.start = None

    def addPPage(self, btnID, ppName, ppHeadLabel, startPP=False):
        btn = Button(self.UIDev, btnID)
        self.PPages[btn] = ppName
        self.PPagesLabel[btn] = ppHeadLabel
        self.MenuButtons.append(btn)
        if len(self.MenuButtons) == 1:
            self.start = btn
        if startPP:
            self.start = btn
        self.MenuButtonsME = MESet(self.MenuButtons)
        # # костыль - подсвециваем активную кнопку
        # for btn in self.MenuButtonsME.Objects:
        #     self.MenuButtonsME.SetStates(btn, 0, 2)

        @event(btn, 'Released')
        def showPPageOnButton(button, state):
            self.showPPage(button)

    def showPPage(self, btn):
        self.MenuButtonsME.SetCurrent(btn)
        for clBtn in self.MenuButtons:
            self.UIDev.HidePopup(self.PPages[clBtn])
        self.UIDev.ShowPopup(self.PPages[btn])
        self.HeadLabel.SetText(self.PPagesLabel[btn])

    def showStartPPage(self):
        self.showPPage(self.start)
        # реализовать кнопку back


class MEPage:
    def __init__(self, UIDev, HeadLabelID):
        self.UIDev = UIDev
        self.Pages = dict()
        self.PagesLabel = dict()
        self.MenuButtons = list()
        self.BackButton = None
        self.HomeButton = None
        self.MenuButtonsME = None
        self.PageHistory = list()
        self.previous_fl = False
        self.HeadLabel = Label(self.UIDev, HeadLabelID)
        self.home = None

    def addPage(self, btnID, pName, pHeadLabel, homeP=False):
        btn = Button(self.UIDev, btnID)
        btn.SetText(pHeadLabel.title())
        self.Pages[btn] = pName
        self.PagesLabel[btn] = pHeadLabel
        self.MenuButtons.append(btn)
        if len(self.MenuButtons) == 1:
            self.home = btn
        if homeP:
            self.home = btn
        self.MenuButtonsME = MESet(self.MenuButtons)
        for i in self.MenuButtons:
            self.MenuButtonsME.SetStates(i, offState=0, onState=2)

        @event(btn, 'Released')
        def showPageOnButton(button, state):
            self.showPage(button)

    def addBackButton(self, BackButtonID):
        self.BackButton = Button(self.UIDev, BackButtonID)

        @event(self.BackButton, 'Released')
        def backButtonAction(btn, action):
            self.showPreviousPage()

    def addHomeButton(self, HomeButtonID):
        self.HomeButton = Button(self.UIDev, HomeButtonID)

        @event(self.HomeButton, 'Released')
        def hameButtonAction(btn, action):
            self.showHomePage()

    def showPage(self, btn):
        self.MenuButtonsME.SetCurrent(btn)
        self.UIDev.ShowPage(self.Pages[btn])
        self.HeadLabel.SetText(self.PagesLabel[btn])
        if not self.previous_fl:
            self.PageHistory.append(btn)
        self.previous_fl = False

    def showPageUsingBtnID(self, button_id):
        for btn in self.MenuButtons:
            if button_id == btn.ID:
                self.showPage(btn)

    def showHomePage(self):
        self.showPage(self.home)

    def showPreviousPage(self):
        try:
            self.PageHistory = self.PageHistory[0:-1]
            backPageBtn = self.PageHistory[-1]
            self.previous_fl = True
            self.showPage(backPageBtn)
        except BaseException as err:
            self.showHomePage()


class MEPageSignal(MEPage):
    def __init__(self, UIDev, HeadLabelID):
        super().__init__(UIDev, HeadLabelID)
        self.__Signals__ = dict()

    def addBtnSignalByID(self, button_id, sig_name, params):
        for btn in self.MenuButtons:
            if button_id == btn.ID:
                self.__Signals__[btn] = {'sig_name': sig_name, 'params': params}

    def showPage(self, btn):
        super().showPage(btn)
        try:
            signals.emit('*',
                         signal=self.__Signals__[btn]['sig_name'],
                         params=self.__Signals__[btn]['params'],
                         isthread=True)
        except BaseException as err:
            dbg.print("Signal for button id={} not defined".format(btn.ID))
