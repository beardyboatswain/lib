#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable

from extronlib.system import Timer

import lib.helpers.ConnectionHandler as ConnectionHandler
import lib.drv.gs.gs_biam_dsp_TesiraSeries_v1_15_1_0 as biampTesiraServerIO

from lib.utils.system_init import InitModule
import lib.utils.signals as signals


from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import AudioProxy_dbg
dbg = debugger(AudioProxy_dbg, __name__)


class AudioProxyBiampTesira():
    tagLevel = "LevelControl"
    tagMute = "MuteControl"
    tagCrosspoint = "CrosspointState"
    tagSPM = "SignalPresentMeter"
    tagLogicMeter = "LogicMeter"

    def __init__(self, dev: biampTesiraServerIO.SSHClass):
        self.__dev = dev

        self.levels = dict()
        self.mutes = dict()
        self.crosspoints = dict()
        self.signalpresents = dict()
        self.logicmeters = dict()

        self.__dev.SubscribeStatus('LevelControl', None, self.faderLevelFbHandler)
        self.__dev.SubscribeStatus('MuteControl', None, self.faderLevelFbHandler)
        self.__dev.SubscribeStatus('CrosspointState', None, self.crosspointFbHandler)
        self.__dev.SubscribeStatus('SignalPresentMeter', None, self.signalPresentMeterFbHandler)
        self.__dev.SubscribeStatus('LogicMeter', None, self.logicMeterFbHandler)
        self.__dev.SubscribeStatus('ConnectionStatus', None, self.connectionStatusFbHandler)

        self.__dev.Connect()

        self.__upateTimer = Timer(30, self.upateTimerHandler)

    def uid(self, tag: str, point: tuple):
        return str(tag) + "-" + str(point[0]) + "-" + str(point[1])

    def connectionStatusFbHandler(self, command, value, qualifier):
        dbg.print("Biamp [{}]".format(value))

    def upateTimerHandler(self, timer: Timer, count: int):
        for i in self.crosspoints:
            self.__dev.UpdateCrosspointState(self.tagCrosspoint, {"Instance Tag": self.crosspoints.get(i).get("tag"),
                                                                  "Input": self.crosspoints.get(i).get("point")[0],
                                                                  "Output": self.crosspoints.get(i).get("point")[1]})
        # for i in self.levels:
        #     self.__dev.Send("")
        #     self.__dev.UpdateLevelControl(self.tagLevel, {"Instance Tag": self.levels[i].get("tag"),
        #                                                   "Channel": self.levels[i].get("channel")})
        #     self.__dev.UpdateMuteControl(self.tagLevel, {"Instance Tag": self.levels[i].get("tag"),
        #                                                  "Channel": self.levels[i].get("channel")})

    def addLevel(self, instanceTag: str, channel: int, callbackMethod: Callable[[str, str], None]):
        self.levels[instanceTag + str(channel)] = {"tag": instanceTag, "channel": channel, "callback": callbackMethod}
        self.__dev.Update("LevelControl", {"Instance Tag": instanceTag, "Channel": channel})
        self.__dev.Update("MuteControl",  {"Instance Tag": instanceTag, "Channel": channel})

    def addMute(self, instanceTag: str, channel: int, callbackMethod: Callable[[str, str], None]):
        self.mutes[instanceTag + str(channel)] = {"tag": instanceTag, "channel": channel, "callback": callbackMethod}
        self.__dev.Update("MuteControl",  {"Instance Tag": instanceTag, "Channel": channel})

    def setLevel(self, instanceTag: str, channel: int, value: int):
        self.__dev.Set(self.tagLevel, value, {"Instance Tag": instanceTag, "Channel": channel})
        self.__dev.Update(self.tagLevel, {"Instance Tag": instanceTag, "Channel": channel})

    def setMute(self, instanceTag: str, channel: int, value: str):
        self.__dev.Set(self.tagMute, value, {"Instance Tag": instanceTag, "Channel": channel})
        self.__dev.Update(self.tagMute, {"Instance Tag": instanceTag, "Channel": channel})

    def faderLevelFbHandler(self, command, value, qualifier):
        if (command == self.tagLevel) and (self.levels.get(qualifier["Instance Tag"] + qualifier["Channel"])):
            self.levels.get(qualifier["Instance Tag"] + qualifier["Channel"]).get("callback")(self.tagLevel, value)
        elif (command == self.tagMute) and (self.levels.get(qualifier["Instance Tag"] + qualifier["Channel"])):
            self.levels.get(qualifier["Instance Tag"] + qualifier["Channel"]).get("callback")(self.tagMute, value)
        elif (command == self.tagMute) and (self.mutes.get(qualifier["Instance Tag"] + qualifier["Channel"])):
            self.mutes.get(qualifier["Instance Tag"] + qualifier["Channel"]).get("callback")(self.tagMute, value)

    def addCposspoint(self, instanceTag: str, points: tuple, callbackMethod: Callable[[tuple, bool], None]):
        for p in points:
            self.crosspoints[self.uid(instanceTag, p)] = {"tag": instanceTag, "point": p, "callback": callbackMethod}
            self.__dev.UpdateCrosspointState(self.tagCrosspoint, {"Instance Tag": instanceTag, "Input": p[0], "Output": p[1]})

    def setCrosspoint(self, instanceTag: str, points: tuple, value: str):
        for p in points:
            self.__dev.Set(self.tagCrosspoint, value, {"Instance Tag": instanceTag,
                                                       "Input": p[0],
                                                       "Output": p[1]})
            self.__dev.UpdateCrosspointState(self.tagCrosspoint, {"Instance Tag": instanceTag, "Input": p[0], "Output": p[1]})

    def crosspointFbHandler(self, command, value, qualifier):
        if (command == self.tagCrosspoint) and self.crosspoints.get(self.uid(qualifier["Instance Tag"],
                                                                             (qualifier["Input"], qualifier["Output"]))):
            self.crosspoints.get(self.uid(qualifier["Instance Tag"],
                                          (qualifier["Input"], qualifier["Output"]))).get("callback")((int(qualifier["Input"]),
                                                                                                       int(qualifier["Output"])), value)

    def addSignalPresentMeter(self, instanceTag: str, channel: int, name: str, callbackMethod: Callable[[str], None]):
        self.signalpresents[instanceTag + str(channel)] = {"tag": instanceTag,
                                                           "channel": channel,
                                                           "name": name,
                                                           "callback": callbackMethod}
        self.__dev.Update(self.tagSPM, {"Instance Tag": instanceTag, "Channel": channel, "Meter Name": name})

    def signalPresentMeterFbHandler(self, command, value, qualifier):
        if (command == self.tagSPM) and self.signalpresents.get(qualifier["Instance Tag"] + qualifier["Channel"]):
            self.signalpresents.get(qualifier["Instance Tag"] + qualifier["Channel"]).get("callback")(value)

    def addLogicMeter(self, instanceTag: str, channel: int, callbackMethod: Callable[[str], None]):
        self.logicmeters[instanceTag + str(channel)] = {"tag": instanceTag,
                                                        "channel": channel,
                                                        "callback": callbackMethod}
        self.__dev.Update(self.tagLogicMeter, {"Instance Tag": instanceTag, "Channel": channel, })

    def logicMeterFbHandler(self, command, value, qualifier):
        if (command == self.tagLogicMeter) and self.logicmeters.get(qualifier["Instance Tag"] + qualifier["Channel"]):
            dbg.print("LOGICMETER FB: cmd<{}> - val<{}> - qualifier<{}>".format(command, value, qualifier))
            self.logicmeters.get(qualifier["Instance Tag"] + qualifier["Channel"]).get("callback")(value)

    def presetCall(self, presetId: int):
        self.__dev.Set("PresetRecall", str(presetId))

    def presetSave(self, presetId: int):
        self.__dev.Set("PresetSave", str(presetId))


InitModule(__name__)
