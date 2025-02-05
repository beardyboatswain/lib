#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union
import re
import time

from extronlib.system import Timer, Wait
from extronlib.device import UIDevice
from extronlib.ui import Button
from extronlib import event

import lib.utils.signals as signals
from lib.var.states import sStates, sPressed, sReleased

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class AtenPDUTelnet(object):
    def __init__(self, device: AutoEthernetConnection, outlet_size: int):

        self.device = device

        self.u_id = self.device.ip + ':' + str(self.device.port)

        self.outlet_size = outlet_size
        self.states = dict()
        self.state_all = 'off'

        self.power_tgl_all_btn = list()
        self.power_on_all_btn = list()
        self.power_off_all_btn = list()
        self.power_tgl_btns = dict()

        for i_outlet in range(1, self.outlet_size + 1):
            self.power_tgl_btns[i_outlet] = list()

        self.outlet_state_match_fb = re.compile("Outlet ([0-9]{2}) (on|off)")
        self.login_match_fb = re.compile("Login:")
        self.password_match_fb = re.compile("Password:")
        self.loginok_match_fb = re.compile("Logged in successfully")
        self.device.subscribe("Connected", self.connect_event_handler)
        self.device.subscribe("Disconnected", self.connect_event_handler)
        self.device.subscribe("ReceiveData", self.receive_data_handler)
        self.rx_buf = str()
        self.renew_timer = Timer(20, self.refres_outlets_state)
        self.renew_timer.Stop()
        self.device.connect()

    def refres_outlets_state(self, timer: Timer = None, count: int = 0):
        for i_outlet in range(1, self.outlet_size + 1):
            self.request_outlet_state(i_outlet)

    def request_outlet_state(self, n_outlet: int = None):
        # dbg.print('PDU[{}]: Request Outlet {} status!'.format(self.u_id, n_outlet))
        self.device.send("read status o{:02} format\x0d\x0a".format(n_outlet))

    def set_outlet_state(self, n_outlet: int, n_state: str) -> None:
        '''
        n_outlet: int - outlet number to set power
        n_state: str - state to set (on|off)
        '''
        self.device.send("sw o{:02} {} imme\r\n".format(n_outlet, n_state))
        self.request_outlet_state(n_outlet)

    def get_outlet_state(self, n_outlet: int) -> str:
        return self.states.get(n_outlet)

    def toggle_outlet_state(self, n_outlet: int) -> None:
        if self.states[n_outlet] == "on":
            self.set_outlet_state(n_outlet, n_state="off")
        else:
            self.set_outlet_state(n_outlet, n_state="on")

    def set_all_outlets_state(self, n_state: str) -> None:
        '''
        n_state: str - state to set (on|off|tgl)
        '''
        set_state = 'off'
        if (n_state == 'tgl'):
            set_state = 'on' if (self.state_all == 'off') else 'off'
        else:
            set_state = n_state

        for i_outlet in range(1, self.outlet_size + 1):
            self.set_outlet_state(i_outlet, set_state)
        self.refres_outlets_state()

    def add_tgl_btn(self, ui_host: UIDevice, button_id: int, outlet: int) -> None:
        if outlet in self.power_tgl_btns.keys():
            self.power_tgl_btns[outlet].append(Button(ui_host, button_id))

        @event(self.power_tgl_btns[outlet], sStates)
        def power_tgl_btns_event_andler(btn: Button, state: str):
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
                self.toggle_outlet_state(outlet)

    def add_tgl_all_btn(self, ui_host: UIDevice, button_id: int):
        self.power_tgl_all_btn.append(Button(ui_host, button_id))

        @event(self.power_tgl_all_btn, sStates)
        def power_tgl_all_btn_event_andler(btn: Button, state: str):
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
                self.set_all_outlets_state('tgl')

    def add_on_all_btn(self, ui_host: UIDevice, button_id: int):
        self.power_on_all_btn.append(Button(ui_host, button_id))

        @event(self.power_on_all_btn, sStates)
        def power_on_all_btn_event_andler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sReleased):
                btn.SetState(0)
                self.set_all_outlets_state('on')

    def add_off_all_btn(self, ui_host: UIDevice, button_id: int):
        self.power_off_all_btn.append(Button(ui_host, button_id))

        @event(self.power_off_all_btn, sStates)
        def power_off_all_btn_event_andler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sReleased):
                btn.SetState(0)
                self.set_all_outlets_state('off')

    def connect_event_handler(self, interface, state):
        dbg.print("PDU [{}] - {}".format(self.u_id, state))

    def update_btn(self, outlet_id: int):
        outlet_state = self.states[outlet_id]

        for i_btn in self.power_tgl_btns[outlet_id]:
            i_btn.SetState(0 if outlet_state == "off" else 2)

        if (outlet_state == 'on'):
            self.state_all = 'on'
        else:
            self.state_all = 'off'
            for i_outlet in self.states:
                if (self.states[i_outlet] == 'on'):
                    self.state_all = 'on'
                    break

        for i_btn in self.power_tgl_all_btn:
            i_btn.SetState(0 if self.state_all == "off" else 2)

    def rx_parser(self, rx: str):
        rx_lines = rx
        # dbg.print('Parse rx line [{}]'.format(rx))

        for rx in rx_lines.splitlines():

            login_match_fbo = self.login_match_fb.search(rx)
            if login_match_fbo:
                self.device.send(self.device.login + "\r\n")

            password_match_fbo = self.password_match_fb.search(rx)
            if password_match_fbo:
                self.device.send(self.device.password + "\r\n")

            loginok_match_fbo = self.loginok_match_fb.search(rx)
            if loginok_match_fbo:
                self.refres_outlets_state()
                self.renew_timer.Restart()

            outlet_state_match_fbo = self.outlet_state_match_fb.search(rx)
            if outlet_state_match_fbo:
                outlet_id = int(outlet_state_match_fbo.group(1))
                outlet_st = str(outlet_state_match_fbo.group(2))
                self.states[outlet_id] = outlet_st
                self.update_btn(outlet_id)
                dbg.print("Outlet {} - {}".format(outlet_id, outlet_st))

    def receive_data_handler(self, interface: AutoEthernetConnection, data: Union[str, bytes]):
        # dbg.print("Aten recieved from [{}]: {} ".format(interface, data.decode()))

        self.rx_buf += data.decode()

        while ((self.rx_buf.find("\x0d\x0a") > -1)
                or (self.rx_buf.find("Login:") > -1)
                or (self.rx_buf.find("Password") > -1)):
            self.rx_parser(self.rx_buf + "\n")
            self.rx_buf = ""
