#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib.system import Timer

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.video.VideoControlProxyMeta import SwitcherControlProxyMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class SwitcherAtenUC3430(SwitcherControlProxyMeta):
    """
    Control Class fro Switcher Aten UC3430
    """
    def __init__(self,
                 dev: AutoEthernetConnection,
                 in_size: int):
        super().__init__()

        self.dev = dev
        self.current_in = 0

        self.in_size = in_size

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', self.rx_event_handler)
        self.dev.connect()

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
            i_func(self.current_in)

    def poll(self, timer: Timer, count: int) -> None:
        cmd = "read\x0d"
        self.dev.send(cmd)

    def set_tie(self, n_in: int, n_out: int = 1) -> None:
        if (0 <= (n_in - 1) <= (self.in_size - 1)):
            cmd = 'scene s{:02}\x0d'.format(n_in - 1)
            self.current_in = n_in
            self.dev.send(cmd)
            self.execute_callback_functions()

    def get_tie(self) -> int:
        return self.current_in

    def connect_event_handler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.dev.send("\x0d")
            dbg.print("Aten UC3430 Connected!")
            self.refresh_fb_timer.Restart()
        elif (state == 'Connected'):
            self.dev.send("\x0d")
            dbg.print("Aten UC3430 Connected!")

    def rx_parser(self, rx_lines: str):
        data_lines = rx_lines

        for rx_line in data_lines.splitlines():
            dbg.print("Aten: {}".format(rx_line))

    def rx_event_handler(self, interface, data):
        self.rx_parser(data.decode())
