#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from extronlib import event
from extronlib.ui import Button, Label
from extronlib.system import MESet
from extronlib.device import UIDevice

import lib.utils.signals as signals

from lib.var.states import sStates, sPressed, sReleased, sTapped, sHeld

from lib.utils.debugger import debugger
from lib.var.lib_debug_mode import menu_dbg

# from utils.traceServer import Print

dbg = debugger(menu_dbg, __name__)


class CMenu:
    def __init__(self, UIDev: UIDevice, HeadLabelID: int, mainMenuPP: str):
        self.UIDev = UIDev
        self.mainMenuPP = mainMenuPP
        self.menuButtons = dict()
        self.submenuButtons = list()
        self.backButton = None
        self.homeButton = None
        self.menuButtonsME = None
        self.closeSubmenuButtons = list()
        self.headLabel = Label(self.UIDev, HeadLabelID)
        self.pageHistory = list()
        self.pageHistoryLen = 10

    def addMenuButton(self,
                      btnID: int,
                      btnTitle: str,
                      pageTitle: str,
                      pageName: str,
                      submenuName: str = None,
                      closeSubmenuButtonID: int = None,
                      parentButtonID: int = None,
                      homeP: bool = False):

        if submenuName:
            btn = Button(self.UIDev, btnID, holdTime=0.7)
        else:
            btn = Button(self.UIDev, btnID)

        btn.SetText(btnTitle.title())

        self.menuButtons[btn] = {'btnTitle': btnTitle,
                                 'pageTitle': pageTitle,
                                 'pageName': pageName}

        if submenuName:
            self.menuButtons[btn]['submenuPopupName'] = submenuName

        if parentButtonID:
            self.menuButtons[btn]['parentButtonID'] = parentButtonID

        if (len(self.menuButtons) == 1) or homeP:
            self.homeButton = btn

        self.menuButtonsME = MESet(self.menuButtons)

        for i in self.menuButtons:
            self.menuButtonsME.SetStates(i, offState=0, onState=2)

        if submenuName:

            @event(btn, [sTapped, sHeld])
            def showPageOrSubmenuButtonEvent(button: Button, state: str):
                if (state == sTapped):
                    self.__showPage(button)
                elif (state == sHeld):
                    self.__showSubmenu(button)

            self.submenuButtons.append(btn)
        else:
            @event(btn, sReleased)
            def showPageButtonEvent(button: Button, state: str):
                self.__showPage(button)

        if closeSubmenuButtonID:
            closeBtn = Button(self.UIDev, closeSubmenuButtonID)

            @event(closeBtn, sReleased)
            def closeSubmenuButtonEvent(button: Button, state: str):
                self.__hideSubmenu()

            self.closeSubmenuButtons.append(closeBtn)

    def __showPage(self, btn: Button):
        dbg.print('Menu button: {}'.format(btn))

        self.__hideSubmenu()

        if (self.menuButtons.get(btn).get('parentButtonID')):
            parentBtnID = self.menuButtons.get(btn).get('parentButtonID')
            for b in self.menuButtons.keys():
                if (b.ID == parentBtnID):
                    self.menuButtonsME.SetCurrent(b)
        else:
            self.menuButtonsME.SetCurrent(btn)
        self.headLabel.SetText(self.menuButtons.get(btn).get('pageTitle'))

        self.UIDev.ShowPage(self.menuButtons[btn].get('pageName'))
        self.__addPageToHistory(btn)
        dbg.print('Btn = {}'.format(btn.ID))

    def __showSubmenu(self, btn: Button):
        self.__hideSubmenu()
        popupToShow = self.menuButtons.get(btn).get('submenuPopupName')
        if (popupToShow):
            self.UIDev.ShowPopup(popupToShow)

    def __hideSubmenu(self):
        for b in self.menuButtons:
            popupToHide = self.menuButtons.get(b).get('submenuPopupName')
            if (popupToHide):
                self.UIDev.HidePopup(popupToHide)

    def addBackButton(self, BackButtonID: int):
        self.backButton = Button(self.UIDev, BackButtonID)

        @event(self.backButton, sReleased)
        def backButtonEvent(btn, action):
            self.__showPreviousPage()

    def __addPageToHistory(self, button: Button):
        self.pageHistory.append(button)
        if (len(self.pageHistory) > self.pageHistoryLen):
            self.pageHistory = self.pageHistory[1:]

    def __showPreviousPage(self):
        if (len(self.pageHistory) > 0):
            self.pageHistory = self.pageHistory[:-1]
            previousMenuBtn = self.pageHistory.pop(-1)
            self.__showPage(previousMenuBtn)

    def showMenu(self):
        self.UIDev.ShowPopup(self.mainMenuPP)
        self.__showPage(self.homeButton)


class CMenuSignal(CMenu):
    def __init__(self, UIDev: UIDevice, HeadLabelID: int, mainMenuPP: str):
        super().__init__(UIDev, HeadLabelID, mainMenuPP)
        self.__Signals__ = dict()

    def addSignalToMenuButton(self, menuButtonID: int,
                              signalName: str,
                              signalParams: dict):
        for btn in self.MenuButtons.keys():
            if menuButtonID == btn.ID:
                self.__Signals__[btn] = {'signalName': signalName,
                                         'signalParams': signalParams}

    def __showPage(self, btn: Button):
        super().__showPage(btn)
        try:
            signals.emit('*',
                         signal=self.__Signals__[btn]['signalName'],
                         params=self.__Signals__[btn]['signalParams'],
                         isthread=True)
        except BaseException as err:
            dbg.print("Button id={} sig not defined.\n\
                      Error: {}".format(btn.ID, err))
