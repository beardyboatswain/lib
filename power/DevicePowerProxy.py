#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib.system import Timer, Wait

import lib.utils.signals as signals
from lib.utils.module_init import InitModule

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)

LcdProxySamsHG_dbg = "no"
LcdProxySamsDM_dbg = "no"
LcdGSProxy_dbg = "no"
ProjectorGSProxy_dbg = "no"


class LcdProxySamsHG(object):
    def __init__(self, dev, rfbPowerCallback=None):
        self._dev = dev
        self._power = None

        self.dbg = debugger(LcdProxySamsHG_dbg, self.__class__)

        self._rfbPowerCallback = []
        if rfbPowerCallback is not None:
            self.rfbPowerCallback = rfbPowerCallback

        self._dev.subscribe("Connected", self.lcdConnectEventHandler)
        self._dev.subscribe("Disconnected", self.lcdConnectEventHandler)
        self._dev.subscribe("ReceiveData", self.lcdRxEventHandler)
        self._dev.connect()

    def rfbCall(self, rfbPowerCallbackParam):
        if rfbPowerCallbackParam == "power":
            for rfbPowerCallbackFunc in self.rfbPowerCallback:
                if callable(rfbPowerCallbackFunc):
                    rfbPowerCallbackFunc(self._power)

    def lcdConnectEventHandler(self, interface, state):
        self.dbg.print("Connection Handler out of class: {} {}".format(interface, state))
        if (state == "Connect"):
            self.dbg.print("Lcd Online")

    def lcdRxEventHandler(self, interface, data):
        if b"\x68\x00\x01\x04\x01" in data:
            self.dbg.print("LCD <{}> RX<{}>".format(self._dev.port, data))
            self.dbg.print("LCD <{}> POWER <{}>".format(self._dev.port, self._power))
            self._power = "On"
            self.rfbCall("power")
        elif b"\x68\x00\x01\x04\x00" in data:
            self.dbg.print("LCD <{}> RX<{}>".format(self._dev.port, data))
            self.dbg.print("LCD <{}> POWER <{}>".format(self._dev.port, self._power))
            self._power = "Off"
            self.rfbCall("power")

    @property
    def rfbPowerCallback(self):
        return self._rfbPowerCallback

    @rfbPowerCallback.setter
    def rfbPowerCallback(self, callbackMethod):
        if callbackMethod is not None:
            if callable(callbackMethod):
                self._rfbPowerCallback.append(callbackMethod)
            else:
                raise TypeError("{} is not callable".format(callbackMethod))
        else:
            self._rfbPowerCallback.append(callbackMethod)

    def power(self, nPower):
        self.dbg.print("Power set to {}".format(nPower))
        if (nPower.title() == "On") or (
            (nPower.title() == "Tgl") and (self._power == "Off")
        ):
            self._dev.send(b"\x68\x80\x00\x01\x80\x69")
        elif (nPower.title() == "Off") or (
            (nPower.title() == "Tgl") and (self._power == "On")
        ):
            self._dev.send(b"\x68\x80\x00\x01\x00\xE9")


class LcdProxySamsDM(object):
    def __init__(self, dev, rfbPowerCallback=None):
        self._dev = dev
        self._power = None

        self.dbg = debugger(LcdProxySamsDM_dbg, self.__class__)

        self._rfbPowerCallback = []
        if rfbPowerCallback is not None:
            self.rfbPowerCallback = rfbPowerCallback

        self._dev.subscribe("Connected", self.lcdConnectEventHandler)
        self._dev.subscribe("Disconnected", self.lcdConnectEventHandler)
        self._dev.subscribe("ReceiveData", self.lcdRxEventHandler)
        self._dev.connect()

    def rfbCall(self, rfbPowerCallbackParam):
        if rfbPowerCallbackParam == "power":
            for rfbPowerCallbackFunc in self.rfbPowerCallback:
                if callable(rfbPowerCallbackFunc):
                    rfbPowerCallbackFunc(self._power)

    def lcdConnectEventHandler(self, interface, state):
        self.dbg.print("Connection Handler out of class: {} {}".format(interface, state))
        if (state == "Connect"):
            self.dbg.print("Lcd Online")

    def lcdRxEventHandler(self, interface, data):
        self.dbg.print("Lcd RX<{}>".format(data))
        if b"\xaa\xff\x01\x03\x41\x11\x01\x56" in data:
            self._power = "On"
            self.rfbCall("power")
        elif b"\xaa\xff\x01\x03\x41\x11\x00\x55" in data:
            self._power = "Off"
            self.rfbCall("power")

    @property
    def rfbPowerCallback(self):
        return self._rfbPowerCallback

    @rfbPowerCallback.setter
    def rfbPowerCallback(self, callbackMethod):
        if callbackMethod is not None:
            if callable(callbackMethod):
                self._rfbPowerCallback.append(callbackMethod)
            else:
                raise TypeError("{} is not callable".format(callbackMethod))
        else:
            self._rfbPowerCallback.append(callbackMethod)

    def power(self, nPower):
        self.dbg.print("Power set to {}".format(nPower))
        if (nPower.title() == "On") or (
            (nPower.title() == "Tgl") and (self._power == "Off")
        ):
            self._dev.send(b"\xaa\x11\x01\x01\x01\x14")
        elif (nPower.title() == "Off") or (
            (nPower.title() == "Tgl") and (self._power == "On")
        ):
            self._dev.send(b"\xaa\x11\x01\x01\x00\x13")


class LcdGSProxy(object):
    def __init__(self, dev, rfbPowerCallback=None):
        self._dev = dev
        self._power = None

        self.dbg = debugger(LcdGSProxy_dbg, self.__class__)

        self._rfbPowerCallback = rfbPowerCallback
        if self._rfbPowerCallback is not None:
            self.rfbPowerCallback = rfbPowerCallback

        def lcdStatusHandler(command, value, qualifier):
            self.dbg.print(
                "LCD Cmd={} Val={} Qaul={}".format(command, value, qualifier)
            )
            if command == "Power":
                self._power = value
                self.dbg.print("self._power = {}".format(self._power))
                if callable(self._rfbPowerCallback):
                    self._rfbPowerCallback(self._power)

        self._dev.Connect()
        self._dev.SubscribeStatus("Power", None, lcdStatusHandler)
        self._dev.Update("Power", {"Device ID": "1"})

    @property
    def rfbPowerCallback(self):
        return self._rfbPowerCallback

    @rfbPowerCallback.setter
    def rfbPowerCallback(self, callbackMethod):
        if callbackMethod is not None:
            if callable(callbackMethod):
                self._rfbPowerCallback = callbackMethod
            else:
                raise TypeError("{} is not callable".format(callbackMethod))
        else:
            self._rfbPowerCallback = callbackMethod

    def power(self, nPower):
        self.dbg.print("Power set to {}".format(nPower))
        self.dbg.print("nPower.title() is {}".format(nPower.title()))
        self.dbg.print("nPower.title() is On = {}".format((nPower.title() == "On")))

        if (nPower.title() == "On") or (
            (nPower.title() == "Tgl") and (self._power == "Off")
        ):
            self._dev.Set("Power", "On", {"Device ID": "1"})
        elif (nPower.title() == "Off") or (
            (nPower.title() == "Tgl") and (self._power == "On")
        ):
            self._dev.Set("Power", "Off", {"Device ID": "1"})


class ProjectorGSProxy(object):
    def __init__(self, dev, rfbPowerCallback=None, rfbLampUsageCallback=None):
        self._dev = dev
        self._power = None
        self._lampusage = None

        self.dbg = debugger(ProjectorGSProxy_dbg, self.__class__)

        self._rfbPowerCallback = []
        if rfbPowerCallback is not None:
            self.rfbPowerCallback = rfbPowerCallback

        self._rfbLampUsageCallback = []
        if self._rfbLampUsageCallback is not None:
            self.rfbLampUsageCallback = rfbLampUsageCallback

        self._dev.Connect()
        self._dev.SubscribeStatus("Power", None, self.projStatusHandler)
        self._dev.SubscribeStatus("LampUsage", None, self.projStatusHandler)
        self._dev.Update("Power")
        self._dev.Update("LampUsage")

        self._pollTimer = Timer(6, self.pollTimerHandler)

    def projStatusHandler(self, command, value, qualifier):
        self.dbg.print(
            "Projector Cmd={} Val={} Qaul={}".format(command, value, qualifier)
        )
        if command == "Power":
            # self.dbg.print("PROJ <{}> RX<{}>".format(self._dev.port, value))
            # self.dbg.print("PROJ <{}> POWER <{}>".format(self._dev.port, self._power))
            self._power = value
            self.rfbCall("power")
        elif command == "LampUsage":
            # self.dbg.print("PROJ <{}> RX<{}>".format(self._dev.port, value))
            # self.dbg.print("PROJ <{}> POWER <{}>".format(self._dev.port, self._power))
            self._lampusage = value
            self.rfbCall("lampusage")

    def rfbCall(self, rfbCallbackParam):
        if rfbCallbackParam == "power":
            for rfbPowerCallbackFunc in self.rfbPowerCallback:
                if callable(rfbPowerCallbackFunc):
                    rfbPowerCallbackFunc(self._power)
        elif rfbCallbackParam == "lampusage":
            for rfbLampUsageCallbackFunc in self.rfbLampUsageCallback:
                if callable(rfbLampUsageCallbackFunc):
                    rfbLampUsageCallbackFunc(self._power)

    @property
    def rfbPowerCallback(self):
        return self._rfbPowerCallback

    @rfbPowerCallback.setter
    def rfbPowerCallback(self, callbackMethod):
        if callbackMethod is not None:
            if callable(callbackMethod):
                self._rfbPowerCallback.append(callbackMethod)
            else:
                raise TypeError("{} is not callable".format(callbackMethod))
        else:
            self._rfbPowerCallback.append(callbackMethod)

    @property
    def rfbLampUsageCallback(self):
        return self._rfbLampUsageCallback

    @rfbLampUsageCallback.setter
    def rfbLampUsageCallback(self, callbackMethod):
        if callbackMethod is not None:
            if callable(callbackMethod):
                self._rfbLampUsageCallback.append(callbackMethod)
            else:
                raise TypeError("{} is not callable".format(callbackMethod))
        else:
            self._rfbLampUsageCallback.append(callbackMethod)

    def power(self, nPower):
        self.dbg.print("Power set to {}".format(nPower))
        if (nPower.title() == "On") or (
            (nPower.title() == "Tgl") and (self._power == "Off")
        ):
            self._dev.Set("Power", "On")
        elif (nPower.title() == "Off") or (
            (nPower.title() == "Tgl") and (self._power == "On")
        ):
            self._dev.Set("Power", "Off")

    def pollTimerHandler(self, timer, count):
        self.dbg.print("POLL TIMER PROJECTORS")
        self._dev.Update("Power")
        self._dev.Update("LampUsage")

        @Wait(2)
        def updateStatus():
            self.projStatusHandler("Power", self._dev.ReadStatus("Power"), None)
            self.projStatusHandler("LampUsage", self._dev.ReadStatus("LampUsage"), None)


InitModule(__name__)
