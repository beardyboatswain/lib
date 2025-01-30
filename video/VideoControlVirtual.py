#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib import event
from extronlib.device import UIDevice

from extronlib.ui import Button, Label

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import VideoControlVirtual_dbg
dbg = debugger(VideoControlVirtual_dbg, __name__)


class VideoOutputType(object):
    display = 1
    connector = 2


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
    def __init__(self, UIHost: UIDevice,
                 videoControlProxy: VideoControlProxyMeta):
        self.UIHost = UIHost

        self.videoControlProxy = videoControlProxy
        self.videoControlProxy.addFbCallbackFunction(self._feedbackHandler)

        self.outButtons = dict()
        self.inButtons = dict()

        self._inputsPopupName = str()
        self._btnClose = None
        self._lblCurrentOut = None

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
                       vType):
        videoInputNew = VideoInput(vName=vName,
                                   vInNumber=vInNumber,
                                   vUIHost=self.UIHost,
                                   vBtnBaseID=vBtnBaseID,
                                   vType=vType)
        videoInputNew.addCallbackFunction(self.__inputCallbackHandler)
        self.inButtons[vInNumber] = videoInputNew

    def switch(self, nOut: int, nIn: int):
        self.videoControlProxy.setTie(nOut, nIn)

    def addConnectedOutputs(self, mainOut: int, slaveOuts: list, inclIns: list = None):
        """
        Switch input, connected to mainOut to outputs in slaveOut list for inputs in inclIns if
        inclIns is not None.
        """
        self._connectedOuts.append({"main": mainOut, "slave": slaveOuts, "in": inclIns})

    def addInputsPopupPage(self, pName: str, btnCloseID: int, lblCurrentOutID: int):
        """
        Add popup page with source buttons
        pName: str - popup page name
        """
        self._inputsPopupName = pName
        self.UIHost.HidePopup(self._inputsPopupName)
        self._btnClose = Button(self.UIHost, btnCloseID)
        self._lblCurrentOut = Label(self.UIHost, lblCurrentOutID)

        @event(self._btnClose, sStates)
        def __btnCloseEventHandler(btn, state):
            if (state == sPressed):
                self._btnClose.SetState(1)
            elif (state == sReleased):
                self._btnClose.SetState(0)
                self._selectedOutput = 0
                self.UIHost.HidePopup(self._inputsPopupName)
                self.hideInputFb()

    def __outputCallbackHandler(self, nOut):
        self._selectedOutput = nOut
        self.UIHost.ShowPopup(self._inputsPopupName)
        self._lblCurrentOut.SetText(self.outButtons.get(nOut).vName.replace("\n", " "))
        self.showInputFb(self.outButtons.get(nOut).currentInput)

    def __inputCallbackHandler(self, nIn):
        self.UIHost.HidePopup(self._inputsPopupName)
        self.hideInputFb()
        self.videoControlProxy.setTie(self._selectedOutput, nIn)
        self._selectedOutput = 0

    def _feedbackHandler(self, nOut: int, nIn: int):
        if (nOut in self.outButtons.keys()):
            self.outButtons.get(nOut).setFbSource(nIn,
                                                  self.inButtons.get(nIn).vName,
                                                  self.inButtons.get(nIn).vType)
        for iCon in self._connectedOuts:
            if (iCon["main"] == nOut):
                if (iCon["in"]):
                    if (nIn in iCon["in"]):
                        for iOut in iCon["slave"]:
                            self.switch(iOut, nIn)
                else:
                    for iOut in iCon["slave"]:
                        self.switch(iOut, nIn)

    def showInputFb(self, currentInput: int):
        self.inButtons.get(currentInput).setState(1)

    def hideInputFb(self):
        for iIn in self.inButtons:
            # if (self.inButtons.get(iIn).vInNumber > 0):
            self.inButtons.get(iIn).setState(0)


class VideoOutFastTie(object):
    def __init__(self,
                 UIHost: UIDevice,
                 videoControlProxy: VideoControlProxyMeta,
                 output: int,
                 outputName: str,
                 lblOutputNameID: int,
                 lblOutputCurrentInID: int):

        self.UIHost = UIHost

        self.videoControlProxy = videoControlProxy
        # todo что это за колбэк
        self.videoControlProxy.addFbCallbackFunction(self._feedbackHandler)

        self.output = output
        self.outputName = outputName

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
        self.videoControlProxy.setTie(self.output, nIn)

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
