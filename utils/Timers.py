#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union, List, Tuple, Dict, Any

import threading
import time

from extronlib.system import Timer

from lib.utils.debugger import debuggerNet as debugger
Timers_dbg = 'time'
dbg = debugger(Timers_dbg, __name__)


class MultiTimer(object):
    tStoped = 0
    tRunning = 1
    tPaused = 2

    """Класс для запуска нескольких таймеров одного за другим"""
    def __init__(self):
        self.intervals: List[Tuple[Union[int, float], Callable]] = []
        self.timers: List[Timer] = []
        self.state = self.tStoped
        self.runnig_timer: Timer = None
        self.running_timer_id = None

    def start(self):
        if (len(self.timers) > 0):
            self.running_timer_id = 0
            self.runnig_timer = self.timers[self.running_timer_id]
            self.runnig_timer.Restart()
            self.state = self.tRunning

    def pause(self):
        if (self.runnig_timer):
            self.state = self.tPaused
            self.runnig_timer.Pause()

    def stop(self):
        if (self.runnig_timer):
            self.state = self.tStoped
            self.runnig_timer.Stop()

    def resume(self):
        if (self.runnig_timer):
            self.state = self.tRunning
            self.runnig_timer.Resume()

    def restart(self):
        self.start()

    def get_state(self) -> int:
        return self.state

    def add_timer(self,
                  interval: Union[int, float],
                  callback: Callable[[List[Any]], None],
                  *args) -> None:
        """Добавляет новый таймер с заданным интервалом и функцией обратного вызова"""
        self.intervals.append((interval, callback, args))

        new_timer = Timer(interval, self.timer_triggered)
        new_timer.Stop()
        self.timers.append(new_timer)

    def remove_timers(self) -> None:
        """Удаляет все таймеры"""
        self.intervals.clear()
        for timer in self.timers:
            timer.Stop()
        self.timers.clear()

    def timer_triggered(self, timer: Timer, count: int) -> None:
        """Вызывается при срабатывании таймера"""
        self.runnig_timer.Stop()
        dbg.print("Timer triggered: id={} interval={}".format(self.running_timer_id,
                                                              self.intervals[self.running_timer_id][0]))
        # callback
        self.intervals[self.running_timer_id][1](*self.intervals[self.running_timer_id][2])
        self.running_timer_id += 1
        try:
            self.intervals[self.running_timer_id]
        except IndexError:
            self.running_timer_id = 0
        finally:
            self.runnig_timer = self.timers[self.running_timer_id]
            self.runnig_timer.Restart()
