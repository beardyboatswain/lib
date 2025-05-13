#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List, Dict

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label

from lib.drv.gs.gs_hdla_bms_HDL_MBUS01IP431_v1_0_0_0 import EthernetClass

from lib.video.VideoControlProxyMeta import MatrixControlProxyMeta
from lib.var.states import sStates, sPressed, sReleased


class HDLCurtainsControl:
    def __init__(self, dev: EthernetClass, curt_name: str):
        self.dev = dev
        self.curt_name = curt_name

        self.hdl_devs: List[Dict] = list()

        self.name_lbls = list()
        self.up_btns = list()
        self.down_btns = list()
        self.stop_btns = list()

        self.up_cmd = 'Open'
        self.down_cmd = 'Close'
        self.stop_cmd = 'Stop'

    def add_hdl_device(self, *hdl_dev):
        '''
        *hdl_dev - list of dictionaries with keys: subnet_id, device_id, number
        Example: add_hdl_device({'subnet_id': 1, 'device_id': 1, 'number': 1}, {'subnet_id': 2, 'device_id': 2, 'number': 2})
        '''
        self.hdl_devs.extend(hdl_dev)

    def add_name_lbl(self, ui_host: UIDevice, lbl_id: Label):
        new_lbl = Label(ui_host, lbl_id)
        new_lbl.SetText(self.curt_name)
        self.name_lbls.append(new_lbl)

    def add_up_btn(self, ui_host: UIDevice, btn_id: Button):
        new_btn = Button(ui_host, btn_id)
        self.up_btns.append(new_btn)

        @event(self.up_btns, sStates)
        def up_btns_event_handler(btn: Button, state: str):
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
                self.send_cmd(self.up_cmd)

    def add_down_btn(self, ui_host: UIDevice, btn_id: Button):
        new_btn = Button(ui_host, btn_id)
        self.down_btns.append(new_btn)

        @event(self.down_btns, sStates)
        def down_btns_event_handler(btn: Button, state: str):
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
                self.send_cmd(self.down_cmd)

    def add_stop_btn(self, ui_host: UIDevice, btn_id: Button):
        new_btn = Button(ui_host, btn_id)
        self.stop_btns.append(new_btn)

        @event(self.stop_btns, sStates)
        def stop_btns_event_handler(btn: Button, state: str):
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
                self.send_cmd(self.stop_cmd)

    def send_cmd(self, cmd: str):
        for i_hdl_dev in self.hdl_devs:
            self.dev.Set('CurtainSwitch', cmd,
                         {'Target Subnet ID': str(i_hdl_dev.get('subnet_id')),
                          'Target Device ID': str(i_hdl_dev.get('device_id')),
                          'Number': str(i_hdl_dev.get('number'))})
