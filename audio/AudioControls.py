from extronlib import event, Version
from extronlib.device import eBUSDevice, ProcessorDevice, UIDevice
from extronlib.interface import (CircuitBreakerInterface, ContactInterface,
                                 DigitalInputInterface, DigitalIOInterface, EthernetClientInterface,
                                 EthernetServerInterfaceEx, FlexIOInterface, IRInterface, PoEInterface,
                                 RelayInterface, SerialInterface, SWACReceptacleInterface, SWPowerInterface,
                                 VolumeInterface)
from extronlib.ui import Button, Knob, Label, Level
from extronlib.system import Clock, MESet, Timer, Wait

import lib.utils.signals as signals
from lib.utils.system_init import InitModule
from lib.var.states import sPressed, sReleased, sHeld, sTapped, sRepeated, sStates

from usr.dev.dev import biamp
from lib.audio.AudioProxy import AudioProxyBiampTesira

from lib.utils.debugger import debuggerNet as debugger
from lib.var.lib_debug_mode import AudioControls_dbg
dbg = debugger(AudioControls_dbg, __name__)


class FaderControl():
    def __init__(self,
                 dev: AudioProxyBiampTesira,
                 instancetag: str = "Instance1",
                 channel: int = 1,
                 name="Level",
                 comment="",
                 minValue: int = -100,
                 maxValue: int = 12,
                 stepValue: int = 1):
        """
        devicenumber - biamp nexia unit id
        instanceid - biamp nexia module id
        channel - biamp nexia fader number in module
        verbalname - name of level, level description
        """
        # self.ui = ui
        self.dev = dev
        self.instancetag = instancetag
        self.channel = channel
        self.name = name
        self.comment = comment

        self.min = minValue
        self.max = maxValue
        self.step = stepValue
        self.value = 0
        self.mute = False

        self.btnInc = list()
        self.btnDec = list()
        self.btnMute = list()
        self.lvlValue = list()
        self.lblValue = list()
        self.lblName = list()
        self.lblComment = list()

        self.dev.addLevel(self.instancetag, self.channel, self.fbHandler)

    def __showlvl__(self):
        dbg.print('showlvl new level {}_{} = {}'.format(self.instancetag, self.channel, self.value))
        for iL in self.lvlValue:
            iL.SetLevel(int(self.value))
        for iL in self.lblValue:
            iL.SetText('{} dB'.format(self.value))

    def __showmute__(self):
        for iM in self.btnMute:
            iM.SetState(2) if self.mute else iM.SetState(0)

    def __inc__(self):
        if (self.value + self.step <= self.max):
            self.value += self.step
        else:
            self.value = self.max
        self.__showlvl__()
        self.dev.setLevel(instanceTag=self.instancetag, channel=self.channel, value=self.value)

    def __dec__(self):
        if (self.value - self.step >= self.min):
            self.value -= self.step
        else:
            self.value = self.min
        self.__showlvl__()
        self.dev.setLevel(instanceTag=self.instancetag, channel=self.channel, value=self.value)

    def __mute__(self):
        self.mute = not self.mute
        self.__showmute__()
        self.dev.setMute(instanceTag=self.instancetag, channel=self.channel, value='On' if self.mute else 'Off')

    def setMechanics(self,
                     uiHost: UIDevice,
                     btnIncId: int,
                     btnDecId: int,
                     btnMuteId: int,
                     lvlValueId: int,
                     lblValueId: int = None,
                     lblNameId: int = None,
                     lblCommentId: int = None):

        newBtnInc = Button(uiHost, btnIncId, holdTime=0.5, repeatTime=0.2)
        newBtnDec = Button(uiHost, btnDecId, holdTime=0.5, repeatTime=0.2)
        newBtnMute = Button(uiHost, btnMuteId)

        newLvlValue = Level(uiHost, lvlValueId)
        newLvlValue.SetRange(self.min, self.max, self.step)

        newLblValue = Label(uiHost, lblValueId)

        newLblName = None
        if (lblNameId):
            newLblName = Label(uiHost, lblNameId)
            newLblName.SetText(self.name)

        newLblComment = None
        if (lblCommentId):
            newLblComment = Label(uiHost, lblCommentId)
            newLblComment.SetText(self.comment)

        self.btnInc.append(newBtnInc)
        self.btnDec.append(newBtnDec)
        self.btnMute.append(newBtnMute)
        self.lvlValue.append(newLvlValue)
        self.lblValue.append(newLblValue)

        if newLblName:
            self.lblName.append(newLblName)

        if newLblComment:
            self.lblComment.append(newLblComment)

        @event(self.btnInc, sStates)
        def btnIncHandler(btn, state):
            if (state == sPressed):
                btn.SetState(1)
                self.__inc__()
            elif (state == sTapped):
                # btn.SetState(1)
                # self.__inc__()
                # @Wait(0.3)
                # def tappedSetStateOff():
                #     btn.SetState(0)
                @Wait(0.3)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.__inc__()
            elif (state == sReleased):
                btn.SetState(0)

        @event(self.btnDec, sStates)
        def btnDecHandler(btn, state):
            if (state == sPressed):
                btn.SetState(1)
                self.__dec__()
            elif (state == sTapped):
                # btn.SetState(1)
                # self.__dec__()
                # @Wait(0.3)
                # def tappedSetStateOff():
                #     btn.SetState(0)
                @Wait(0.3)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sRepeated):
                self.__dec__()
            elif (state == sReleased):
                btn.SetState(0)

        @event(self.btnMute, sStates)
        def btnMuteHandler(btn, state):
            if (state == sPressed):
                btn.SetState(1)
            elif (state == sTapped):
                btn.SetState(1)
                self.__mute__()

                @Wait(0.3)
                def tappedSetStateOff():
                    btn.SetState(0)
            elif (state == sReleased):
                btn.SetState(0)
                self.__mute__()

        self.__showlvl__()
        self.__showmute__()

    def fbHandler(self, itType, value):
        if (itType == AudioProxyBiampTesira.tagLevel):
            self.value = value
            self.__showlvl__()
        elif (itType == AudioProxyBiampTesira.tagMute):
            self.mute = (value == "On")
            self.__showmute__()


class CrosspointControl():
    def __init__(self,
                 ui: UIDevice,
                 dev: AudioProxyBiampTesira,
                 instancetag: str = 'Instance1',
                 name: str = 'Crosspoint',
                 points: tuple = ((1, 1), )
                 ):

        self.ui = ui
        self.instancetag = instancetag
        self.dev = dev
        self.name = name
        self.points = points

        self.btnOnOff = None
        self.value = "Off"

        self.states = dict()
        for p in self.points:
            self.states[p] = "Off"

        self.dev.addCposspoint(self.instancetag, self.points, self.fbHandler)

    def __showPoint__(self):
        self.btnOnOff.SetState(2 if (self.value == 'On') else 0)

    def __toggleState__(self):
        self.__setState__('On' if (self.value == 'Off') else 'Off')

    def __setState__(self, state: str):
        """
        state = "On" | "Off"
        """
        if (state in ["On", "Off"]):
            self.dev.setCrosspoint(self.instancetag, self.points, state)

    def setMechanics(self, btnOnOffId):
        self.btnOnOff = Button(self.ui, btnOnOffId)
        self.btnOnOff.SetText(self.name)
        self.__showPoint__()

        @event(self.btnOnOff, sStates)
        def btnIncHandler(btn: Button, state: str):
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
                self.__toggleState__()

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.__setState__(value)

    def fbHandler(self, point: tuple, value: str):
        self.states[point] = value
        self.value = True
        for s in self.states:
            self.value = self.value and (self.states.get(s) == "On")
        self.value = "On" if self.value else "Off"
        self.__showPoint__()


class SignalPresentMeter():
    def __init__(self,
                 ui: UIDevice,
                 dev: AudioProxyBiampTesira,
                 instancetag: str = 'Instance1',
                 channel: int = 1,
                 name='Channel Identifier'):

        self.ui = ui
        self.dev = dev
        self.instancetag = instancetag
        self.channel = channel
        self.name = name

        self.value = 'No Signal Present'
        self.btnProbe = None

        self.dev.addSignalPresentMeter(self.instancetag, self.channel, self.name, self.fbHandler)

    def __showSignal__(self):
        if (self.btnProbe is not None):
            self.btnProbe.SetState(1 if (self.value == 'Signal Present') else 0)
            signals.emit("*", signal="MicActive", params={"mic": self.name, "state": (1 if (self.value == 'Signal Present') else 0)})

    def setMechanics(self, btnProbeId: int):
        self.btnProbe = Button(self.ui, btnProbeId)
        self.__showSignal__()

    def fbHandler(self, value: str):
        self.value = value
        self.__showSignal__()


class LogicMeter():
    def __init__(self,
                 ui: UIDevice,
                 dev: AudioProxyBiampTesira,
                 instancetag: str = 'Instance1',
                 channel: int = 1):

        self.ui = ui
        self.dev = dev
        self.instancetag = instancetag
        self.channel = channel

        self.value = 'True'
        self.btnProbe = None

        self.dev.addLogicMeter(self.instancetag, self.channel, self.fbHandler)

    def __showSignal__(self):
        if (self.btnProbe is not None):
            self.btnProbe.SetState(1 if (self.value == 'True') else 0)

    def setMechanics(self, btnProbeId: int):
        self.btnProbe = Button(self.ui, btnProbeId)
        self.__showSignal__()

    def fbHandler(self, value: str):
        self.value = value
        self.__showSignal__()


class MuteControl():
    def __init__(self,
                 dev: AudioProxyBiampTesira,
                 instancetag: str = "Instance1",
                 channel: int = 1,
                 name="Mute",
                 comment=""):
        self.dev = dev
        self.instancetag = instancetag
        self.channel = channel
        self.name = name
        self.comment = comment
        self.mute = False
        self.btnMute = list()
        self.btnName = list()
        self.btnComment = list()

        self.dev.addMute(self.instancetag, self.channel, self.fbHandler)

    def __showmute__(self):
        for iM in self.btnMute:
            if iM:
                iM.SetState(2) if self.mute else iM.SetState(0)

    def __mute__(self):
        self.mute = not self.mute
        self.__showmute__()
        self.dev.setMute(instanceTag=self.instancetag, channel=self.channel, value='On' if self.mute else 'Off')

    def setMechanics(self,
                     uiHost: UIDevice,
                     btnMuteId: int,
                     btnNameId: int,
                     btnCommentId: int = None):

        newBtnMute = Button(uiHost, btnMuteId)

        newBtnName = Button(uiHost, btnNameId)
        newBtnName.SetText(self.name)

        newBtnComment = Button(uiHost, btnCommentId)
        newBtnComment.SetText(self.comment)

        self.btnMute.append(newBtnMute)
        self.btnName.append(newBtnName)
        self.btnComment.append(newBtnComment)

        @event(self.btnMute, sStates)
        @event(self.btnName, sStates)
        @event(self.btnComment, sStates)
        def btnMuteHandler(btn: Button, state: str):
            if (state == sPressed):
                if (self.btnMute.State == 0):
                    self.btnMute.SetState(1)
                elif (self.btnMute.State == 2):
                    self.btnMute.SetState(3)
            elif (state == sTapped):
                if (self.btnMute.State == 0):
                    self.btnMute.SetState(1)
                elif (self.btnMute.State == 2):
                    self.btnMute.SetState(3)
                self.__mute__()

                @Wait(0.3)
                def tappedSetStateOff():
                    if (self.btnMute.State == 1):
                        self.btnMute.SetState(0)
                    elif (self.btnMute.State == 3):
                        self.btnMute.SetState(2)
            elif (state == sReleased):
                if (self.btnMute.State == 1):
                    self.btnMute.SetState(0)
                elif (self.btnMute.State == 3):
                    self.btnMute.SetState(2)
                self.__mute__()

    def fbHandler(self, itType: str, value: str):
        if (itType == AudioProxyBiampTesira.tagMute):
            self.mute = (value == "On")
            self.__showmute__()


class PresetControl():
    def __init__(self, dev: AudioProxyBiampTesira):
        self.dev = dev

    def call(self, presetId: int):
        self.dev.presetCall(presetId)

    def save(self, presetId: int):
        self.dev.presetCall(presetId)


InitModule(__name__)
