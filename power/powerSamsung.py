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

from lib.utils.debugger import debugger
from lib.var.lib_debug_mode import powerSamsung_dbg
dbg = debugger(powerSamsung_dbg, __name__)


class SamsungHGxxAU8xxx(DevicePowerMeta):
    model_name = 'Samsung HG LCD'

    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev

        self.tgl_power_btns = list()

        self.rx_buf = str()
        self.power = "Off"

        self.h_id = self.model_name + ' (' + str(self.dev.ip) + ':' + str(self.dev.port) + ') '

        self.fb_callback_functions = list()

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', self.rx_event_handler)

        self.dev.connect()

        self.poll_timer = Timer(10, self.poll_device)

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

    def get_power(self) -> str:
        return self.power

    def add_fb_callback_function(self, fb_callback_function: Callable[[str], None]):
        if callable(fb_callback_function):
            self.fb_callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fb_callback_function' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fb_callback_functions:
            cFunc(self.power)

    def connect_event_handler(self, interface, state):
        dbg.print("{} {} is {}!".format(self.h_id, self.dev.ip, state))

    def poll_device(self, timer, counter):
        self.dev.send(b"\x68\x80\x03\x01\x00\xec")

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def set_power(self, power: str):
        if (power == "On"):
            self.dev.send(b"\x68\x80\x00\x01\x80\x69")
            dbg.print("{} Power ON sent".format(self.h_id))
        elif (power == "Off"):
            self.dev.send(b"\x68\x80\x00\x01\x00\xE9")
            dbg.print("{} Power OFF sent".format(self.h_id))

    def show_fb(self):
        self.execute_callback_functions()
        for iBtn in self.tgl_power_btns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rx_parser(self, rx_line: str):
        if (b'\x68\x00\x01\x04\x01' in rx_line):
            self.power = 'On'
            dbg.print("{} POWER <{}>".format(self.h_id, self.power))
        elif (b'\x68\x00\x01\x04\x00' in rx_line):
            self.power = 'Off'
            dbg.print("{} POWER <{}>".format(self.h_id, self.power))

    def rx_event_handler(self, interface: AutoEthernetConnection, data: bytes):
        dbg.print("{} recieved: {} ".format(self.h_id, data.decode()))
        self.rx_parser(data)


class SamsungQMxxR(DevicePowerMeta):
    model_name = 'Samsung QM LCD'

    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev

        self.tgl_power_btns = list()

        self.rx_buf = str()
        self.power = "Off"

        self.h_id = self.model_name + ' (' + str(self.dev.ip) + ':' + str(self.dev.port) + ') '

        self.fb_callback_functions = list()

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', self.rx_event_handler)

        self.dev.connect()

        self.poll_timer = Timer(10, self.poll_device)

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

    def get_power(self) -> str:
        return self.power

    def add_fb_callback_function(self, fb_callback_function: Callable[[str], None]):
        if callable(fb_callback_function):
            self.fb_callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fb_callback_function' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fb_callback_functions:
            cFunc(self.power)

    def connect_event_handler(self, interface, state):
        dbg.print("{} {} is {}!".format(self.h_id, self.dev.ip, state))

    def poll_device(self, timer, counter):
        self.dev.send(b"\xaa\x11\x01\x00\x12")

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def set_power(self, power: str):
        if (power == "On"):
            self.dev.send(b"\xaa\x11\x01\x01\x01\x14")
            dbg.print("{} Power ON sent".format(self.h_id))
        elif (power == "Off"):
            self.dev.send(b"\xaa\x11\x01\x01\x00\x13")
            dbg.print("{} Power OFF sent".format(self.h_id))

    def show_fb(self):
        self.execute_callback_functions()
        for iBtn in self.tgl_power_btns:
            iBtn.SetState(2 if self.power == "On" else 0)

    def rx_parser(self, rx_line: str):
        if (b'\xaa\xff\x01\x03\x41\x11\x01\x56' in rx_line):
            self.power = 'On'
            dbg.print("{} POWER <{}>".format(self.h_id, self.power))
        elif (b'\xaa\xff\x01\x03\x41\x11\x00\x55' in rx_line):
            self.power = 'Off'
            dbg.print("{} POWER <{}>".format(self.h_id, self.power))

    def rx_event_handler(self, interface: AutoEthernetConnection, data: bytes):
        dbg.print("{} recieved: {} ".format(self.h_id, data.decode()))
        self.rx_parser(data)
