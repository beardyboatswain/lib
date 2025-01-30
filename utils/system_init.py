#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from extronlib import Version, Platform

import lib.utils.signals as signals

from lib.utils.debugger import debuggerNet as debugger


def InitMain(modName: str = ''):
    dbgMain = debugger("time", module=modName)
    startTimeHMS = time.strftime("%H:%M:%S")
    startTimeMS = int(round(time.time(), 3) % 1 * pow(10, 3))
    prec = str(3)
    dbgMain.print('System Start at {}.{:0{}}'.format(startTimeHMS, startTimeMS, prec))
    dbgMain.print('System SW: {}'.format(Version()))
    dbgMain.print('ControlScript: {}\n'.format(Platform()))
    signals.emit('*', signal='SYS', params={'system': 'started'})


def InitModule(modName: str = ''):
    dbgModule = debugger("time", module=modName)
    dbgModule.print("<{}> imported!".format(modName))
