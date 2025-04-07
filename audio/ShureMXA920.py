#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List
import re

from extronlib import event
from extronlib.system import Timer, Wait
from extronlib.device import UIDevice
from extronlib.ui import Button

from lib.var.states import sPressed, sReleased, sHeld, sTapped, sRepeated, sStates

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.audio.MicrophoneMeta import MicrophoneWithBeamsMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class ShureMXA920(MicrophoneWithBeamsMeta):
    """
    Control Class for Shure MXA310
    """
    def __init__(self,
                 device: AutoEthernetConnection,
                 micId: int = 0):
        '''
        xOffset, yOffset - offset block beam for VCS codec, using for tracking
        codecChan - input channel of VCS code, using for tracking
        '''
        super().__init__()

        self.device = device
        self.fbFunctions = list()
        self.fbCallbackFunctions = list()

        self.micId = micId
        self.mute = False

        self.rxBuf = str()

        self.mute_btns: List[Button] = list()

        self.pollCmd = "< GET SERIAL_NUM >\r"
        self.audioMuteOnCmd = "< SET DEVICE_AUDIO_MUTE ON >\r"
        self.audioMuteOffCmd = "< SET DEVICE_AUDIO_MUTE OFF >\r"

        self.audioMuteGetCmd = "< GET DEVICE_AUDIO_MUTE >"

        self.audioMutePattern = re.compile("< REP DEVICE_AUDIO_MUTE (ON|OFF) >")

        self.device.subscribe('Connected', self.connectEventHandler)
        self.device.subscribe('Disconnected', self.connectEventHandler)
        self.device.subscribe('ReceiveData', self.rxEventHandler)
        self.device.connect()

        self.pollTimeInterval = 10
        self.refreshFbTimer = Timer(self.pollTimeInterval, self.poll)
        self.refreshFbTimer.Stop()

    def __del__(self):
        self.device.disconnect()

    def add_mute_btn(self, ui_host: UIDevice, btn_id: int):
        self.mute_btns.append(Button(ui_host, btn_id))

        @event(self.mute_btns, sStates)
        def mute_btns_event_handler(btn: Button, state: str):
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
                self.set_mute()

    def show_fb_mute_btns(self):
        for btn in self.mute_btns:
            btn.SetState(2 if self.mute else 0)

    def poll(self, timer: Timer, count: int):
        self.device.send(self.audioMuteGetCmd)

    def getAudioMute(self):
        self.device.send(self.audioMuteGetCmd)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[list, list, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self):
        pass

    def set_mute(self, mute: str = None):
        if mute:
            if (mute == 'ON'):
                self.device.send(self.audioMuteOnCmd)
            elif (mute == 'OFF'):
                self.device.send(self.audioMuteOffCmd)
        else:
            if self.mute:
                self.device.send(self.audioMuteOffCmd)
            else:
                self.device.send(self.audioMuteOnCmd)
        self.getAudioMute()

    def connectEventHandler(self, interface, state):
        dbg.print("Connection Handler: {} {}".format(interface, state))
        if (state == 'Connected'):
            self.poll(0, 0)
            self.refreshFbTimer.Restart()
            self.getAudioMute()
            dbg.print("Shure MXA920 Connected!")

    def rxParser(self, rxLine: str):
        matchObjectAudioMutePattern = self.audioMutePattern.search(rxLine)
        if matchObjectAudioMutePattern:
            self.mute = True if matchObjectAudioMutePattern.group(1) == "ON" else False
            self.show_fb_mute_btns()
            dbg.print("MXA920 MUTE: {}".format(self.mute))

            return

    def rxEventHandler(self, interface, data: str):
        # dbg.print("MXW received from [{}]: {}".format(interface, data.decode()))
        self.rxParser(data.decode())
