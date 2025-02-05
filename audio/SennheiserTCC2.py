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


class SennheiserTCC2(MicrophoneWithBeamsMeta):
    """
    Control Class for Sennheiser TeamConnect Ceiling 2
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
        self.beam = {"a": 0, "e": 0, "rms": 0}
        self.beamXY = [xOffset, yOffset, xOffset, yOffset]
        self.micId = micId
        self.mute = False

        self.xOffset = xOffset
        self.yOffset = yOffset

        self.pollCmd = '{"device":{"identity":{"version":null}}}\r'
        self.beamSubscribeStartCmd = ('{"osc":{"state":{"subscribe":[{'
                                      '"#":{"cancel":false},'
                                      '"m":{"beam":{"azimuth":null}},'
                                      '"m":{"beam":{"elevation":null}},'
                                      '"m":{"in1":{"peak":null}}}]}}}\r')
        self.beamSubscribeStopCmd = ('{"osc":{"state":{"subscribe":[{'
                                     '"#":{"cancel":true},'
                                     '"m":{"beam":{"azimuth":null}},'
                                     '"m":{"beam":{"elevation":null}},'
                                     '"m":{"in1":{"peak":null}}}]}}}\r')
        self.audioMuteSubscribeCmd = '{"osc":{"state":{"subscribe":[ {"audio":{"mute":null}}]}}}\r'

        self.azimuthMatchPattern = re.compile('{"m":{"beam":{"azimuth":(\d+)}}}')
        self.elevationMatchPattern = re.compile('{"m":{"beam":{"elevation":(\d+)}}}')
        self.peakMatchPattern = re.compile('{"m":{"in1":{"peak":(-*\d+)}}}')
        self.audioMutePattern = re.compile('{"audio":{"mute":(true|false)}}')

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.pollTimeInterval = 10
        self.refreshFbTimer = Timer(self.pollTimeInterval, self.poll)
        self.refreshFbTimer.Stop()

    def __del__(self):
        self.unsubscribeOnBeam()
        self.device.disconnect()

    def poll(self, timer: Timer, count: int):
        self.device.send(self.pollCmd)
        self.subscribeOnBeam()

    def subscribeOnBeam(self):
        self.device.send(self.beamSubscribeStartCmd)

    def unsubscribeOnBeam(self):
        self.device.send(self.beamSubscribeStopCmd)

    def subscribeOnMute(self):
        self.device.send(self.audioMuteSubscribeCmd)

    def resetStat(self):
        self.beamXY = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]

    def recalcVoiceVector(self):
        mV = [self.xOffset, self.yOffset, self.xOffset, self.yOffset]
        mV = [mV[0],
              mV[1],
              mV[2] + self.beam["rms"] * cos((pi * self.beam["a"]) / 180),
              mV[3] + self.beam["rms"] * sin((pi * self.beam["a"]) / 180)]
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
            self.subscribeOnBeam()
            self.subscribeOnMute()
            dbg.print("Sennheiser TCC2 Connected!")

    def rxParser(self, rxLines: str):
        dataLines = rxLines
        # dbg.print(dataLines)

        for rxLine in dataLines.splitlines():
            matchObjectAzimuthMatchPattern = self.azimuthMatchPattern.search(rxLine)
            if matchObjectAzimuthMatchPattern:
                # (-1) - recalc CW to nornal coordinate grid (CCW)
                self.beam["a"] = 360 - int(matchObjectAzimuthMatchPattern.group(1))
                print("Azimuth: {}".format(self.beam["a"]))
                self.recalcVoiceVector()
                continue

            matchObjectElevationMatchPattern = self.elevationMatchPattern.search(rxLine)
            if matchObjectElevationMatchPattern:
                self.beam["e"] = int(matchObjectElevationMatchPattern.group(1))
                print("Elevation: {}".format(self.beam["e"]))
                self.recalcVoiceVector()
                continue

            matchObjectPeakMatchPattern = self.peakMatchPattern.search(rxLine)
            if matchObjectPeakMatchPattern:
                rms = int(matchObjectPeakMatchPattern.group(1))
                # sennheiser gets from -90 to 0
                self.beam["rms"] = (rms + 90) * cos((pi * self.beam["e"]) / 180) / 6
                print("Rms: {}".format(self.beam["rms"]))
                self.recalcVoiceVector()
                continue

            matchObjectAudioMutePattern = self.audioMutePattern.search(rxLine)
            if matchObjectAudioMutePattern:
                self.mute = True if matchObjectAudioMutePattern.group(1) == "true" else False
                self.executeCallbackFunctions()
                continue

    def rxEventHandler(self, interface, data):
        self.rxParser(data.decode())
