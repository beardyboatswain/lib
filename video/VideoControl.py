#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label
from extronlib.system import MESet

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class VideoOutputType(object):
    unplugged = 0
    display = 1
    connector = 2
    audio = 3


class VideoInputType(object):
    unplugged = 0
    appletv = 2
    ymodule = 4
    people = 6
    presentation = 8
    camera = 10
    laptop = 12
    hdmi = 14
    wallplate = 16
    pc = 18
    audio = 20
    blank = 22
    sdi = 24
    adv = 26


class VideoInputFastTie(object):
    def __init__(self,
                 vName: str,
                 vInNumber: int,
                 vUIHost: UIDevice,
                 vBtnBaseID: int,
                 vType):
        self.vName = vName
        self.vInNumber = vInNumber
        self.vUIHost = vUIHost
        self.vBtnBaseID = vBtnBaseID
        self.vType = vType

        self.vIsVirtual = False
        self.vRealInput = 0

        # Callback function ib btn presset
        self._callbackFunctions = list()

        self._vBtnMain = Button(self.vUIHost, self.vBtnBaseID)
        self._vBtnInName = Button(self.vUIHost, self.vBtnBaseID + 1)
        self._vBtnInName.SetText(self.vName)
        self._vBtnInputIco = Button(self.vUIHost, self.vBtnBaseID + 2)
        self._vBtnInputIco.SetState(self.vType)

        self._vActBtns = [self._vBtnMain,
                          self._vBtnInName,
                          self._vBtnInputIco]

        @event(self._vActBtns, sStates)
        def __vActBtnsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                self._vBtnMain.SetState(1)
                self._vBtnInputIco.SetState(self.vType + 1)
            elif (state == sReleased):
                self._vBtnMain.SetState(0)
                self._vBtnInputIco.SetState(self.vType)
                self.executeCallbackFunctions(self.vInNumber)

    def addCallbackFunction(self, fbCallbackFunction: Callable[[int], None]):
        if callable(fbCallbackFunction):
            self._callbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def executeCallbackFunctions(self, nIn: int):
        for cFunc in self._callbackFunctions:
            cFunc(nIn)

    def setState(self, state: int):
        """
        Set button active/inactive to show real fb
        """
        dbg.print("Button {} - Current state {}".format(self._vBtnMain.ID, self._vBtnMain.State))
        if ((state == 1) and (self._vBtnMain.State == 0)):
            self._vBtnMain.SetState(2)
            self._vBtnInName.SetState(2)
            self._vBtnInputIco.SetState(self.vType + 1)
        elif ((state == 0) and (self._vBtnMain.State == 2)):
            self._vBtnMain.SetState(0)
            self._vBtnInName.SetState(0)
            self._vBtnInputIco.SetState(self.vType)


class VideoInput():
    def __init__(self,
                 vName: str,
                 vInNumber: int,
                 vUIHost: UIDevice,
                 vBtnBaseID: int,
                 vType: int,
                 vVirtual: bool = False):
        self.vName = vName
        self.vInNumber = vInNumber
        self.vUIHost = vUIHost
        self.vBtnBaseID = vBtnBaseID
        self.vType = vType
        self.vVirtual = vVirtual

        self.vRealInput = 0

        # Callback function if btn presset
        self._callbackFunctions = list()

        self._vBtnMain = Button(self.vUIHost, self.vBtnBaseID)
        self._vBtnInName = Button(self.vUIHost, self.vBtnBaseID + 1)
        self._vBtnInName.SetText(self.vName)
        self._vBtnInputIco = Button(self.vUIHost, self.vBtnBaseID + 2)
        self._vBtnInputIco.SetState(self.vType)
        self._vBtnInputNumber = Button(self.vUIHost, self.vBtnBaseID + 3)
        self._vBtnInputNumber.SetText(str(self.vInNumber))

        self.__vActBtns = [self._vBtnMain,
                           self._vBtnInName,
                           self._vBtnInputIco,
                           self._vBtnInputNumber]

        @event(self.__vActBtns, sStates)
        def __vActBtnsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                # self._vBtnMain.SetState(1)
                # self._vBtnInputIco.SetState(self._vBtnInputIco.State + 1)
                self.setState(1)
            elif (state == sReleased):
                # self._vBtnMain.SetState(0)
                # self._vBtnInputIco.SetState(self._vBtnInputIco.State - 1)
                self.setState(0)
                self.executeCallbackFunctions(self.vInNumber)

    def addCallbackFunction(self, fbCallbackFunction: Callable[[int], None]):
        if callable(fbCallbackFunction):
            self._callbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def executeCallbackFunctions(self, nIn: int):
        for cFunc in self._callbackFunctions:
            cFunc(nIn)

    def setState(self, state: int):
        """
        Set button active/inactive to show real fb
        """
        dbg.print("Button {} - Current state {}".format(self._vBtnMain.ID, self._vBtnMain.State))
        if ((state == 1) and (self._vBtnMain.State == 0)):
            self._vBtnMain.SetState(2)
            self._vBtnInName.SetState(2)
            self._vBtnInputNumber.SetState(2)
            self._vBtnInputIco.SetState(self.vType + 1)
            # self._vBtnInputIco.SetState(self._vBtnInputIco.State + 1)
        elif ((state == 0) and (self._vBtnMain.State == 2)):
            self._vBtnMain.SetState(0)
            self._vBtnInName.SetState(0)
            self._vBtnInputNumber.SetState(0)
            self._vBtnInputIco.SetState(self.vType)
            # self._vBtnInputIco.SetState(self._vBtnInputIco.State - 1)


class VideoInputVirtual():
    def __init__(self,
                 vName: str,
                 vInNumber: int,
                 vUIHost: UIDevice,
                 vBtnBaseID: int,
                 vType: int,
                 vVirtual: bool = False):
        self.vName = vName
        self.vInNumber = vInNumber
        self.vUIHost = vUIHost
        self.vBtnBaseID = vBtnBaseID
        self.vType = vType
        self.vVirtual = vVirtual

        self.vRealInput = 0

        # Callback function if btn presset
        self._callbackFunctions = list()

        self._vBtnMain = Button(self.vUIHost, self.vBtnBaseID)
        self._vBtnInName = Button(self.vUIHost, self.vBtnBaseID + 1)
        self._vBtnInName.SetText(self.vName)
        self._vBtnInputIco = Button(self.vUIHost, self.vBtnBaseID + 2)
        self._vBtnInputIco.SetState(self.vType)
        self._vBtnInputNumber = Button(self.vUIHost, self.vBtnBaseID + 3)
        if self.vVirtual:
            self._vBtnInputNumber.SetText("V" + str(self.vInNumber))
        else:
            self._vBtnInputNumber.SetText(str(self.vInNumber))

        self.__vActBtns = [self._vBtnMain,
                           self._vBtnInName,
                           self._vBtnInputIco,
                           self._vBtnInputNumber]

        @event(self.__vActBtns, sStates)
        def __vActBtnsEventHandler(btn: Button, state: str):
            if (state == sPressed):
                # self._vBtnMain.SetState(1)
                # self._vBtnInputIco.SetState(self._vBtnInputIco.State + 1)
                self.setState(1)
            elif (state == sReleased):
                # self._vBtnMain.SetState(0)
                # self._vBtnInputIco.SetState(self._vBtnInputIco.State - 1)
                self.setState(0)
                self.executeCallbackFunctions(self.vInNumber)

    def addCallbackFunction(self, fbCallbackFunction: Callable[[int], None]):
        if callable(fbCallbackFunction):
            self._callbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def executeCallbackFunctions(self, nIn: int):
        for cFunc in self._callbackFunctions:
            cFunc(nIn)

    def setState(self, state: int):
        """
        Set button active/inactive to show real fb
        """
        dbg.print("Button {} - Current state {}".format(self._vBtnMain.ID, self._vBtnMain.State))
        if ((state == 1) and (self._vBtnMain.State == 0)):
            self._vBtnMain.SetState(2)
            self._vBtnInName.SetState(2)
            self._vBtnInputNumber.SetState(2)
            self._vBtnInputIco.SetState(self.vType + 1)
            # self._vBtnInputIco.SetState(self._vBtnInputIco.State + 1)
        elif ((state == 0) and (self._vBtnMain.State == 2)):
            self._vBtnMain.SetState(0)
            self._vBtnInName.SetState(0)
            self._vBtnInputNumber.SetState(0)
            self._vBtnInputIco.SetState(self.vType)
            # self._vBtnInputIco.SetState(self._vBtnInputIco.State - 1)

    def setVirtalInput(self, nIn: int, nInName: str):
        self.vInNumber = nIn
        self.vName = nInName
        self._vBtnInputNumber.SetText("V" + str(self.vInNumber))
        self._vBtnInName.SetText(self.vName)


class VideoOutput(object):
    def __init__(self,
                 vName: str,
                 vOutNumber: int,
                 vUIHost: UIDevice,
                 vBtnBaseID: int,
                 vType: int):
        """
        vBtnBaseID - first id for group of buttons for output control, next 5 ids will be used
                        For examle: vBtnBaseID = 11, 12-16 used
        """
        self.vName = vName
        self.vOutNumber = vOutNumber
        self.vUIHost = vUIHost
        self.vBtnBaseID = vBtnBaseID
        if (vType in [VideoOutputType.display, VideoOutputType.connector]):
            self.vType = vType
        else:
            self.vType = VideoOutputType.display
            dbg.print("Wrong out type: {}".format(vType))

        self.currentInput = None

        self.__vBtnMain = Button(self.vUIHost, self.vBtnBaseID)
        self.__vBtnOutName = Button(self.vUIHost, self.vBtnBaseID + 1)
        self.__vBtnOutName.SetText(self.vName.replace("\n", " "))
        self.__vBtnInputIco = Button(self.vUIHost, self.vBtnBaseID + 2)
        self.__vBtnInputName = Button(self.vUIHost, self.vBtnBaseID + 3)
        self.__vBtnTypeIco = Button(self.vUIHost, self.vBtnBaseID + 4)
        self.__vBtnTypeIco.SetState(self.vType)
        self.__vBtnOutNumber = Button(self.vUIHost, self.vBtnBaseID + 5)
        self.__vBtnOutNumber.SetText(str(self.vOutNumber))

        # callback function if btn pressed
        self.__callbackFunction = list()

        self.__vActBtns = [self.__vBtnMain,
                           self.__vBtnOutName,
                           self.__vBtnInputIco,
                           self.__vBtnInputName,
                           self.__vBtnTypeIco,
                           self.__vBtnOutNumber
                           ]

        # for iBtn in self.__vActBtns:
        #     setattr(iBtn, 'nOut', self.vOutNumber)

        @event(self.__vActBtns, sStates)
        def __vActBtnsEventHandler(btn, state):
            # dbg.print("ActBtnsEventHandler - Out <{}> - State <{}>".format(getattr(btn, "nOut"), state))
            if (state == sPressed):
                self.__vBtnMain.SetState(1)
            elif (state == sReleased):
                self.__vBtnMain.SetState(0)
                self.executeCallbackFunctions(self.vOutNumber)
                # dbg.print("Out <{}> selected!".format(getattr(btn, "nOut")))
                # self.executeCallbackFunctions(getattr(btn, "nOut"))

    def addCallbackFunction(self, fbCallbackFunction: Callable[[int], None]):
        if callable(fbCallbackFunction):
            self.__callbackFunction.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def executeCallbackFunctions(self, nOut: int):
        for cFunc in self.__callbackFunction:
            cFunc(nOut)

    def setFbSource(self, currentInput: int, currentInputName: str, currentInputIco: int):
        self.currentInput = currentInput
        self.__vBtnInputName.SetText(currentInputName)
        self.__vBtnInputIco.SetState(currentInputIco)


class VideoControl(object):
    '''
    Class for gui control for any video matrix switcher
    '''
    def __init__(self, UIHost: UIDevice,
                 videoControlProxy: VideoControlProxyMeta):
        self.UIHost = UIHost

        self.videoControlProxy = videoControlProxy
        self.videoControlProxy.addFbCallbackFunction(self._feedbackHandler)

        self.outButtons = dict()
        self.inButtons = dict()

        self._inputsFavPopupName = str()
        self._inputsFavPopupBtn = None
        self._btnClose = None
        self._lblCurrentOut = None

        self.displayPopups = dict()
        self.displayPopupSelectBtns = list()
        self.displayPopupSelectBtnsME = None

        self.displayPopupsSelectorPP = None

        self.srcPopups = dict()
        self.srcPopupSelectBtns = list()
        self.srcPopupSelectBtnsME = None

        self._selectedOutput = 0

        self._connectedOuts = list()

    def addOutputButton(self,
                        vName: str,
                        vOutNumber: int,
                        vBtnBaseID: int,
                        vType: int):
        cVideoControlNew = VideoOutput(vName=vName,
                                       vOutNumber=vOutNumber,
                                       vUIHost=self.UIHost,
                                       vBtnBaseID=vBtnBaseID,
                                       vType=vType)
        cVideoControlNew.addCallbackFunction(self.__outputCallbackHandler)
        self.outButtons[vOutNumber] = cVideoControlNew

    def addInputButton(self,
                       vName: str,
                       vInNumber: int,
                       vBtnBaseID: int,
                       vType: int):
        videoInputNew = VideoInput(vName=vName,
                                   vInNumber=vInNumber,
                                   vUIHost=self.UIHost,
                                   vBtnBaseID=vBtnBaseID,
                                   vType=vType)
        videoInputNew.addCallbackFunction(self.__inputCallbackHandler)
        self.inButtons[vInNumber] = videoInputNew

    def switch(self, nOut: int, nIn: int):
        dbg.print("Switching!!!!!!!!!")
        self.videoControlProxy.setTie(nOut, nIn)

        # switch linked outputs
        for iCon in self._connectedOuts:
            dbg.print("Connected:")
            dbg.print(iCon)
            if (iCon["main"] == nOut):
                dbg.print("Output {} is maseter ({}). Linked outs {}.".format(nOut, iCon["main"], iCon["slave"]))
                if (iCon["in"]):
                    if (nIn in iCon["in"]):
                        for iOut in iCon["slave"]:
                            dbg.print("Linked switch out {} - in {} ".format(iOut, nIn))
                            self.videoControlProxy.setTie(iOut, nIn)
                else:
                    for iOut in iCon["slave"]:
                        dbg.print("Linked switch out {} - in {} ".format(iOut, nIn))
                        self.videoControlProxy.setTie(iOut, nIn)

    def addConnectedOutputs(self, mainOut: int, slaveOuts: list, inclIns: list = None):
        """
        Switch input, connected to mainOut to outputs in slaveOut list for inputs in inclIns if
        inclIns is not None.
        """
        self._connectedOuts.append({"main": mainOut, "slave": slaveOuts, "in": inclIns})

    def addInputsPopupPage(self, pPopupBtnID: int, pName: str) -> None:
        """
        Add popup page with source buttons
        pPopupBtnID: int - button id for opening popup page with src buttons
        pName: str - popup page name
        Note: First added popup will be shown fist
        """
        newSrcPPButton = Button(self.UIHost, pPopupBtnID)

        if (len(self.srcPopups) == 0):
            self._inputsFavPopupName = pName
            self._inputsFavPopupBtn = newSrcPPButton
            self.srcPopupSelectBtnsME = MESet([newSrcPPButton, ])
            self.srcPopupSelectBtnsME.SetStates(newSrcPPButton, offState=0, onState=2)
        else:
            self.srcPopupSelectBtnsME.Append(newSrcPPButton)
            self.srcPopupSelectBtnsME.SetStates(newSrcPPButton, offState=0, onState=2)

        self.srcPopups[pPopupBtnID] = pName

        @event(newSrcPPButton, sStates)
        def newSrcPPButtonEventHandler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    btn.SetState(1)
                elif (btn.State == 2):
                    btn.SetState(3)
            elif (state == sReleased):
                self.srcPopupSelectBtnsME.SetCurrent(btn)
                self.UIHost.ShowPopup(self.srcPopups[btn.ID])

        self.srcPopupSelectBtns.append(newSrcPPButton)

    def addDisplayPopupSelector(self, pName: str) -> None:
        self.displayPopupsSelectorPP = pName
        self.UIHost.ShowPopup(self.displayPopupsSelectorPP)

    def addDisplaysPopupPage(self, pPopupBtnID: int, pName: None) -> None:
        """
        Add popup page with displays buttons, if number of displays is more than
        you cal placed on one page.
        pPopupBtnID: int - button id for opening popup page with src buttons
        pName: str - popup page name
        Note: First added popup will be shown fist
        """
        newDisplayPPButton = Button(self.UIHost, pPopupBtnID)

        if (len(self.displayPopups) == 0):
            self.displayPopupSelectBtnsME = MESet([newDisplayPPButton, ])
            self.displayPopupSelectBtnsME.SetStates(newDisplayPPButton, offState=0, onState=2)
            self.UIHost.ShowPopup(pName)
            self.displayPopupSelectBtnsME.SetCurrent(newDisplayPPButton)
        else:
            self.displayPopupSelectBtnsME.Append(newDisplayPPButton)
            self.displayPopupSelectBtnsME.SetStates(newDisplayPPButton, offState=0, onState=2)

        self.displayPopups[pPopupBtnID] = pName

        @event(newDisplayPPButton, sStates)
        def newdisplayPPButtonEventHandler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    btn.SetState(1)
                elif (btn.State == 2):
                    btn.SetState(3)
            elif (state == sReleased):
                self.displayPopupSelectBtnsME.SetCurrent(btn)
                self.UIHost.ShowPopup(self.displayPopups[btn.ID])

        self.displayPopupSelectBtns.append(newDisplayPPButton)

    def addInputsPopupPageMechanic(self, btnCloseSrcPopupID: int, lblCurrentOutID: int):
        self._btnClose = Button(self.UIHost, btnCloseSrcPopupID)
        self._lblCurrentOut = Label(self.UIHost, lblCurrentOutID)

        self.hideSrcPopups()

        @event(self._btnClose, sStates)
        def __btnCloseEventHandler(btn, state):
            if (state == sPressed):
                self._btnClose.SetState(1)
            elif (state == sReleased):
                self._btnClose.SetState(0)
                self._selectedOutput = 0
                self.hideSrcPopups()
                self.hideInputFb()

    def hideSrcPopups(self):
        if (len(self.srcPopups) > 0):
            for iPP in self.srcPopups:
                self.UIHost.HidePopup(self.srcPopups.get(iPP))

    def __outputCallbackHandler(self, nOut):
        self._selectedOutput = nOut
        self.UIHost.ShowPopup(self._inputsFavPopupName)
        self.srcPopupSelectBtnsME.SetCurrent(self._inputsFavPopupBtn)
        self._lblCurrentOut.SetText(self.outButtons.get(nOut).vName.replace("\n", " "))
        self.showInputFb(self.outButtons.get(nOut).currentInput)

    def __inputCallbackHandler(self, nIn):
        self.hideSrcPopups()
        self.hideInputFb()
        # self.videoControlProxy.setTie(self._selectedOutput, nIn)
        self.switch(nOut=self._selectedOutput, nIn=nIn)
        self._selectedOutput = 0

    def _feedbackHandler(self, nOut: int, nIn: int):
        if (nOut in self.outButtons.keys()):
            self.outButtons.get(nOut).setFbSource(nIn,
                                                  self.inButtons.get(nIn).vName,
                                                  self.inButtons.get(nIn).vType)

        # # switch linked outputs
        # for iCon in self._connectedOuts:
        #     if (iCon["main"] == nOut):
        #         dbg.print("Output {} is maseter ({}). Linked outs {}.".format(nOut, iCon["main"], iCon["slave"]))
        #         if (iCon["in"]):
        #             if (nIn in iCon["in"]):
        #                 for iOut in iCon["slave"]:
        #                     dbg.print("Linked switch out {} - in {} ".format(iOut, nIn))
        #                     self.switch(iOut, nIn)
        #         else:
        #             for iOut in iCon["slave"]:
        #                 dbg.print("Linked switch out {} - in {} ".format(iOut, nIn))
        #                 self.switch(iOut, nIn)

    def showInputFb(self, currentInput: int):
        dbg.print(self.inButtons)
        self.inButtons.get(currentInput).setState(1)

    def hideInputFb(self):
        for iIn in self.inButtons:
            # if (self.inButtons.get(iIn).vInNumber > 0):
            self.inButtons.get(iIn).setState(0)


class VideoOutFastTie(object):
    def __init__(self,
                 UIHost: UIDevice,
                 #  videoControlProxy: VideoControlProxyMeta,
                 videoControl: VideoControl,
                 output: int,
                 outputName: str,
                 lblOutputNameID: int,
                 lblOutputCurrentInID: int):

        self.UIHost = UIHost

        self.videoControl = videoControl
        # todo что это за колбэк
        self.videoControl.videoControlProxy.addFbCallbackFunction(self._feedbackHandler)

        self.output = output
        # self.outputName = outputName
        self.outputName = outputName.replace("\n", " ")

        self.__lblOutputName = Label(self.UIHost, lblOutputNameID)
        self.__lblOutputName.SetText(self.outputName)

        self.__lblCurrentIn = Label(self.UIHost, lblOutputCurrentInID)

        self.inButtons = dict()
        self.inNames = dict()

    def addInputButton(self,
                       vName: str,
                       vInNumber: int,
                       vBtnBaseID: int,
                       vType):
        videoInputNew = VideoInputFastTie(vName=vName,
                                          vInNumber=vInNumber,
                                          vUIHost=self.UIHost,
                                          vBtnBaseID=vBtnBaseID,
                                          vType=vType)
        videoInputNew.addCallbackFunction(self.__inputCallbackHandler)
        self.inButtons[vInNumber] = videoInputNew

    def addInNames(self, inNames: dict):
        self.inNames = inNames

    def __inputCallbackHandler(self, nIn):
        dbg.print("Input {} pressed".format(nIn))
        self.hideInputFb()
        self.videoControl.switch(self.output, nIn)

    def _feedbackHandler(self, nOut: int, nIn: int):
        dbg.print("VideoControlFastTie FB: out {} - in {}".format(nOut, nIn))
        if (nOut == self.output):
            if (nIn in self.inButtons.keys()):
                for iBtn in self.inButtons:
                    if (iBtn == nIn):
                        self.inButtons.get(iBtn).setState(1)

                    else:
                        self.inButtons.get(iBtn).setState(0)
                self.__lblCurrentIn.SetText(" ")
            else:
                self.__lblCurrentIn.SetText(self.inNames.get(nIn))
                self.hideInputFb()

    def hideInputFb(self):
        for iIn in self.inButtons:
            self.inButtons.get(iIn).setState(0)
