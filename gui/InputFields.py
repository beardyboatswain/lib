#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Level, Label
from extronlib.system import Wait

from lib.var.states import sStates, sPressed, sReleased, sHeld, sRepeated, sTapped


class NumberInputSpinner(object):
    def __init__(self,
                 ui_host: UIDevice,
                 inc_btn_id: int,
                 dec_btn_id: int,
                 value_lbl_id: int,
                 min_value: Union[int, float],
                 max_value: Union[int, float],
                 default_value: Union[int, float] = 0,
                 step: Union[int, float] = 1):

        self.ui_host = ui_host
        self.inc_btn = Button(self.ui_host, inc_btn_id, 1, 0.1)
        self.dec_btn = Button(self.ui_host, dec_btn_id, 1, 0.1)
        self.value_lbl = Label(self.ui_host, value_lbl_id)

        self.min_value = min_value
        self.max_value = max_value
        if (default_value > self.max_value):
            self.default_value = self.max_value
        elif (default_value < self.min_value):
            self.default_value = self.min_value
        else:
            self.default_value = default_value
        self.step = step

        self.value = self.default_value

        self.value_lbl.SetText(str(self.default_value))

        @event(self.inc_btn, sStates)
        def btn_inc_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
                self.inc_value()
            elif (state == sTapped):
                @Wait(0.2)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.inc_value()
            elif (state == sReleased):
                btn.SetState(0)

        @event(self.dec_btn, sStates)
        def btn_dec_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
                self.dec_value()
            elif (state == sTapped):
                @Wait(0.2)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.dec_value()
            elif (state == sReleased):
                btn.SetState(0)

    def inc_value(self):
        self.value += self.step
        if (self.value > self.max_value):
            self.value = self.max_value
        self.update_label()

    def dec_value(self):
        self.value -= self.step
        if (self.value < self.min_value):
            self.value = self.min_value
        self.update_label()

    def update_label(self):
        self.value_lbl.SetText(str(self.value))

    def get_value(self):
        return self.value

    def set_value(self, new_value: Union[int, float]):
        if (new_value > self.max_value):
            self.value = self.max_value
        elif (new_value < self.min_value):
            self.value = self.min_value
        else:
            self.value = new_value

class NumberInputSpinnerWCallback(NumberInputSpinner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._callback_functions = list()
    
    def add_callback(self, callback: Callable):
        self._callback_Functions.append(callback)

    def add_callback_function(self, callback_function: Callable[[int | float], None]):
        if callable(callback_function):
            self._callback_functions.append(callback_function)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execute_callback_functions(self, ):
        for cFunc in self._callback_functions:
            cFunc(nIn)
    