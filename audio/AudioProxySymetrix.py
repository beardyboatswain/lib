#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re

from extronlib.system import Timer

import lib.drv.gs.gs_syme_dsp_Radius_NX_Series_v1_0_2_0 as symetrixRadius

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import AudioProxySymetrix_dbg
dbg = debugger(AudioProxySymetrix_dbg, __name__)


class AudioProxySymetrix():
    tagLevel = "LevelControl"
    tagMute = "MuteControl"
    tagCrosspoint = "CrosspointState"
    tagSPM = "SignalPresentMeter"
    tagLogicMeter = "LogicMeter"

    def __init__(self, dev: AutoEthernetConnection):
        self.dev = dev

        self.controls = dict()

        self.matchFb = re.compile("#{0,1}([0-9]{3,}) {0,1}={0,1}([0-9]{1,})")

        self.dev.subscribe('Connected', self.connectEventHandler)
        self.dev.subscribe('Disconnected', self.connectEventHandler)
        self.dev.subscribe('ReceiveData', self.rxEventHandler)
        self.dev.connect()

        self.__upateTimer = Timer(30, self.upateTimerHandler)

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connect'):
            # todo -------------------------------------------------
            # todo self.requestTie()
            dbg.print("Symetrix Connected!")
        elif (state == 'Disconnected'):
            dbg.print("Symetrix Connected!")

    def upateTimerHandler(self, timer: Timer, count: int):
        self.updateControl()

    def addLevel(self, levelRcId: int, muteRcId: int, callbackMethod: Callable[[int, int], None]):
        self.controls[levelRcId] = {"tag": levelRcId, "callback": callbackMethod}
        self.controls[muteRcId] = {"tag": muteRcId, "callback": callbackMethod}
        self.updateControl(levelRcId)
        self.updateControl(muteRcId)

    def addMute(self, muteRcId: int, callbackMethod: Callable[[str, str], None]):
        self.controls[muteRcId] = {"tag": muteRcId, "callback": callbackMethod}
        self.updateControl(muteRcId)

    def updateControl(self, rcId: int = None) -> None:
        if rcId:
            self.getControl(rcId)
        else:
            for iRcId in self.controls:
                self.getControl(iRcId)

    def getControl(self, rcId: int) -> None:
        self.dev.send("GS2 {}\x0d\x0a".format(rcId))

    def setControl(self, rcId: int, value: int) -> None:
        self.dev.send("CS {} {}\x0d\x0a".format(rcId, value))
        self.updateControl(rcId)

    def setLevel(self, levelRcId: int, value: int):
        self.setControl(levelRcId, value)

    def setMute(self, muteRcId: int, value: int):
        self.setControl(muteRcId, value)

    def addCposspoint(self, cpRcId: int, callbackMethod: Callable[[int, int], None]):
        self.controls[cpRcId] = {"tag": cpRcId, "callback": callbackMethod}
        self.updateControl(cpRcId)

    def setCrosspoint(self, instanceTag: str, points: tuple, value: str):
        # todo
        pass

    def crosspointFbHandler(self, command, value, qualifier):
        # todo
        pass

    def addSignalPresentMeter(self, instanceTag: str, channel: int, name: str, callbackMethod: Callable[[str], None]):
        # todo
        pass

    def signalPresentMeterFbHandler(self, command, value, qualifier):
        # todo
        pass

    def addSignalProbe(self, rcId: int, callbackMethod: Callable[[int, int], None]):
        self.controls[rcId] = {"tag": rcId, "callback": callbackMethod}
        self.updateControl(rcId)

    def logicMeterFbHandler(self, command, value, qualifier):
        # todo
        pass

    def presetCall(self, presetId: int):
        self.dev.send("LP{}\x0d\x0a".format(presetId))

    def presetSave(self, presetId: int):
        # No command in API, rtfm
        pass

    def updateFb(self, rcId: int, value: int) -> None:
        if rcId in self.controls.keys():
            self.controls[rcId]["callback"](rcId, value)

    def rxParser(self, rxLine: str):
        dataLines = rxLine
        dbg.print("rxParser recieved: {} ".format(dataLines))

        for rxLine in dataLines.splitlines():
            dbg.print("PARSE LINE: {}".format(rxLine))
            matchObjectFb = self.matchFb.search(rxLine)
            if matchObjectFb:
                dbg.print("FOUND: {}".format(matchObjectFb))
                rcId = int(matchObjectFb.group(1))
                rcValue = int(matchObjectFb.group(2))
                self.updateFb(rcId, rcValue)

    def rxEventHandler(self, interface, data):
        dbg.print("From symetrix recieved: {} ".format(data.decode()))
        self.rxParser(data.decode())
