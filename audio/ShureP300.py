#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
from math import cos, sin, pi

from extronlib.system import Timer, Wait

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.audio.MicrophoneMeta import MicrophoneWithBeamsMeta

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import ShureP300_dbg
dbg = debugger(ShureP300_dbg, __name__)


class ShureP300(MicrophoneWithBeamsMeta):
    """
    Control Class for Shure MXA310
    """
    def __init__(self,
                 device: AutoEthernetConnection,
                 xOffset: float = 0.0,
                 yOffset: float = 0.0,
                 codecChan: int = 1,
                 micId: int = 0):
        '''
        xOffset, yOffset - offset block beam for VCS codec, using for tracking
        codecChan - input channel of VCS code, using for tracking
        '''
        super().__init__()

        self.device = device
        self.codecChan = codecChan
        self.noiceOffset = -18
        self.fbFunctions = list()
        self.fbCallbackFunctions = list()
        self.beam = {"a": 0, "e": 0, "rms": None}
        # self.beamsInAutomix = {1: False, 2: False, 3: False, 4: False}
        self.beamXY = [xOffset, yOffset, xOffset, yOffset]
        self.micId = micId
        self.mute = False
        self.automix_mute = False

        self.rxBuf = str()
        self.meterRateInterval = 300    # Metering in milliseconds

        self.xOffset = xOffset
        self.yOffset = yOffset

        self.devideFactor = 2

        self.pollCmd = "< GET SERIAL_NUM >"

        self.beamMeterSubscribeCmd = "< SET METER_RATE_IN {} >".format(self.meterRateInterval)
        self.beamMeterUnsubscribeCmd = "< SET METER_RATE 0 >"

        self.audioDeviceMutePattern = re.compile("< REP DEVICE_AUDIO_MUTE (ON|OFF) >")
        self.audioAutomixMutePattern = re.compile("< REP 21 AUTOMXR_MUTE (ON|OFF) >")
        self.beamMeterPattern = re.compile("< SAMPLE_IN ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) " +
                                           "([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) " +
                                           "([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) >")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.pollTimeInterval = 30
        self.refreshFbTimer = Timer(self.pollTimeInterval, self.poll)
        # self.refreshFbTimer.Stop()

    def __del__(self):
        self.unsubscribeOnBeamsMeter()
        self.device.disconnect()

    def poll(self, timer: Timer, count: int):
        self.device.send(self.pollCmd)

    def subscribeOnBeamsMeter(self):
        self.device.send(self.beamMeterSubscribeCmd)
        dbg.print("P300 beam subscripted")

    def unsubscribeOnBeamsMeter(self):
        self.device.send(self.beamMeterUnsubscribeCmd)

    def resetStat(self):
        self.beamXY = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]
        # pass

    def recalcVoiceVector(self):
        mV = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]
        mV[2] = mV[2] + self.beam["rms"] * cos((pi * self.beam["a"]) / 180)
        mV[3] = mV[3] + self.beam["rms"] * sin((pi * self.beam["a"]) / 180)
        self.beamXY = [(self.beamXY[0] + mV[0]) / self.devideFactor,
                       (self.beamXY[1] + mV[1]) / self.devideFactor,
                       (self.beamXY[2] + mV[2]) / self.devideFactor,
                       (self.beamXY[3] + mV[3]) / self.devideFactor]
        # dbg.print("P300 Main Beam: {}".format(self.beamXY))
        self.executeCallbackFunctions()

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[list, list, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self):
        for func in self.fbCallbackFunctions:
            func(self.beamXY, (self.xOffset, self.yOffset), self.micId)

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.poll(0, 0)
            self.refreshFbTimer.Restart()
            self.subscribeOnBeamsMeter()
            dbg.print("Shure P300 Connected!")

    def rxParser(self, rxLine: str):
        # dbg.print("string parse: {}".format(rxLine))
        matchObjectbeamMeterPattern = self.beamMeterPattern.search(rxLine)
        if matchObjectbeamMeterPattern:
            self.beam["rms"] = int(matchObjectbeamMeterPattern.group(self.codecChan)) + self.noiceOffset
            # self.beam["rms"] = (-1) * self.beam["rms"] + 60
            # dbg.print("P300 RMS: {}".format(self.beam["rms"]))
            self.recalcVoiceVector()
            return

        matchObjectAutomixMutePattern = self.audioAutomixMutePattern.search(rxLine)
        if matchObjectAutomixMutePattern:
            self.automix_mute = True if matchObjectAutomixMutePattern.group(1) == "ON" else False
            dbg.print("P300 Automix MUTE: {}".format(self.automix_mute))
            return

        matchObjectDeviceMutePattern = self.audioDeviceMutePattern.search(rxLine)
        if matchObjectDeviceMutePattern:
            self.mute = True if matchObjectDeviceMutePattern.group(1) == "ON" else False
            dbg.print("P300 Device MUTE: {}".format(self.mute))
            return

        # matchObjectAudioAutomixGate = self.audioAutomixGate.search(rxLine)
        # if matchObjectAudioAutomixGate:
        #     beamId = int(matchObjectAudioAutomixGate.group(1))
        #     beamValue = True if (matchObjectAudioAutomixGate.group(2) == "ON") else False
        #     self.beamsInAutomix[beamId] = beamValue
        #     # dbg.print("automix <{}>: {}".format(self.micId, self.beamsInAutomix))
        #     return

    def rxEventHandler(self, interface, data: str):
        # dbg.print("P300 recieved from [{}]: {}".format(interface, data.decode()))
        self.rxParser(data.decode())
