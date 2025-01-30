#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib import event
from extronlib.ui import Button, Label
from extronlib.device import UIDevice


class cMicControl(object):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

        self.presetID = None
        self.presetType = None

        self.btnTrackOnOff = None
        self.btnTrackPreset = None
        self.btnTrackZone = None
        self.lblTrackMode = None

    def setMwchanics(self,
                     UIHost: UIDevice,
                     btnTrackOnOffID: int,
                     btnTrackPresetID: int,
                     btnTrackZoneID: int,
                     lblTrackModeID: int):
        self.btnTrackOnOff = Button(UIHost, btnTrackOnOffID)
        self.btnTrackPreset = Button(UIHost, btnTrackPresetID)
        self.btnTrackZone = Button(UIHost, btnTrackZoneID)
        self.lblTrackMode = Label(UIHost, lblTrackModeID)

        @event(None, 'EventName')
        def HandlerFunction(actor, eventname):
            pass
        

# todo ALLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL
