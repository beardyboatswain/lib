#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List
from abc import ABCMeta, abstractmethod
from extronlib.interface import (EthernetClientInterface,
                                 EthernetServerInterfaceEx,
                                 SerialInterface)

from extronlib import event
from extronlib.device import UIDevice
from extronlib.system import Timer, Wait
from extronlib.ui import Button

from lib.power.DevicePowerMeta import DevicePowerMeta
from lib.var.states import sStates, sPressed, sReleased
from lib.drv.gs.gs_nvstr_vprocessor_J6_v1_0_1_0 import EthernetClass as NovastarEthClass
from lib.utils.debugger import debugger
NovastarControl_dbg = 'no'
dbg = debugger(NovastarControl_dbg, __name__)


class NovastarControl(DevicePowerMeta):
    def __init__(self, dev: NovastarEthClass):
        self.dev: NovastarEthClass = dev

        self.dev.Connect()

        self.tgl_power_btns: List[Button] = list()
        self.layout_btns = list()

        self.current_layout = 0
        self.power = "Off"

        self.default_power_on_layout = 2
        self.default_power_off_layout = 1

        self.fb_callback_functions = list()

    def add_power_btn(self, ui_host: UIDevice, btn_power_tgl_id: int):
        self.tgl_power_btns.append(Button(ui_host, btn_power_tgl_id))

        @event(self.tgl_power_btns, sStates)
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

    def add_layout_btn(self, ui_host: UIDevice, btn_layout_id: int, layout: int):
        new_btn = Button(ui_host, btn_layout_id)
        setattr(new_btn, 'layout', layout)
        self.layout_btns.append(new_btn)

        @event(self.layout_btns, sStates)
        def layout_btn_event(btn: Button, state: str) -> None:
            if state == sPressed:
                btn.SetState(1)
            elif state == sReleased:
                btn.SetState(0)
                self.set_layout(getattr(btn, 'layout'))

    def set_layout(self, layout: int):
        if (layout > 0):
            self.current_layout = layout
            self.dev.Set('Preset', self.current_layout, {'Command': 'Load'})
            if (self.current_layout == 1):
                self.power = "Off"
            else:
                self.power = "On"
            self.showFb()

    def get_power(self) -> str:
        return self.power

    def tgl_power(self):
        if (self.power == "On"):
            self.set_power("Off")
        else:
            self.set_power("On")

    def set_power(self, power: str):
        if (power == "On"):
            self.set_layout(self.default_power_on_layout)
        elif (power == "Off"):
            self.set_layout(self.default_power_off_layout)

    def add_fb_callback_function(self, fb_callback_function: Callable[[str], None]):
        if callable(fb_callback_function):
            self.fb_callback_functions.append(fb_callback_function)
        else:
            raise TypeError("Param 'fb_callback_function' is not Callable")

    def execute_callback_functions(self):
        for cFunc in self.fb_callback_functions:
            cFunc(self.power)

    def showFb(self):
        self.execute_callback_functions()
        for iBtn in self.tgl_power_btns:
            iBtn.SetState(2 if self.power == "On" else 0)
