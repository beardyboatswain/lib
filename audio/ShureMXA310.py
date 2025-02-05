#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
from math import cos, sin, pi

from extronlib.system import Timer, Wait

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.audio.MicrophoneMeta import MicrophoneWithBeamsMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class ShureMXA310(MicrophoneWithBeamsMeta):
    """
    Control Class for Shure MXA310
    """
    def __init__(self,
                 device: AutoEthernetConnection,
                 xOffset: float = 0.0,
                 yOffset: float = 0.0,
                 micId: int = 0):
        '''
        xOffset, yOffset - offset block beam for VCS codec, using for tracking
        codecChan - input channel of VCS code, using for tracking
        '''
        super().__init__()

        self.device = device
        self.fbFunctions = list()
        self.fbCallbackFunctions = list()
        self.beams = {1: {"a": 0, "e": 0, "rms": None},
                      2: {"a": -90, "e": 0, "rms": None},
                      3: {"a": -180, "e": 0, "rms": None},
                      4: {"a": -270, "e": 0, "rms": None}}
        self.beamsInAutomix = {1: False, 2: False, 3: False, 4: False}

        self.beamXY = [xOffset, yOffset, xOffset, yOffset]
        self.micId = micId
        self.mute = False

        self.rxBuf = str()
        self.meterRateInterval = 200    # Metering in milliseconds

        self.xOffset = xOffset
        self.yOffset = yOffset

        self.pollCmd = "< GET SERIAL_NUM >\r"
        self.audioMuteOnCmd = "< SET x AUDIO_MUTE ON >\r"
        self.audioMuteOffCmd = "< SET x AUDIO_MUTE OFF >\r"

        self.beamMeterSubscribeCmd = "< SET METER_RATE {} >".format(self.meterRateInterval)
        self.beamMeterUnsubscribeCmd = "< SET METER_RATE 0 >"
        self.audioMuteGetCmd = "< GET DEVICE_AUDIO_MUTE >"

        self.audioMutePattern = re.compile("< REP DEVICE_AUDIO_MUTE (ON|OFF) >")
        self.beamMeterPattern = re.compile("< SAMPLE ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) ([0-9]{3}) >")

        self.audioAutomixGate = re.compile("< REP ([0-9]{1}) AUTOMIX_GATE_OUT_EXT_SIG (ON|OFF){1} >")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.pollTimeInterval = 1
        self.refreshFbTimer = Timer(self.pollTimeInterval, self.poll)
        # self.refreshFbTimer.Stop()

    def __del__(self):
        self.unsubscribeOnBeamsMeter()
        self.device.disconnect()

    def poll(self, timer: Timer, count: int):
        self.device.send(self.audioMuteGetCmd)

    def subscribeOnBeamsMeter(self):
        self.device.send(self.beamMeterSubscribeCmd)

    def unsubscribeOnBeamsMeter(self):
        self.device.send(self.beamMeterUnsubscribeCmd)

    def getAudioMute(self):
        self.device.send(self.audioMuteGetCmd)

    def resetStat(self):
        self.beamXY = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]

    def recalcVoiceVector(self):
        mV = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]
        for iB in self.beams:
            if self.beamsInAutomix[iB]:
                # dbg.print("MXA310 RMS: {}".format(self.beams[iB]["rms"]))
                # dbg.print("mic <{}> - beam <{}>: {}".format(self.micId, iB, self.beamsInAutomix[iB]))
                mV[2] = mV[2] + self.beams[iB]["rms"] * cos((pi * self.beams[iB]["a"]) / 180)
                mV[3] = mV[3] + self.beams[iB]["rms"] * sin((pi * self.beams[iB]["a"]) / 180)
        # dbg.print("mic <{}> mV: {}".format(self.micId, mV))
        self.beamXY = [(self.beamXY[0] + mV[0]) / 2,
                       (self.beamXY[1] + mV[1]) / 2,
                       (self.beamXY[2] + mV[2]) / 2,
                       (self.beamXY[3] + mV[3]) / 2]
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
            self.getAudioMute()
            self.subscribeOnBeamsMeter()
            dbg.print("Shure MXA310 Connected!")

    def rxParser(self, rxLine: str):
        # dbg.print("string parse: {}".format(rxLine))
        matchObjectAudioMutePattern = self.beamMeterPattern.search(rxLine)
        if matchObjectAudioMutePattern:
            self.beams[1]["rms"] = int(matchObjectAudioMutePattern.group(1))
            self.beams[2]["rms"] = int(matchObjectAudioMutePattern.group(2))
            self.beams[3]["rms"] = int(matchObjectAudioMutePattern.group(3))
            self.beams[4]["rms"] = int(matchObjectAudioMutePattern.group(4))
            self.recalcVoiceVector()
            return

        matchObjectAudioMutePattern = self.audioMutePattern.search(rxLine)
        if matchObjectAudioMutePattern:
            self.mute = True if matchObjectAudioMutePattern.group(1) == "ON" else False
            dbg.print("MXA310 MUTE: {}".format(self.mute))
            return

        matchObjectAudioAutomixGate = self.audioAutomixGate.search(rxLine)
        if matchObjectAudioAutomixGate:
            beamId = int(matchObjectAudioAutomixGate.group(1))
            beamValue = True if (matchObjectAudioAutomixGate.group(2) == "ON") else False
            self.beamsInAutomix[beamId] = beamValue
            # dbg.print("automix <{}>: {}".format(self.micId, self.beamsInAutomix))
            return

    def rxEventHandler(self, interface, data: str):
        # dbg.print("MXW recieved from [{}]: {}".format(interface, data.decode()))
        self.rxParser(data.decode())
