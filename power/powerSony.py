#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod

from extronlib import event
from extronlib.device import UIDevice
from extronlib.system import Timer, Wait
from extronlib.ui import Button

from lib.power.DevicePowerMeta import DevicePowerMeta

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.var.states import sStates, sPressed, sReleased

from lib.utils.ipcputils import HexUtils as Hex

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class LCDSonyEthernet(DevicePowerMeta):
    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev

        self.tglPowerBtns = list()

        self.rxBuf = str()
        self.power = "Off"

        self.fbCallbackFunctions = list()

        self.dev.subscribe('Connected', self.connectEventHandler)
        self.dev.subscribe('Disconnected', self.connectEventHandler)
        self.dev.subscribe('ReceiveData', self.rxEventHandler)

        self.dev.connect()

        self.pollTimer = Timer(10, self.pollDevice)

    def setMechanics(self, uiHost: UIDevice, btnTglPowerId: int):
        self.tglPowerBtns.append(Button(uiHost, btnTglPowerId))

        @event(self.tglPowerBtns, sStates)
        def tglPowerBtnsEventHandler(btn: Button, state: str):
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
                self.tgl_power()

    def get_power(self) -> str:
        return self.power

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def add_fb_callback_function(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.fbCallbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fbCallbackFunctions:
            cFunc(self.power)

    def connectEventHandler(self, interface, state):
        dbg.print("Bravia {} is {}!".format(self.dev.ip, state))

    def pollDevice(self, timer, counter):
        # self.dev.send("POWER REQUEST")
        self.dev.send("*SEPOWR################\x0a")

    def set_power(self, power: str):
        if (power == "On"):
            self.dev.send("*SCPOWR0000000000000001\x0a")
            # dbg.print("Brabia Power ON sent")
        elif (power == "Off"):
            self.dev.send("*SCPOWR0000000000000000\x0a")
            # dbg.print("Bravia Power OFF sent")

    def showFb(self):
        self.execute_callback_functions()
        for iBtn in self.tglPowerBtns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rxParser(self, rxLine: str):
        # dbg.print("RX lines:\n{}".format(rxLine))
        dataLines = rxLine

        for rxLine in dataLines.splitlines():
            if (rxLine.find("*SAPOWR0000000000000001") > -1):
                self.power = "On"
                self.showFb()
            elif (rxLine.find("*SAPOWR0000000000000000") > -1):
                self.power = "Off"
                self.showFb()

    def rxEventHandler(self, interface, data):
        # dbg.print("Sony {} recieved: {} ".format(self.dev.ip, data.decode()))
        self.rxBuf = data.decode()
        self.rxParser(data.decode())


class LCDSonySerialOverEthernet(DevicePowerMeta):
    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev
        self.uid = f'{self.dev.ip}:{self.dev.port}'

        self.tglPowerBtns = list()

        self.rxBuf = str()
        self.power = "Off"

        self.fbCallbackFunctions = list()

        self.dev.subscribe('Connected', self.connectEventHandler)
        self.dev.subscribe('Disconnected', self.connectEventHandler)
        self.dev.subscribe('ReceiveData', self.rxEventHandler)

        self.dev.connect()

        # self.pollTimer = Timer(30, self.pollDevice)
        dbg.print("Bravia created - {}".format(self.uid))

    def setMechanics(self, uiHost: UIDevice, btnTglPowerId: int):
        self.tglPowerBtns.append(Button(uiHost, btnTglPowerId))

        @event(self.tglPowerBtns, sStates)
        def tglPowerBtnsEventHandler(btn: Button, state: str):
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
                self.tgl_power()
                dbg.print("Bravia {} power toggled".format(self.uid))

    def get_power(self) -> str:
        return self.power

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def add_fb_callback_function(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.fbCallbackFunctions.append(fbCallbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fbCallbackFunctions:
            cFunc(self.power)

    def connectEventHandler(self, interface, state):
        dbg.print("Bravia {} - port {}!".format(self.uid, state))
        if self.dev.ConnectedFlag:
            self.pollDevice(0, 0)

    def pollDevice(self, timer, counter):
        dbg.print("Bravia {} - pollDevice. Connected {}".format(self.uid, self.dev.ConnectedFlag))
        self.dev.send(b"\x83\x00\x00\xff\xff\x81")

        # [70][00][02][01][73] - power is on
        # [70][00][02][00][72] - power is off

    def set_power(self, power: str):
        cmd = b''
        self.power = power

        if (self.power == "On"):
            cmd = b"\x8c\x00\x00\x02\x01\x8f"
        elif (self.power == "Off"):
            cmd = b"\x8c\x00\x00\x02\x00\x8e"
        
        self.dev.send(cmd)
        dbg.print("Bravia {} - power {} sent: {}".format(self.uid, self.power, Hex.line_bytes_to_hexstring(cmd)))
        self.showFb()
        @Wait(3)
        def poll_dev_wait_event():
            self.pollDevice(0, 0)

    def showFb(self):
        self.execute_callback_functions()
        for iBtn in self.tglPowerBtns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rxParser(self, rxLine: str):
        dbg.print("Bravia {} - RX lines:\n{}".format(self.uid, Hex.line_bytes_to_hexstring(rxLine)))
        dataLines = rxLine
        # no real fb for now
        for rxLine in dataLines.splitlines():
            if (rxLine.find(b"\x02\x01") > -1):
                dbg.print("Bravia POn find")
                self.power = "On"
                self.showFb()
            elif (rxLine.find(b"\x02\x00") > -1):
                dbg.print("Bravia POff find")
                self.power = "Off"
                self.showFb()

    def rxEventHandler(self, interface, data:bytes):
        dbg.print("Sony {} recieved: {} ".format(self.uid, Hex.line_bytes_to_hexstring(data)))
        # self.rxBuf = data.decode()
        self.rxParser(data.decode())
