#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List
import re

from extronlib import event
from extronlib.device import UIDevice
from extronlib.interface import SerialInterface
from extronlib.system import Timer, Wait
from extronlib.ui import Button

from lib.power.DevicePowerMeta import DevicePowerMeta
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.utils.ipcputils import HexUtils
from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class LCDLGSerial(object):
    def __init__(self, dev: SerialInterface):
        self.dev = dev

        self.tglPowerBtns = list()

        self.devID = "01"
        self.rxBuf = str()
        self.power = "Off"

        self.fbFunctions = list()

        self.LGMatchPowerFb = re.compile("a [0-9]{2} OK([0-9]{2})")

        @event(self.dev, "ReceiveData")
        def rxEventHandler(interface: SerialInterface, rx: str):
            dbg.print("LCD {} - Rx: {}".format(interface.Port, rx.decode()))
            self.rxBuf += rx.decode()
            self.rxParser(self.rxBuf.split("\x78"))
            self.rxBuf = ""

        self.pollTimer = Timer(10, self.pollDevice)

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglPowerBtns.append(Button(uiHost, btnTglPowerID))

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
                self.tglPower()

    def tglPower(self):
        if (self.power == "On"):
            self.setPower("Off")
        else:
            self.setPower("On")

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def pollDevice(self, timer, counter):
        self.dev.Send("ka {} ff\x0d\x0a".format(self.devID))

    def setPower(self, power: str):
        self.dev.Send("ka {} {}\x0d\x0a".format(self.devID, ("01" if power == "On" else "00")))

    def rxParser(self, rxLines: str):
        dbg.print("Parser: {}".format(rxLines))
        for rxLine in rxLines:
            dbg.print("Line: {}".format(rxLine))
            LGMatchObject = self.LGMatchPowerFb.search(rxLine)
            if LGMatchObject:
                dbg.print("RE Match!")
                powerState = LGMatchObject.group(1)
                dbg.print("Port {} - Power {}".format(self.dev.Port, powerState))
                self.power = "On" if powerState == "01" else "Off"
                self.showFb()

    def showFb(self):
        for iBtn in self.tglPowerBtns:
            iBtn.SetState(2 if self.power == "On" else 0)


class LCDLGSerialOverEthernet(DevicePowerMeta):
    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev
        self.uid = f'{self.dev.ip}:{self.dev.port}'

        self.tgl_power_btns: List[Button] = list()

        self.dev_id = "01"
        self.power = "Off"

        self.fb_callback_functions = list()

        self.match_power_fb = re.compile("a [0-9]{2} OK([0-9]{2})")

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', self.rx_event_handler)

        self.dev.connect()

        # self.pollTimer = Timer(30, self.pollDevice)
        dbg.print("LG created - {}".format(self.uid))

    def set_mechanics(self, ui_host: UIDevice, btn_tgl_power_id: int):
        self.tgl_power_btns.append(Button(ui_host, btn_tgl_power_id))

        @event(self.tgl_power_btns, sStates)
        def tgl_power_btns_event_handler(btn: Button, state: str):
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
                dbg.print("LG {} power toggled".format(self.uid))

    def get_power(self) -> str:
        return self.power

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def add_fb_callback_function(self, fb_callback_function: Callable[[str], None]):
        if callable(fb_callback_function):
            self.fb_callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self):
        for i_func in self.fb_callback_functions:
            i_func(self.power)

    def connect_event_handler(self, interface, state):
        dbg.print("LG {} - port {}!".format(self.uid, state))
        if self.dev.connected_fl:
            self.poll_device(0, 0)

    def poll_device(self, timer, counter):
        dbg.print("LG {} - pollDevice. Connected {}".format(self.uid, self.dev.connected_fl))
        self.dev.send("ka {} ff\x0d\x0a".format(self.dev_id))
        # [70][00][02][01][73] - power is on
        # [70][00][02][00][72] - power is off

    def set_power(self, power: str):
        self.power = power.title()
        cmd = "ka {} {}\x0d\x0a".format(self.dev_id, ("01" if power == "On" else "00"))
        self.dev.send(cmd)

        dbg.print("LG {} - power {} sent: {}".format(self.uid, self.power, HexUtils.line_bytes_to_hexstring(cmd)))
        self.show_fb()

        @Wait(3)
        def poll_dev_wait_event():
            self.poll_device(0, 0)

    def show_fb(self):
        self.execute_callback_functions()
        for iBtn in self.tgl_power_btns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rx_parser(self, rx_lines: str):
        dbg.print("Parser: {}".format(rx_lines))
        for rx_line in rx_lines:
            dbg.print("Line: {}".format(rx_line))
            lg_match_object = self.match_power_fb.search(rx_line)
            if lg_match_object:
                dbg.print("RE Match!")
                power_state = lg_match_object.group(1)
                dbg.print("Port {} - Power {}".format(self.dev.port, power_state))
                self.power = "On" if power_state == "01" else "Off"
                self.show_fb()

    def rx_event_handler(self, interface, data: Union[bytes, str]):
        dbg.print("Sony {} received: {} ".format(self.uid, HexUtils.line_bytes_to_hexstring(data)))
        # self.rxBuf = data.decode()
        self.rx_parser(data.decode())
