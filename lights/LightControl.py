#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List

from extronlib import event
from extronlib.system import Wait
from extronlib.device import UIDevice
from extronlib.interface import SerialInterface
from extronlib.system import Timer
from extronlib.ui import Button, Label, Level

from lib.utils.module_init import InitModule
from lib.var.states import sStates, sPressed, sReleased, sHeld, sRepeated, sTapped
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.lights.MALightControl import MALightControl

from usr.dev.dev import ipad_adm, ipad_usr

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger("no", __name__)


class LightPowerProxy(object):
    def __init__(self, dev: AutoEthernetConnection):
        self._dev = dev
        self._dev.connect()
        self.cmdBuffer = list()
        self.sendTimer = Timer(0.3, self.sender)

    def send(self, cmd: str):
        self.cmdBuffer.append(cmd)
        self.sendTimer.Resume()

    def sender(self, timername, counter):
        if len(self.cmdBuffer) == 0:
            self.sendTimer.Stop()
        else:
            self._dev.connect()
            cmd = self.cmdBuffer.pop(0)
            self._dev.send(cmd)
            self._dev.disconnect()


class LightPower(object):
    def __init__(self, dev: LightPowerProxy, id: str, onValue: int):
        self._dev = dev
        self.id = id
        self.onValue = onValue
        self.light = "Off"
        self.tglLightBtns = list()
        self.__fbFunctions = list()

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglLightBtns.append(Button(uiHost, btnTglPowerID))

        @event(self.tglLightBtns, sStates)
        def tglLightBtnsEventHandler(btn: Button, state: str):
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
                self.tglPower()

    def tglPower(self):
        if (self.light == "On"):
            self.setPower("Off")
        else:
            self.setPower("On")

    def setPower(self, power: str):
        self.light = power
        self._dev.send(self.id + " " + (str(self.onValue) if power == "On" else "0"))
        self.showFb()
        self.callFbFunction()

    def showFb(self):
        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if self.light == "On" else 0)

    def addFbFunction(self, fbCallbackFunction: Callable[[str], None]):
        if callable(fbCallbackFunction):
            self.__fbFunctions.append(fbCallbackFunction)
            dbg.print("FB CALLBACK ADDED: {} - {}".format(self.id, fbCallbackFunction))
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def callFbFunction(self):
        for cf in self.__fbFunctions:
            cf(self.id, self.light)


class LightPowerGroup(object):
    def __init__(self):
        self.grouplight = "Off"
        self.groups = dict()
        self.tglLightBtns = list()

    def setMechanics(self, uiHost: UIDevice, btnTglPowerID: int):
        self.tglLightBtns.append(Button(uiHost, btnTglPowerID))

        @event(self.tglLightBtns, sStates)
        def tglLightBtnsEventHandler(btn: Button, state: str):
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
                self.tglPower()

    def addGroup(self, group: LightPower):
        self.groups[group.id] = {"group": group, "light": "Off"}
        self.groups[group.id]["group"].addFbFunction(self.fbFunction)

    def fbFunction(self, id: str, power: str):
        self.groups[id]["light"] = power
        dbg.print("CALLBACK: gr {} - light {}".format(id, self.groups[id]["light"]))

        allPower = True
        for iGr in self.groups:
            allPower = allPower and (self.groups[iGr]["light"] == "On")

        self.grouplight = "On" if allPower else "Off"

        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if allPower else 0)

    def tglPower(self):
        newPower = "On" if (self.grouplight == "Off") else "Off"
        for iGr in self.groups:
            self.groups[iGr]["group"].setPower(newPower)


class LightPowerGroupUser(LightPowerGroup):
    def __init__(self):
        super().__init__()

    def fbFunction(self, id: str, power: str):
        self.groups[id]["light"] = power
        dbg.print("CALLBACK USER: gr {} - light {}".format(id, self.groups[id]["light"]))

        allPower = False
        for iGr in self.groups:
            allPower = allPower or (self.groups[iGr]["light"] == "On")

        self.grouplight = "On" if allPower else "Off"

        for iBtn in self.tglLightBtns:
            iBtn.SetState(2 if allPower else 0)


class LightControlDimmerMA(object):
    def __init__(self, ma: MALightControl, fader_id: str, fader_name: str):
        self.ma = ma
        self.fader_id = fader_id
        self.fader_name = fader_name

        self.min_value = 0x00
        self.max_value = 0xff

        self.default_on = (self.max_value - self.min_value) / 100 * 70

        self.value = 0x00

        self.step_in_percent = 5
        self.step = (self.max_value - self.min_value) * self.step_in_percent / 100

        self.tgl_btns: List[Button] = list()
        self.on_btns: List[Button] = list()
        self.off_btns: List[Button] = list()
        self.inc_level_btns: List[Button] = list()
        self.dec_level_btns: List[Button] = list()
        self.value_lvls: List[Level] = list()
        self.value_lbls: List[Label] = list()
        self.name_lbls: List[Label] = list()

        self.preset_btns: List[Button] = list()

    def add_mechanics(self,
                      ui_host: UIDevice,
                      btn_tgl_id: int = None,
                      btn_on_id: int = None,
                      btn_off_id: int = None,
                      btn_inc_level_id: int = None,
                      btn_dec_level_id: int = None,
                      lvl_level_id: int = None,
                      lbl_value_id: int = None,
                      lbl_name_id: int = None):
        if btn_tgl_id is not None:
            self.tgl_btns.append(Button(ui_host, btn_tgl_id))

        if btn_on_id is not None:
            self.on_btns.append(Button(ui_host, btn_on_id))

        if btn_off_id is not None:
            self.off_btns.append(Button(ui_host, btn_off_id))

        if btn_inc_level_id is not None:
            self.inc_level_btns.append(Button(ui_host, btn_inc_level_id, holdTime=0.3, repeatTime=0.3))

        if btn_dec_level_id is not None:
            self.dec_level_btns.append(Button(ui_host, btn_dec_level_id, holdTime=0.3, repeatTime=0.3))

        if lvl_level_id is not None:
            new_lvl = Level(ui_host, lvl_level_id)
            new_lvl.SetRange(self.min_value, self.max_value)
            self.value_lvls.append(new_lvl)

        if lbl_value_id is not None:
            self.value_lbls.append(Label(ui_host, lbl_value_id))

        if lbl_name_id is not None:
            new_lbl_name = Label(ui_host, lbl_name_id)
            new_lbl_name.SetText(self.fader_name)
            self.name_lbls.append(new_lbl_name)

        @event(self.tgl_btns, sStates)
        def tgl_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1 if btn.State == 0 else 3)
            elif (state == sReleased):
                btn.SetState(0 if btn.State == 1 else 2)
                self.set_state()

        @event(self.on_btns, sStates)
        def on_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1 if btn.State == 0 else 3)
            elif (state == sReleased):
                btn.SetState(0 if btn.State == 1 else 2)
                self.set_state('On')

        @event(self.off_btns, sStates)
        def off_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1 if btn.State == 0 else 3)
            elif (state == sReleased):
                btn.SetState(0 if btn.State == 1 else 2)
                self.set_state('Off')

        @event(self.inc_level_btns, sStates)
        def inc_level_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sTapped):
                self.inc_value()

                @Wait(0.3)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.inc_value()
            elif (state == sReleased):
                btn.SetState(0)

        @event(self.dec_level_btns, sStates)
        def dec_level_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sTapped):
                self.dec_value()

                @Wait(0.3)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.dec_value()
            elif (state == sReleased):
                btn.SetState(0)

        self.show_fb()

    def add_preset_button(self, ui_host: UIDevice, btn_id: int, preset_percent: int):
        new_preset_btn = Button(ui_host, btn_id)
        new_preset_btn.SetText(str(preset_percent) + "%")
        setattr(new_preset_btn, 'preset_percent', preset_percent)
        self.preset_btns.append(new_preset_btn)

        @event(new_preset_btn, sStates)
        def preset_btn_event_handler(btn: Button, state: str):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sReleased):
                btn.SetState(0)
                percent = getattr(btn, 'preset_percent')
                if percent is not None:
                    self.set_value(self.max_value * percent / 100)

    def inc_value(self):
        if (self.value + self.step > self.max_value):
            self.set_value(self.max_value)
        else:
            self.set_value(self.value + self.step)

    def dec_value(self):
        if (self.value - self.step < self.min_value):
            self.set_value(self.min_value)
        else:
            self.set_value(self.value - self.step)

    def set_value(self, value: int):
        self.value = round(value)
        self.ma.set_value(self.fader_id, self.value)
        self.show_fb()

    def set_state(self, new_state: str = None):
        if (new_state is not None):
            if (str.upper(new_state) == "ON"):
                self.set_value(self.default_on)
            elif (str.upper(new_state) == "OFF"):
                self.set_value(self.min_value)
        else:
            if (self.value > 0):
                self.set_value(self.min_value)
            else:
                self.set_value(self.default_on)

    def show_fb(self):
        value_in_percent = str(round((self.value - self.min_value) / (self.max_value - self.min_value) * 100)) + ' %'
        for i_lbl in self.value_lbls:
            i_lbl.SetText(value_in_percent)

        for i_btn in self.tgl_btns:
            i_btn.SetState(2 if (self.value > 0) else 0)

        for i_lvl in self.value_lvls:
            i_lvl.SetLevel(int(self.value))

        for i_btn in self.off_btns:
            if (self.value == 0):
                i_btn.SetState(2)
            else:
                i_btn.SetState(0)

        for i_btn in self.on_btns:
            if (self.value == self.max_value):
                i_btn.SetState(2)
            else:
                i_btn.SetState(0)

        for i_btn in self.preset_btns:
            if (self.value == int(getattr(i_btn, 'preset_percent') * self.max_value / 100)):
                i_btn.SetState(2)
            else:
                i_btn.SetState(0)
