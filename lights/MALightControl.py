#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib.interface import EthernetClientInterface

from lib.utils.debugger import debugger
dbg = debugger('time', __name__)


class MALightControl(object):
    def __init__(self, dev: EthernetClientInterface):
        self.dev = dev

    def set_value(self, fader_number: int, value: int):
        cmd = '/gma3/Page2/Fader{}\x00\x00\x00\x00,ii\x00\x00\x00\x00{}\x00\x00\x00\x01'.format(str(fader_number), chr(value))
        # cmd = '\x2f\x67\x6d\x61\x33\x2f\x50\x61\x67\x65\x32\x2f\x46\x61\x64\x65\x72{}\x00\x00\x00\x00\x2c\x69\x69\x00\x00\x00\x00{}\x00\x00\x00\x01 '
        self.dev.Send(cmd.encode())
        dbg.print(cmd)

# /gma3/Page2/Fader203\00\00\00\00,ii\00\00\00\00\00\00\00\00\01
# /gma3/Page2/Fader203\00\00\00\00,ii\00\00\00\00\ff\00\00\00\01
