#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List, Tuple, Dict, Any

import threading
import time

from extronlib.device import UIDevice
from extronlib.interface import Button, Label
from extronlib.system import Clock

from lib.gui.InputFields import NumberInputSpinner as NumIS
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
        
        self.clock = Clock(['{}:{}:00'.format(self.trig_time['hh'], self.trig_time['mm'], ), ], None, trig_callback)
        self.clock.SetDays(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])    

        self.clock.Disable()
        self.is_running = (lambda: False if (self.clock.State == 'Enabled') else True)()

        self.h_input_fields = list()
        self.m_input_fields = list()

    def start(self):
        self.clock.Enable()

    def stop(self):
        self.clock.Disable()

    def set_time(self, trig_time_hh: int, trig_time_mm: int):
        self.trig_time = {'hh': trig_time_hh, 'mm': trig_time_mm}

    def add_widget(self,
                   ui_host: UIDevice,
                   h_inc_btn_id: int,
                   h_dec_btn_id: int,
                   h_lbl_id: int,
                   m_inc_btn_id: int,
                   m_dec_btn_id: int,
                   m_lbl_id: int):
        
        new_h_input_field = NumIS(ui_host, h_inc_btn_id, h_dec_btn_id, h_lbl_id, 0, 23, 1)
        self.h_input_fields.append(new_h_input_field)
        
        new_m_input_field = NumIS(ui_host, m_inc_btn_id, m_dec_btn_id, m_lbl_id, 0, 59, 1)
        self.m_input_fields.append(new_m_input_field)
        

shutdownProjectorsScheduler = Clock(['22:00:00'], None, schedulerRun)
shutdownProjectorsScheduler.SetDays(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
shutdownProjectorsScheduler.Enable()
if (shutdownProjectorsScheduler.State == 'Enabled'):
    btnScheduler.SetState(1)
else:
    btnScheduler.SetState(0)


def toggleScheduler():
    if (shutdownProjectorsScheduler.State == 'Enabled'):
        shutdownProjectorsScheduler.Disable()
    else:
        shutdownProjectorsScheduler.Enable()
    if (shutdownProjectorsScheduler.State == 'Enabled'):
        btnScheduler.SetState(1)
    else:
        btnScheduler.SetState(0)
    


@event(btnScheduler, sStates)
def btnSchedulerEventHandler(btn, state):
    if (state == sPressed):
        if (btn.State == 0):
            btn.SetState(2)
        elif (btn.State == 1):
            btn.SetState(3)
    elif (state == sReleased):
        if (btn.State == 2):
            btn.SetState(0)
        elif (btn.State == 3):
            btn.SetState(1)
        toggleScheduler()

shutdownProjectorsScheduler.Enable()
if (shutdownProjectorsScheduler.State == 'Enabled'):
    btnScheduler.SetState(1)
else:
    btnScheduler.SetState(0)
dbg.print("Scheduler is {}". format(shutdownProjectorsScheduler.State))

def Initialize():
    dbg.print('Imported')

Initialize()
