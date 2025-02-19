#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List, Tuple, Dict, Any

import threading
import time

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label
from extronlib.system import Clock

from lib.gui.InputFields import NumberInputSpinnerWCallback as NumISWC
from lib.var.states import sPressed, sReleased, sHeld, sTapped, sStates

from lib.utils.debugger import debuggerNet as debugger
Schedulers_dbg = 'time'
dbg = debugger(Schedulers_dbg, __name__)


class SchedulerClock(object):
    def __init__(self, trig_time_hh: int, trig_time_mm: int, trig_callback: Callable[[], None]):
        '''
        trig_time: str - time in 'HH:MM' format
        trig_callback: Callable[[], None]
        '''
        self.trig_time = {'hh': trig_time_hh, 'mm': trig_time_mm}
        self.trig_callback = trig_callback
        
        self.clock = Clock(['{}:{}:00'.format(self.trig_time['hh'], self.trig_time['mm'], ), ], None, self.trig_clock)
        self.clock.SetDays(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])    

        self.clock.Disable()
        self.is_running = False

        self.hh_input_fields = list()
        self.mm_input_fields = list()
        self.state_btns = list()

    def start(self):
        self.clock.Enable()
        self.is_running = True if (self.clock.State == 'Enabled') else False
        self.update_state_btn()

    def stop(self):
        self.clock.Disable()
        self.is_running = True if (self.clock.State == 'Enabled') else False
        self.update_state_btn()

    def tgl_state(self):
        dbg.print('Toggling state. Current state: {}'.format(self.is_running))
        if self.is_running:
            self.stop()
        else:
            self.start()

    def trig_clock(self, clock, dt):
        dbg.print('Triggered, clock({})={} dt({})={}'.format(type(clock), clock, type(dt), dt))
        self.trig_callback()

    def set_time(self, trig_time_hh: int = None, trig_time_mm: int = None):
        new_hh = trig_time_hh if trig_time_hh else self.trig_time['hh']
        new_mm = trig_time_mm if trig_time_mm else self.trig_time['mm']
        self.trig_time = {'hh': new_hh, 'mm': new_mm}
        self.clock.SetTimes(['{}:{}:00'.format(self.trig_time['hh'], self.trig_time['mm']), ])
        dbg.print('Times set to {}'.format(self.clock.Times))

    def add_widget(self,
                   ui_host: UIDevice,
                   hh_inc_btn_id: int,
                   hh_dec_btn_id: int,
                   hh_lbl_id: int,
                   mm_inc_btn_id: int,
                   mm_dec_btn_id: int,
                   mm_lbl_id: int,
                   state_btn_id: int):
        
        new_hh_input_field = NumISWC(ui_host, hh_inc_btn_id, hh_dec_btn_id, hh_lbl_id, 0, 23, self.trig_time['hh'], 1)
        new_hh_input_field.add_callback(self._hh_time_changed)
        new_hh_input_field.set_digits_number(2)
        self.hh_input_fields.append(new_hh_input_field)
        
        new_mm_input_field = NumISWC(ui_host, mm_inc_btn_id, mm_dec_btn_id, mm_lbl_id, 0, 59, self.trig_time['mm'], 1)
        new_mm_input_field.add_callback(self._mm_time_changed)
        new_mm_input_field.set_digits_number(2)
        self.mm_input_fields.append(new_mm_input_field)

        self.add_state_btn(ui_host, state_btn_id)
        
    def add_state_btn(self, ui_host: UIDevice, state_btn_id: int):
        new_state_btn = Button(ui_host, state_btn_id)
        self.state_btns.append(new_state_btn)

        @event(self.state_btns, sStates)
        def _state_btns_event_handler(btn: Button, state: str):
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
                self.tgl_state()

    def _hh_time_changed(self, value: Union[int, float]):
        self.set_time(trig_time_hh=int(value))
        
    def _mm_time_changed(self, value: Union[int, float]):
        self.set_time(trig_time_mm=int(value))

    def update_state_btn(self):
        if len(self.state_btns) > 0:
            dbg.print('Current state btn state: {}'.format(self.is_running))
            dbg.print('Updating state btn state to {}'.format(2 if self.is_running else 0))
            _ = [btn.SetState(2 if self.is_running else 0) for btn in self.state_btns]
            # for btn in self.state_btns:
            #     btn.SetState(2 if self.is_running else 0)
