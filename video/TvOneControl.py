#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List
from abc import ABCMeta, abstractmethod
from extronlib.interface import (EthernetClientInterface,
                                 EthernetServerInterfaceEx,
                                 SerialInterface)
from lib.helpers.AutoSerialConnection import AutoSerialConnection
from lib.video.VideoControlProxyMeta import SwitcherControlProxyMeta

from extronlib import event
from extronlib.device import UIDevice
from extronlib.system import Timer, Wait
from extronlib.ui import Button

from lib.power.DevicePowerMeta import DevicePowerMeta

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.ipcputils import HexUtils

from lib.utils.debugger import debugger
LEDPowerTvOne_dbg = 'no'
dbg = debugger(LEDPowerTvOne_dbg, __name__)


class TvOne(DevicePowerMeta):
    def __init__(self, dev: Union[EthernetClientInterface, EthernetServerInterfaceEx, SerialInterface]):
        self.dev: Union[EthernetClientInterface, EthernetServerInterfaceEx, SerialInterface] = dev

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
            self.dev.Set('PresetRecall', self.current_layout)
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


class TvOneSwitcherControl(SwitcherControlProxyMeta):
    """
    Control Class fro Switcher Aten UC3430
    """
    def __init__(self,
                 dev: AutoSerialConnection,
                 in_size: int):
        super().__init__()

        self.dev = dev
        self.current_in = 0

        self.out_number = 1

        self.in_size = in_size

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', self.rx_event_handler)

        self.poll_time_interval = 300
        self.refresh_fb_timer = Timer(self.poll_time_interval, self.poll)
        self.refresh_fb_timer.Stop()

    def add_fb_callback_function(self, fb_callback_func: Callable[[int], None]):
        if callable(fb_callback_func):
            self.fb_callback_functions.append(fb_callback_func)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def execute_callback_functions(self):
        for i_func in self.fb_callback_functions:
            i_func(self.out_number, self.current_in)

    def poll(self, timer: Timer, count: int) -> None:
        pass

    def set_tie(self, n_in: int, n_out: int = 1) -> None:
        # TvOneInterface.Send('F041041024F000291??\r')
        # TvOneInterface.Send('F041041024F000292??\r')
        if (0 <= (n_in - 1) <= (self.in_size - 1)):
            cmd = 'F041041024F00029{}??\r'.format(n_in)
            self.current_in = n_in
            self.dev.send(cmd)
            self.execute_callback_functions()

    def get_tie(self) -> int:
        return self.current_in

    def connect_event_handler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.dev.send("\x0d")
            dbg.print("TvOne Switcher Connected!")
            self.refresh_fb_timer.Restart()
        elif (state == 'Connected'):
            self.dev.send("\x0d")
            dbg.print("TvOne Switcher Connected!")

    def rx_parser(self, rx_lines: str):
        data_lines = rx_lines

        for rx_line in data_lines.splitlines():
            dbg.print("Aten: {}".format(rx_line))

    def rx_event_handler(self, interface, data: Union[str, bytes]):
        self.rx_parser(data.decode())
