#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label
from extronlib.system import MESet

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta
from lib.var.states import sStates, sPressed, sReleased

from lib.video.VideoControl import VideoOutputType, VideoInputType

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class VideoInput():
    def __init__(self,
                 in_name: str,
                 in_id: int,
                 in_number: int,
                 ui_host: UIDevice,
                 btn_base_id: int,
                 in_type: int,
                 is_virtual: bool = False):
        '''
        Input class for virtual or real input on matrix. Virtual input can be connected to defferent 
        real inputs on matrix depends on programm state.
        in_name: str - name of input
        in_id: int - inner id of input
        in_number: int - number of input in matrix
        ui_host: UIDevice - UI device for button
        btn_base_id: int - base id of button, next 3 id will be use
            btn_base_id + 0 - main input button
            btn_base_id + 1 - button for input name
            btn_base_id + 2 - button for input icon
            btn_base_id + 3 - button for input number
        in_type: int - type of input, actually determines ico for input button (see VideoInputType)
        is_virtual: bool = False - is button connected to virtual input or real input on matrix
        '''
        self.in_name = in_name
        self.in_id = in_id
        self.in_number = in_number
        self.ui_host = ui_host
        self.btn_base_id = btn_base_id
        self.in_type = in_type
        self.is_virtual = is_virtual

        # Callback function if btn presset
        self._callback_functions = list()

        self._btn_main = Button(self.ui_host, self.btn_base_id)
        self._btn_in_name = Button(self.ui_host, self.btn_base_id + 1)
        self._btn_in_name.SetText(self.in_name)
        self._btn_input_ico = Button(self.ui_host, self.btn_base_id + 2)
        self._btn_input_ico.SetState(self.in_type)
        self._btn_input_number = Button(self.ui_host, self.btn_base_id + 3)
        if self.is_virtual:
            self._btn_input_number.SetText("V" + str(self.in_number))
        else:
            self._btn_input_number.SetText(str(self.in_number))

        self._act_btns = [self._btn_main,
                          self._btn_in_name,
                          self._btn_input_ico,
                          self._btn_input_number]

        @event(self._act_btns, sStates)
        def _act_btns_event_handler(btn: Button, state: str):
            if (state == sPressed):
                self.set_state(1)
            elif (state == sReleased):
                self.set_state(0)
                self.execute_callback_functions()

    def add_callback_function(self, fb_callback_function: Callable[[int, bool], None]):
        '''
        Add callback function which will be called when input button pressed
        fbCallbackFunction: Callable[[int], None] - callback function
        '''
        if callable(fb_callback_function):
            self._callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self):
        '''
        Call all callback functions using real input number or virtual input number
        '''
        for i_func in self._callback_functions:
            i_func(self.in_number, self.in_id)

    def set_state(self, state: int):
        """
        Set button active/inactive to show real fb
        """
        dbg.print("Button {} - Current state {}".format(self._btn_main.ID, self._btn_main.State))
        if ((state == 1) and (self._btn_main.State == 0)):
            self._btn_main.SetState(2)
            self._btn_in_name.SetState(2)
            self._btn_input_number.SetState(2)
            self._btn_input_ico.SetState(self.in_type + 1)
        elif ((state == 0) and (self._btn_main.State == 2)):
            self._btn_main.SetState(0)
            self._btn_in_name.SetState(0)
            self._btn_input_number.SetState(0)
            self._btn_input_ico.SetState(self.in_type)


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


class VideoOutput(object):
    def __init__(self,
                 out_name: str,
                 out_number: int,
                 ui_host: UIDevice,
                 btn_base_id: int,
                 out_type: int):
        """
        out_name: str - output name
        out_number: int - output number in matrix
        ui_host: UIDevice - UIDevice for out button
        btn_base_id: int - first id for group of buttons for output control, next 5 ids will be used
                           For examle: vBtnBaseID = 11, 12-16 used
            btn_base_id + 0 - main button
            btn_base_id + 1 - output name
            btn_base_id + 2 - input ico
            btn_base_id + 3 - input name
            btn_base_id + 4 - type ico
        out_type: int -  type of output, actually determines ico for output button (see VideoOutputType)
        """
        self.out_name = out_name
        self.out_number = out_number
        self.ui_host = ui_host
        self.btn_base_id = btn_base_id
        self.out_type = out_type

        self.current_input = 0
        self.current_input_id = 0

        self._btn_main = Button(self.ui_host, self.btn_base_id)
        self._btn_out_name = Button(self.ui_host, self.btn_base_id + 1)
        self._btn_out_name.SetText(self.out_name.replace("\n", " "))
        self._btn_input_ico = Button(self.ui_host, self.btn_base_id + 2)
        self._btn_input_name = Button(self.ui_host, self.btn_base_id + 3)
        self._btn_type_ico = Button(self.ui_host, self.btn_base_id + 4)
        self._btn_type_ico.SetState(self.out_type)
        self._btn_out_number = Button(self.ui_host, self.btn_base_id + 5)
        self._btn_out_number.SetText(str(self.out_number))

        # callback function if btn pressed
        self._callback_functions = list()

        self._act_btns = [self._btn_main,
                          self._btn_out_name,
                          self._btn_input_ico,
                          self._btn_input_name,
                          self._btn_type_ico,
                          self._btn_out_number]

        @event(self._act_btns, sStates)
        def _act_btns_event_handler(btn, state):
            # dbg.print("ActBtnsEventHandler - Out <{}> - State <{}>".format(getattr(btn, "nOut"), state))
            if (state == sPressed):
                self._btn_main.SetState(1)
            elif (state == sReleased):
                self._btn_main.SetState(0)
                self.execute_callback_functions()
                # dbg.print("Out <{}> selected!".format(getattr(btn, "nOut")))
                # self.executeCallbackFunctions(getattr(btn, "nOut"))

    def add_callback_function(self, fb_callback_function: Callable[[int], None]):
        if callable(fb_callback_function):
            self._callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self, nOut: int):
        for cFunc in self._callback_functions:
            cFunc(nOut)

    def set_fb_source(self, current_input: int, current_input_name: str, current_input_ico: int):
        self.current_input = current_input
        self._btn_input_name.SetText(current_input_name)
        self._btn_input_ico.SetState(current_input_ico)


class VideoControl(object):
    '''
    Class for gui control for any video matrix switcher
    '''
    def __init__(self, UIHost: UIDevice,
                 videoControlProxy: VideoControlProxyMeta):
        self.UIHost = UIHost

        self.videoControlProxy = videoControlProxy
        self.videoControlProxy.add_callback_functions(self._feedbackHandler)

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
        cVideoControlNew = VideoOutput(out_name=vName,
                                       out_number=vOutNumber,
                                       ui_host=self.UIHost,
                                       btn_base_id=vBtnBaseID,
                                       out_type=vType)
        cVideoControlNew.add_callback_function(self.__outputCallbackHandler)
        self.outButtons[vOutNumber] = cVideoControlNew

    def addInputButton(self,
                       vName: str,
                       vInNumber: int,
                       vBtnBaseID: int,
                       vType: int):
        videoInputNew = VideoInput(in_name=vName,
                                   in_number=vInNumber,
                                   ui_host=self.UIHost,
                                   btn_base_id=vBtnBaseID,
                                   in_type=vType)
        videoInputNew.add_callback_function(self.__inputCallbackHandler)
        self.inButtons[vInNumber] = videoInputNew

    def switch(self, nOut: int, nIn: int):
        dbg.print("Switching!!!!!!!!!")
        self.videoControlProxy.set_tie(nOut, nIn)

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
                            self.videoControlProxy.set_tie(iOut, nIn)
                else:
                    for iOut in iCon["slave"]:
                        dbg.print("Linked switch out {} - in {} ".format(iOut, nIn))
                        self.videoControlProxy.set_tie(iOut, nIn)

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
        self.videoControl.videoControlProxy.add_callback_functions(self._feedbackHandler)

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
