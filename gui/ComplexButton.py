#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List

from extronlib import event
from extronlib.system import Wait
from extronlib.device import UIDevice
from extronlib.ui import Button

from lib.var.states import sStates, sPressed, sReleased, sHeld, sTapped, sRepeated

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no ', __name__)


class ComplexButton(object):
    def __init__(self,
                 ui_host: UIDevice,
                 base_id: int,
                 name: str = '',
                 comment: str = '',
                 hold_time: int = None,
                 repeat_time: int = None):
        """
        ui_host: UIDevice - UI Host Device
        base_id: int - id of main button, next two id will be use (base_id + 1 and base_id + 2)
        """
        self.main_btn = Button(ui_host, base_id, holdTime=hold_time, repeatTime=repeat_time)
        self.name_btn = Button(ui_host, base_id + 1, holdTime=hold_time, repeatTime=repeat_time)
        self.comment_btn = Button(ui_host, base_id + 2, holdTime=hold_time, repeatTime=repeat_time)
        self.btns = [self.main_btn, self.name_btn, self.comment_btn]

        self.name_btn.SetText(name)
        self.comment_btn.SetText(comment)

        self.method = None
        self.args = None
        self.kwargs = None

        @event(self.btns, sStates)
        def main_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    for i_btn in self.btns:
                        i_btn.SetState(1)
                elif (btn.State == 2):
                    for i_btn in self.btns:
                        i_btn.SetState(3)

            elif (state == sReleased):
                if (btn.State == 1):
                    for i_btn in self.btns:
                        i_btn.SetState(0)
                elif (btn.State == 3):
                    for i_btn in self.btns:
                        i_btn.SetState(2)
                self.call_action()

            elif (state == sRepeated):
                self.call_action()

            elif (state == sTapped):
                if (btn.State == 0):
                    for i_btn in self.btns:
                        i_btn.SetState(1)
                elif (btn.State == 2):
                    for i_btn in self.btns:
                        i_btn.SetState(3)
                self.call_action()

                @Wait(0.3)
                def tapped_wait_handler():
                    if (btn.State == 1):
                        for i_btn in self.btns:
                            i_btn.SetState(0)
                    elif (btn.State == 3):
                        for i_btn in self.btns:
                            i_btn.SetState(2)

    def add_action(self, method: Callable, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def call_action(self):
        dbg.print('Call action!')
        if (self.method is not None):
            self.method(*self.args, **self.kwargs)


class ComplexButtonPopup(object):
    def __init__(self,
                 ui_host: UIDevice,
                 base_id: int,
                 name: str = '',
                 comment: str = '',
                 popup_name: str = ''):
        """
        ui_host: UIDevice - UI Host Device
        base_id: int - id of main button, next three id will be use (base_id + 1 and base_id + 2,
                        base_id + 3 - for close popup btn)
        """
        self.ui_host = ui_host

        self.main_btn = Button(ui_host, base_id)
        self.name_btn = Button(ui_host, base_id + 1)
        self.comment_btn = Button(ui_host, base_id + 2)
        self.close_btn = Button(ui_host, base_id + 3)

        self.btns = [self.main_btn, self.name_btn, self.comment_btn]

        self.name_btn.SetText(name)
        self.comment_btn.SetText(comment)

        self.popup_name = popup_name

        @event(self.btns, sStates)
        def main_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                if (btn.State == 0):
                    for i_btn in self.btns:
                        i_btn.SetState(1)
                elif (btn.State == 2):
                    for i_btn in self.btns:
                        i_btn.SetState(3)
            elif (state == sReleased):
                if (btn.State == 1):
                    for i_btn in self.btns:
                        i_btn.SetState(0)
                elif (btn.State == 3):
                    for i_btn in self.btns:
                        i_btn.SetState(2)
                self.ui_host.ShowPopup(self.popup_name)

        @event(self.close_btn, sStates)
        def close_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                self.close_btn.SetState(1)
            elif (state == sReleased):
                self.close_btn.SetState(0)
                self.ui_host.HidePopup(self.popup_name)
