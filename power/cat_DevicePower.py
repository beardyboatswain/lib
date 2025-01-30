#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib import event, Version
from extronlib.device import eBUSDevice, ProcessorDevice, UIDevice
from extronlib.interface import (CircuitBreakerInterface, ContactInterface,
    DigitalInputInterface, DigitalIOInterface, EthernetClientInterface,
    EthernetServerInterfaceEx, FlexIOInterface, IRInterface, PoEInterface,
    RelayInterface, SerialInterface, SWACReceptacleInterface, SWPowerInterface,
    VolumeInterface)
from extronlib.ui import Button, Knob, Label, Level
from extronlib.system import Clock, MESet, Timer, Wait

from lib.utils.debugger import debugger
from usr.var.usr_debug_mode import cat_DevicePower_dbg
dbg = debugger(cat_DevicePower_dbg, __name__)

import lib.utils.signals as signals
from lib.var.states import *


class CatMainPower(object):
    def __init__(self,
                 UIHost,
                 devName="Питание зала",
                 devNameLblID=None,
                 tglBtnID=None,
                 stateLblID=None, 
                 onBtnID=None, 
                 offBtnID=None, 
                 probeBtnID=None,
                 spinnerBtnID=None,
                 powerOffPageName=None,
                 powerOnPageName=None):
        
        self._UIHost = UIHost
        self._Dev = []
        
        self._power = "Off"
        self._powerOnInProcess = False
        self._powerOffInProcess = False

        self._rfbPowerCallback = self.rfb
                
        self._devName = str(devName)

        self.msg = {"On":"Зал включен", "Off":"Зал выключен", "Warming Up":"Зал включается", "Cooling Down":"Зал отключается"}

        self._devNameLblID = devNameLblID
        self._devNameLbl = None
        if self._devNameLblID is not None:
            self.devNameLbl = self._devNameLblID

        self._tglBtnID = tglBtnID
        self._tglBtn = None
        if self._tglBtnID is not None:
            self.tglBtn = self._tglBtnID

        self._onBtnID = onBtnID
        self._onBtn = None
        if self._onBtnID is not None:
            self.onBtn = self._onBtnID

        self._offBtnID = offBtnID
        self._offBtn = None
        if self._offBtnID is not None:
            self.offBtn = self._offBtnID

        self._probeBtnID = probeBtnID
        self._probeBtn = None
        if self._probeBtnID is not None:
            self.probeBtn = self._probeBtnID

        self._stateLblID = stateLblID
        self._stateLbl = None
        if self._stateLblID is not None:
            self.stateLbl = self._stateLblID

        self._spinnerBtnID = spinnerBtnID
        self._spinnerBtn = None
        if self._spinnerBtnID is not None:
            self.spinnerBtn = self._spinnerBtnID

        self._powerOffPageName = powerOffPageName
        if self._powerOffPageName is not None:
            self.powerOffPageName = self._powerOffPageName

        self._powerOnPageName = powerOnPageName
        if self._powerOnPageName is not None:
            self.powerOnPageName = self._powerOnPageName

        self._rfbPowerFbForVideoSw = None
        if self._rfbPowerFbForVideoSw is not None:
            self.rfbPowerFbForVideoSw = self._rfbPowerFbForVideoSw

    @property
    def devNameLbl(self):
        return self._devNameLbl

    @devNameLbl.setter
    def devNameLbl(self, buttonID):
        self._devNameLbl = Label(self._UIHost, buttonID)
        self._devNameLbl.SetText(self._devName)

    @property
    def tglBtn(self):
        return self._tglBtn

    @tglBtn.setter
    def tglBtn(self, buttonID):
        self._tglBtn = Button(self._UIHost, buttonID)
        @event(self._tglBtn, ['Pressed', 'Released'])
        def tglBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power Toggle')
                self.powerTgl()

    @property
    def onBtn(self):
        return self._onBtn

    @onBtn.setter
    def onBtn(self, buttonID):
        self._onBtn = Button(self._UIHost, buttonID)
        @event(self._onBtn, ['Pressed', 'Released'])
        def onBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power On')
                self.powerOn()
    
    @property
    def offBtn(self):
        return self._offBtn

    @offBtn.setter
    def offBtn(self, buttonID):
        self._offBtn = Button(self._UIHost, buttonID)
        @event(self._offBtn, ['Pressed', 'Released'])
        def offBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power Off')
                self.powerOff()

    @property
    def probeBtn(self):
        return self._probeBtn

    @probeBtn.setter
    def probeBtn(self, buttonID):
        self._probeBtn = Button(self._UIHost, buttonID)

    @property
    def stateLbl(self):
        return self._stateLbl

    @stateLbl.setter
    def stateLbl(self, labelID):
        self._stateLbl = Label(self._UIHost, labelID)
        self._stateLbl.SetText(self.msg[self._power])

    @property
    def devices(self):
        return self._Dev

    @devices.setter
    def devices(self, devProxy):
        if devProxy is not None:
            devProxy.rfbPowerCallback = self._rfbPowerCallback
            self._Dev.append(devProxy)

    @property
    def spinnerBtn(self):
        return self._spinnerBtn

    @spinnerBtn.setter
    def spinnerBtn(self, buttonID):
        self._spinnerBtn = Button(self._UIHost, buttonID)

    @property
    def powerOffPageName(self):
        return self._powerOffPageName

    @powerOffPageName.setter
    def powerOffPageName(self, pageName):
        self._powerOffPageName = pageName

    @property
    def powerOnPageName(self):
        return self._powerOnPageName

    @powerOnPageName.setter
    def powerOnPageName(self, pageName):
        self._powerOnPageName = pageName

    @property
    def rfbPowerFbForVideoSw(self):
        return self._rfbPowerFbForVideoSw

    @rfbPowerFbForVideoSw.setter
    def rfbPowerFbForVideoSw(self, callbackMethod):
        if (callable(callbackMethod)):
            if self._rfbPowerFbForVideoSw is None:
                self._rfbPowerFbForVideoSw = []
            self._rfbPowerFbForVideoSw.append(callbackMethod)

    def _ShowPage(self, pageName):
        if (pageName is not None):
            self._UIHost.ShowPage(pageName)

    def _SetSpinner(self, spinnerState):
        if (self.spinnerBtn is not None):
            self.spinnerBtn.SetState(spinnerState)

    def _SetStateText(self, stateText):
        if (self.stateLbl is not None):
            self.stateLbl.SetText(self.msg["Cooling Down"])

    def powerOn(self):
        print("Start power on")
        self._powerOffInProcess = False
        self._powerOnInProcess = True
        self._SetStateText(self.msg["Warming Up"])        
        self._SetSpinner(1)
        for device in self.devices:
            device.power("On")
        signals.emit('*', signal='roomkit', params={'cmd':'standby', 'action':'set', 'state':'Deactivate'})
        

    def powerOff(self):
        print("Start power off")
        self._powerOnInProcess = False
        self._powerOffInProcess = True
        self._ShowPage(self.powerOffPageName)
        self._SetSpinner(0)
        self._SetStateText(self.msg["Cooling Down"])
        for device in self.devices:
            device.power("Off")
        # signals.emit('*', signal='roomkit', params={'cmd':'standby', 'action':'set', 'state':'Activate'})

    def powerTgl(self):
        if (self._power == "On"):
            self.powerOff()
        elif (self._power == "Off"):
            self.powerOn()

    def powerSet(self, nPower:str):
        """nPower:"On, Off or Tgl"
        """
        if (nPower.title() == "On"):
            self.powerOn()
        elif (nPower.title() == "Off"):
            self.powerOff()
        elif (nPower.title() == "Tgl"):
            self.powerTgl()
        else:
            raise AttributeError("Wrong power value: {}".format(nPower))

    def rfbForVideo(self):
        if (self._rfbPowerFbForVideoSw):
            for method in self._rfbPowerFbForVideoSw:
                if callable(method):
                    method(self._power)

    def rfb(self, power):
        totalPowerDevs = len(self.devices)
        onDevs = 0
        offDevs = 0
        for device in self.devices:
            if (device._power == "On"):
                # self._power = "On"
                onDevs += 1
            elif (device._power == "Off"):
                offDevs += 1

        dbg.print("RFB. onDev={} offDev={}".format(onDevs, offDevs))

        if (self._powerOnInProcess and onDevs < totalPowerDevs):
            self._power = "Warming Up"
            dbg.print("Power STARTING. self._power={}".format(self._power))
        elif (self._powerOffInProcess and offDevs < totalPowerDevs):
            self._power = "Cooling Down"
            dbg.print("Power STOPPING. self._power={}".format(self._power))
        # переходить на страницу включенного зала, если все девайсы включены
        elif (onDevs >= totalPowerDevs):
            # включились
            self._power = "On"
            self._powerOnInProcess = False
            self._ShowPage(self.powerOnPageName)
            dbg.print("Power IS ON. onDev={} self._power={}".format(onDevs, self._power))
        # переходить на страницу отключенного зала, если все девайсы выключены
        elif (offDevs >= totalPowerDevs):
            # выключились
            self._power = "Off"
            self._powerOffInProcess = False
            self._ShowPage(self.powerOffPageName)
            dbg.print("Power IS OFF. offDev={} self._power={}".format(offDevs, self._power))

        if (self.devNameLbl):
            self.devNameLbl.SetText(self._devName) 
        if (self.tglBtn):
            self.tglBtn.SetState(2 if (self._power == "On") else 0)
        # if (self.onBtn):
        #     self.onBtn.SetState(1 if (self._power == "On") else 0)
        # if (self.offBtn):
        #     self.offBtn.SetState(1 if (self._power == "Off") else 0)
        if (self.probeBtn):
            self.probeBtn.SetState(1 if (self._power == "On") else 0)
        if (self.stateLbl):
            self.stateLbl.SetText(self.msg[self._power])

        self.rfbForVideo()


class CatDevicePower(object):
    def __init__(self,
                 UIHost,
                 Dev,
                 devName,
                 devNameLblID=None,
                 tglBtnID=None,
                 stateLblID=None, 
                 onBtnID=None, 
                 offBtnID=None, 
                 probeBtnID=None):
        
        self._UIHost = UIHost

        self._Dev = Dev
        self._Dev.rfbPowerCallback = self.rfb
        
        self._power = None

        self._devName = str(devName)
        self.msg = {"On":"Включено", "Off":"Отключено", "Warming Up":"Включается", "Cooling Down":"Отключается"}

        self._devNameLblID = devNameLblID
        self._devNameLbl = None
        if self._devNameLblID is not None:
            self.devNameLbl = self._devNameLblID

        self._tglBtnID = tglBtnID
        self._tglBtn = None
        if self._tglBtnID is not None:
            self.tglBtn = self._tglBtnID

        self._onBtnID = onBtnID
        self._onBtn = None
        if self._onBtnID is not None:
            self.onBtn = self._onBtnID

        self._offBtnID = offBtnID
        self._offBtn = None
        if self._offBtnID is not None:
            self.offBtn = self._offBtnID

        self._probeBtnID = probeBtnID
        self._probeBtn = None
        if self._probeBtnID is not None:
            self.probeBtn = self._probeBtnID
            
        self._stateLblID = stateLblID
        self._stateLbl = None
        if self._stateLblID is not None:
            self.stateLbl = self._stateLblID
        
        
    def setMsg(self, state, message):
        if (state in ["On", "Off"]):
            self.msg[state] = message

    @property
    def devNameLbl(self):
        return self._devNameLbl

    @devNameLbl.setter
    def devNameLbl(self, buttonID):
        self._devNameLbl = Label(self._UIHost, buttonID)
        self._devNameLbl.SetText(self._devName)

    @property
    def tglBtn(self):
        return self._tglBtn

    @tglBtn.setter
    def tglBtn(self, buttonID):
        self._tglBtn = Button(self._UIHost, buttonID)
        @event(self._tglBtn, ['Pressed', 'Released'])
        def tglBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power Toggle')
                self.powerTgl()


    @property
    def onBtn(self):
        return self._onBtn

    @onBtn.setter
    def onBtn(self, buttonID):
        self._onBtn = Button(self._UIHost, buttonID)
        @event(self._onBtn, ['Pressed', 'Released'])
        def onBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power On')
                self.powerOn()

    
    @property
    def offBtn(self):
        return self._offBtn

    @offBtn.setter
    def offBtn(self, buttonID):
        self._offBtn = Button(self._UIHost, buttonID)
        @event(self._offBtn, ['Pressed', 'Released'])
        def offBtnEvent(btn, state):
            btn.SetState(1) if (state == 'Pressed') else btn.SetState(0)
            if (state == 'Released'):
                dbg.print('Power Off')
                self.powerOff()

    @property
    def probeBtn(self):
        return self._probeBtn

    @probeBtn.setter
    def probeBtn(self, buttonID):
        self._probeBtn = Button(self._UIHost, buttonID)

    @property
    def stateLbl(self):
        return self._stateLbl

    @stateLbl.setter
    def stateLbl(self, buttonID):
        self._stateLbl = Label(self._UIHost, buttonID)


    def powerOn(self):
        self._Dev.power("On")

    def powerOff(self):
        self._Dev.power("Off")

    def powerTgl(self):
        self._Dev.power("Tgl")

    def powerSet(self, nPower:str):
        """nPower:"On, Off or Tgl"
        """
        if (nPower.title() == "On"):
            self.powerOn()
        elif (nPower.title() == "Off"):
            self.powerOff()
        elif (nPower.title() == "Tgl"):
            self.powerTgl()
        else:
            raise AttributeError("Wrong power value: {}".format(nPower))

    def rfb(self, power):
        if (power in self.msg.keys()):
            self._power = power

            if (self.devNameLbl):
                self.devNameLbl.SetText(self._devName) 
            if (self.tglBtn):
                self.tglBtn.SetState(2 if (self._power == "On") else 0)
            # if (self.onBtn):
            #     self.onBtn.SetState(1 if (self._power == "On") else 0)
            # if (self.offBtn):
            #     self.offBtn.SetState(1 if (self._power == "Off") else 0)
            if (self.probeBtn):
                self.probeBtn.SetState(1 if (self._power == "On") else 0)
            if (self.stateLbl):
                self.stateLbl.SetText(self.msg[self._power])

        else:
            raise TypeError("Illegal power state: {}".format(power))


class CatDevicePowerMultiBtn(object):
    def __init__(self,  devProxy, devName):

        self._Dev = devProxy
        self._Dev.rfbPowerCallback = self.rfb

        self._power = None

        self._devName = str(devName)
        self.msg = {"On": "Включено", "Off": "Отключено", "Warming Up": "Включается", "Cooling Down": "Отключается"}

        self._devNameLbl = []
        self._tglBtn = []
        self._onBtn = []
        self._offBtn = []
        self._probeBtn = []
        self._stateLbl = []

    def setMechanic(self, UIHost, devNameLblID=None, stateLblID=None, tglBtnID=None, onBtnID=None, offBtnID=None, probeBtnID=None):
        if (devNameLblID is not None):
            self._devNameLbl.append(Label(UIHost, devNameLblID))

        if (stateLblID is not None):
            self._stateLbl.append(Label(UIHost, stateLblID))

        if (tglBtnID is not None):
            self._tglBtn.append(Button(UIHost, tglBtnID))

        if (onBtnID is not None):
            self._tglBtn.append(Button(UIHost, onBtnID))

        if (offBtnID is not None):
            self._offBtn.append(Button(UIHost, offBtnID))

        if (probeBtnID is not None):
            self._probeBtn.append(Button(UIHost, probeBtnID))

        if (self._devNameLbl):
            for lbl in self._devNameLbl:
                lbl.SetText(self._devName)

        if (self._tglBtn):
            @event(self._tglBtn, sStates)
            def _tglBtnEventHandler(btn, state):
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
                dbg.print('Power Toggle')
                self.powerTgl()

        if (self._onBtn):
            @event(self._onBtn, sStates)
            def _onBtnEventHandler(btn, state):
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
                dbg.print('Power On')
                self.powerOn()

        if (self._offBtn):
            @event(self._offBtn, sStates)
            def _offBtnEventHandler(btn, state):
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
                dbg.print('Power Off')
                self.powerOff()

    def setMsg(self, state, message):
        if (state in ["On", "Off"]):
            self.msg[state] = message

    def powerOn(self):
        self._Dev.power("On")

    def powerOff(self):
        self._Dev.power("Off")

    def powerTgl(self):
        self._Dev.power("Tgl")

    def powerSet(self, nPower:str):
        """nPower:"On, Off or Tgl"
        """
        if (nPower.title() == "On"):
            self.powerOn()
        elif (nPower.title() == "Off"):
            self.powerOff()
        elif (nPower.title() == "Tgl"):
            self.powerTgl()
        else:
            raise AttributeError("Wrong power value: {}".format(nPower))

    def rfb(self, power):
        if (power in self.msg.keys()):
            self._power = power
            if (self._tglBtn):
                for btn in self._tglBtn:
                    btn.SetState(2 if (self._power == "On") else 0)
            if (self._probeBtn):
                for probe in self._probeBtn:
                    probe.SetState(1 if (self._power == "On") else 0)
            if (self._stateLbl):
                for lbl in self._stateLbl:
                    lbl.SetText(self.msg.get(self._power))
        else:
            raise TypeError("Illegal power state: {}".format(power))



class CatMainPowerMultiButton(object):
    def __init__(self, devName="Питание"):
        self._Dev = []
        self._Pages = []
        
        self._power = "Off"
        self._powerOnInProcess = False
        self._powerOffInProcess = False

        self._rfbPowerCallback = self.rfb
                
        self._devName = str(devName)
        
        self.msg = {"On":"Зал включен", "Off":"Зал выключен", "Warming Up":"Зал включается", "Cooling Down":"Зал отключается"}
        
        self._devNameLbl = []
        self._tglBtn = []
        self._onBtn = []
        self._offBtn = []
        self._probeBtn = []
        self._stateLbl = []
        self._spinnerBtn = []

        self._rfbPowerFbForVideoSw = None
        if self._rfbPowerFbForVideoSw is not None:
            self.rfbPowerFbForVideoSw = self._rfbPowerFbForVideoSw

    def setMechanic(self, UIHost, devNameLblID=None, stateLblID=None, tglBtnID=None, onBtnID=None, offBtnID=None, probeBtnID=None, spinnerBtnID=None, powerOffPageName=None, powerOnPageName=None):
        if (devNameLblID is not None):
            self._devNameLbl.append(Label(UIHost, devNameLblID))

        if (stateLblID is not None):
            self._stateLbl.append(Label(UIHost, stateLblID))

        if (onBtnID is not None):
            self._onBtn.append(Button(UIHost, onBtnID))

        if (offBtnID is not None):
            self._offBtn.append(Button(UIHost, offBtnID))

        if (tglBtnID is not None):
            self._tglBtn.append(Button(UIHost, tglBtnID))

        if (probeBtnID is not None):
            self._probeBtn.append(Button(UIHost, probeBtnID))

        if (spinnerBtnID is not None):
            self._spinnerBtn.append(Button(UIHost, spinnerBtnID))

        if (self._devNameLbl):
            for lbl in self._devNameLbl:
                lbl.SetText(self._devName)

        if (powerOffPageName is not None) or (powerOnPageName is not None):
            self._Pages.append({'UIHost':UIHost, 'OnPage':powerOnPageName, 'OffPage':powerOffPageName})

        if (self._tglBtn):
            @event(self._tglBtn, sStates)
            def _tglBtnEventHandler(btn, state):
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
                dbg.print('Power Toggle')
                self.powerTgl()

        if (self._onBtn):
            @event(self._onBtn, sStates)
            def _onBtnEventHandler(btn, state):
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
                dbg.print('Power On')
                self.powerOn()

        if (self._offBtn):
            @event(self._offBtn, sStates)
            def _offBtnEventHandler(btn, state):
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
                dbg.print('Power Off')
                self.powerOff()

    @property
    def devices(self):
        return self._Dev

    @devices.setter
    def devices(self, devProxy):
        if devProxy is not None:
            devProxy.rfbPowerCallback = self._rfbPowerCallback
            self._Dev.append(devProxy)

    @property
    def rfbPowerFbForVideoSw(self):
        return self._rfbPowerFbForVideoSw

    @rfbPowerFbForVideoSw.setter
    def rfbPowerFbForVideoSw(self, callbackMethod):
        if (callable(callbackMethod)):
            if self._rfbPowerFbForVideoSw is None:
                self._rfbPowerFbForVideoSw = []
            self._rfbPowerFbForVideoSw.append(callbackMethod)

    def _ShowPage(self, pageName):
        for pg in self._Pages:
            if (pg.get(pageName) and pg.get('UIHost')):
                pg.get('UIHost').ShowPage(pg.get(pageName) )

    def _SetSpinner(self, spinnerState):
        for spnr in self._spinnerBtn:
            spnr.SetState(spinnerState)

    def _SetStateText(self, stateText):
        for lbl in self._stateLbl:
            lbl.SetText(stateText)

    def powerOn(self):
        print("Start power on")
        self._powerOffInProcess = False
        self._powerOnInProcess = True
        self._SetStateText(self.msg["Warming Up"])        
        self._SetSpinner(1)
        for device in self.devices:
            device.power("On")
        if (self._devName == "Питание зала"):
            signals.emit('*', signal='roomkit', params={'cmd':'standby', 'action':'set', 'state':'Deactivate'})
        
    def powerOff(self):
        print("Start power off")
        self._powerOnInProcess = False
        self._powerOffInProcess = True
        self._ShowPage("OffPage")
        self._SetSpinner(0)
        self._SetStateText(self.msg["Cooling Down"])
        for device in self.devices:
            device.power("Off")
        #!!! переписать управление света со стандартным api, убрать костыль V
        # signals.emit('*', signal='roomkit', params={'cmd':'standby', 'action':'set', 'state':'Activate'})
        if (self._devName == "Питание зала"):
            signals.emit('*', signal = "lights", params={'cmd':'alloff'})
            signals.emit('*', signal='roomkit', params={'cmd':'standby', 'action':'set', 'state':'Activate'})

    def powerTgl(self):
        if (self._power == "On"):
            self.powerOff()
        elif (self._power == "Off"):
            self.powerOn()

    def powerSet(self, nPower:str):
        """nPower:"On, Off or Tgl"
        """
        if (nPower.title() == "On"):
            self.powerOn()
        elif (nPower.title() == "Off"):
            self.powerOff()
        elif (nPower.title() == "Tgl"):
            self.powerTgl()
        else:
            raise AttributeError("Wrong power value: {}".format(nPower))

    def rfbForVideo(self):
        if (self._rfbPowerFbForVideoSw):
            for method in self._rfbPowerFbForVideoSw:
                if callable(method):
                    method(self._power)
    
    def _updateUIfb(self):
        for btn in self._tglBtn:
            btn.SetState(2 if (self._power == "On") else 0)
        # if (self.onBtn):
        #     self.onBtn.SetState(1 if (self._power == "On") else 0)
        # if (self.offBtn):
        #     self.offBtn.SetState(1 if (self._power == "Off") else 0)
        for probe in self._probeBtn:
            self.probeBtn.SetState(1 if (self._power == "On") else 0)

        self._SetSpinner(1 if (self._power == "On") else 0)
        self._SetStateText(self.msg[self._power])


    def rfb(self, power):
        totalPowerDevs = len(self.devices)
        onDevs = 0
        offDevs = 0
        for device in self.devices:
            if (device._power == "On"):
                # self._power = "On"
                onDevs += 1
            elif (device._power == "Off"):
                offDevs += 1

        dbg.print("RFB. onDev={} offDev={}".format(onDevs, offDevs))

        if (self._powerOnInProcess and onDevs < totalPowerDevs):
            self._power = "Warming Up"
            dbg.print("Power STARTING. self._power={}".format(self._power))
        elif (self._powerOffInProcess and offDevs < totalPowerDevs):
            self._power = "Cooling Down"
            dbg.print("Power STOPPING. self._power={}".format(self._power))
        # переходить на страницу включенного зала, если все девайсы включены
        elif (onDevs > 0):
            # включились
            self._power = "On"
            self._powerOnInProcess = False
            self._ShowPage('OnPage')
            dbg.print("Power IS ON. onDev={} self._power={}".format(onDevs, self._power))
        # переходить на страницу отключенного зала, если все девайсы выключены
        elif (offDevs == totalPowerDevs):
            # выключились
            self._power = "Off"
            self._powerOffInProcess = False
            self._ShowPage('OffPage')
            dbg.print("Power IS OFF. offDev={} self._power={}".format(offDevs, self._power))
        
        self._updateUIfb()

        self.rfbForVideo()


