#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
import time

from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import Timer, Wait
from extronlib.ui import Button
from extronlib import event
from usr.dev.dev import ipad_adm

import lib.utils.signals as signals

import lib.helpers.ConnectionHandler as ConnectionHandler
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection

from usr.dev.dev import (aten_pdu1CP,
                         aten_pdu2CP,
                         aten_pdu3CP,
                         aten_pdu4CP,
                         aten_pdu5CP,
                         aten_pdu6CP)

from lib.utils.debugger import debuggerNet as debugger
from usr.var.debug_mode import dev_aten_pdu_dbg
dbg = debugger(dev_aten_pdu_dbg, __name__)


class atenPDU:
    def __init__(self, device: AutoEthernetConnection, outletSize: int):

        self.device = device
        self.outletSize = outletSize
        self.states = dict()
        self.atenMatchFB = re.compile("Outlet ([0-9]{2}) (on|off)")
        self.atenLoginFB = re.compile("Login:")
        self.atenPasswordFB = re.compile("Password:")
        self.atenLoginOKFB = re.compile("Logged in successfully")
        self.atenButtons = dict()
        self.device.subscribe("Connected", self.ConnectEventHandler)
        self.device.subscribe("Disconnected", self.ConnectEventHandler)
        self.device.subscribe("ReceiveData", self.atenReceiveDataHandler)
        self.atenRxBuf = str()
        self.renewtimer = Timer(10, self.refreshOutlet)
        self.renewtimer.Stop()
        self.device.connect()

    # definisemo funkciju koja odrzava konekciju - svakix 10 sekundi pitamo za status outputa.
    def refreshOutlet(self, timer: Timer, count: int):
        self.requestOutlet()

    def requestOutlet(self, nOut: int = None):
        dbg.print("request Outlets")
        if nOut:
            self.device.send("read status o{:02} format\x0d\x0a".format(nOut))
        else:
            for iOut in range(1, self.outletSize + 1):
                self.device.send("read status o{:02} format\x0d\x0a".format(iOut))

    # definisemo funkciju koja upravlja outputom. - ovde prosledjujemo string sa komandom
    def setOutletState(self, nOut: int, newState: str) -> None:
        self.device.send("sw o{:02} {} imme\r\n".format(nOut, newState))
        self.requestOutlet(nOut=nOut)

    def getOutletState(self, nOut: int) -> str:
        return self.states.get(nOut)

    def toggleOutletState(self, nOut: int) -> None:
        if self.states[nOut] == "on":
            self.setOutletState(nOut, newState="off")
        else:
            self.setOutletState(nOut, newState="on")

    def addButton(self, NewButton, ButtonNo):
        self.atenButtons[ButtonNo] = NewButton

    # komunikacija sa uredjajem. Skupljamo eho koji nam uredjaj vraca i kada dodje
    # do \r\n sastavljamo ga i reagujemo ukoliko nam trazi login ili password.
    def ConnectEventHandler(self, interface, state):
        dbg.print("Connection Handler: Aten PDU {}".format(state))

    def atenRXparser(self, rxLine: str):
        dataLines = rxLine
        dbg.print(rxLine)
        for rxLine in dataLines.splitlines():
            atenLoginObjectFB = self.atenLoginFB.search(rxLine)
            if atenLoginObjectFB:
                self.device.send(self.device.login + "\r\n")
            atenPasswordObjectFB = self.atenPasswordFB.search(rxLine)
            if atenPasswordObjectFB:
                self.device.send(self.device.password + "\r\n")
            atenLoginOK = self.atenLoginOKFB.search(rxLine)
            if atenLoginOK:
                self.renewtimer.Restart()
            atenOutletStateObjectFB = self.atenMatchFB.search(rxLine)
            if atenOutletStateObjectFB:
                outletNO = int(atenOutletStateObjectFB.group(1))
                outletState = str(atenOutletStateObjectFB.group(2))
                self.states[outletNO] = outletState
                self.atenButtons[outletNO].SetState(0 if outletState == "off" else 2)

                # dbg.print("Ties MatchObject: {}".format(kramerMatchObjectTiesFb))
                # if kramerMatchObjectTiesFb:
                #     for mO in kramerMatchObjectTiesFb:
                #         self.kramerStates[int(mO[2])] = int(mO[1])
                #         self.executeFbFunctions(int(mO[2]), int(mO[1]))
                #     dbg.print("kramerState {}".format(self.kramerStates))

    def atenReceiveDataHandler(self, interface, data):
        # dbg.print("Aten recieved from [{}]: {} ".format(interface, data.decode()))

        self.atenRxBuf += data.decode()

        while (
            (self.atenRxBuf.find("\x0d\x0a") > -1)
            or (self.atenRxBuf.find("Login:") > -1)
            or (self.atenRxBuf.find("Password") > -1)
        ):
            # self.atenRXparser(self.atenRxBuf.partition("\x0d\x0a")[0])
            # self.atenRxBuf = self.atenRxBuf.partition("\x0d\x0a")[2]
            self.atenRXparser(self.atenRxBuf + "\n")
            self.atenRxBuf = ""


# ovde prenosimo uredjaje definisane u dev.dev.py U nasem slucaju cemo imati 6 uredjaja i sve kontrolisemo jednom klasom.
aten01 = atenPDU(device=aten_pdu1CP, outletSize=8)
aten02 = atenPDU(device=aten_pdu2CP, outletSize=8)
aten03 = atenPDU(device=aten_pdu3CP, outletSize=8)
aten04 = atenPDU(device=aten_pdu4CP, outletSize=8)
aten05 = atenPDU(device=aten_pdu5CP, outletSize=8)
aten06 = atenPDU(device=aten_pdu6CP, outletSize=8)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU1O1 = Button(ipad_adm, 7101)
btnPowerPDU1O2 = Button(ipad_adm, 7102)
btnPowerPDU1O3 = Button(ipad_adm, 7103)
btnPowerPDU1O4 = Button(ipad_adm, 7104)
btnPowerPDU1O5 = Button(ipad_adm, 7105)
btnPowerPDU1O6 = Button(ipad_adm, 7106)
btnPowerPDU1O7 = Button(ipad_adm, 7107)
btnPowerPDU1O8 = Button(ipad_adm, 7108)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU2O1 = Button(ipad_adm, 7201)
btnPowerPDU2O2 = Button(ipad_adm, 7202)
btnPowerPDU2O3 = Button(ipad_adm, 7203)
btnPowerPDU2O4 = Button(ipad_adm, 7204)
btnPowerPDU2O5 = Button(ipad_adm, 7205)
btnPowerPDU2O6 = Button(ipad_adm, 7206)
btnPowerPDU2O7 = Button(ipad_adm, 7207)
btnPowerPDU2O8 = Button(ipad_adm, 7208)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU3O1 = Button(ipad_adm, 7301)
btnPowerPDU3O2 = Button(ipad_adm, 7302)
btnPowerPDU3O3 = Button(ipad_adm, 7303)
btnPowerPDU3O4 = Button(ipad_adm, 7304)
btnPowerPDU3O5 = Button(ipad_adm, 7305)
btnPowerPDU3O6 = Button(ipad_adm, 7306)
btnPowerPDU3O7 = Button(ipad_adm, 7307)
btnPowerPDU3O8 = Button(ipad_adm, 7308)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU4O1 = Button(ipad_adm, 7401)
btnPowerPDU4O2 = Button(ipad_adm, 7402)
btnPowerPDU4O3 = Button(ipad_adm, 7403)
btnPowerPDU4O4 = Button(ipad_adm, 7404)
btnPowerPDU4O5 = Button(ipad_adm, 7405)
btnPowerPDU4O6 = Button(ipad_adm, 7406)
btnPowerPDU4O7 = Button(ipad_adm, 7407)
btnPowerPDU4O8 = Button(ipad_adm, 7408)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU5O1 = Button(ipad_adm, 7501)
btnPowerPDU5O2 = Button(ipad_adm, 7502)
btnPowerPDU5O3 = Button(ipad_adm, 7503)
btnPowerPDU5O4 = Button(ipad_adm, 7504)
btnPowerPDU5O5 = Button(ipad_adm, 7505)
btnPowerPDU5O6 = Button(ipad_adm, 7506)
btnPowerPDU5O7 = Button(ipad_adm, 7507)
btnPowerPDU5O8 = Button(ipad_adm, 7508)

# btnPowerPDU1_ALL = Button(iPadAdm, 7000)
btnPowerPDU6O1 = Button(ipad_adm, 7601)
btnPowerPDU6O2 = Button(ipad_adm, 7602)
btnPowerPDU6O3 = Button(ipad_adm, 7603)
btnPowerPDU6O4 = Button(ipad_adm, 7604)
btnPowerPDU6O5 = Button(ipad_adm, 7605)
btnPowerPDU6O6 = Button(ipad_adm, 7606)
btnPowerPDU6O7 = Button(ipad_adm, 7607)
btnPowerPDU6O8 = Button(ipad_adm, 7608)

# aten01.addButton(btnPowerPDU1_ALL, )
aten01.addButton(btnPowerPDU1O1, 1)
aten01.addButton(btnPowerPDU1O2, 2)
aten01.addButton(btnPowerPDU1O3, 3)
aten01.addButton(btnPowerPDU1O4, 4)
aten01.addButton(btnPowerPDU1O5, 5)
aten01.addButton(btnPowerPDU1O6, 6)
aten01.addButton(btnPowerPDU1O7, 7)
aten01.addButton(btnPowerPDU1O8, 8)

# aten01.addButton(btnPowerPDU1_ALL, )
aten02.addButton(btnPowerPDU2O1, 1)
aten02.addButton(btnPowerPDU2O2, 2)
aten02.addButton(btnPowerPDU2O3, 3)
aten02.addButton(btnPowerPDU2O4, 4)
aten02.addButton(btnPowerPDU2O5, 5)
aten02.addButton(btnPowerPDU2O6, 6)
aten02.addButton(btnPowerPDU2O7, 7)
aten02.addButton(btnPowerPDU2O8, 8)

# aten01.addButton(btnPowerPDU1_ALL, )
aten03.addButton(btnPowerPDU3O1, 1)
aten03.addButton(btnPowerPDU3O2, 2)
aten03.addButton(btnPowerPDU3O3, 3)
aten03.addButton(btnPowerPDU3O4, 4)
aten03.addButton(btnPowerPDU3O5, 5)
aten03.addButton(btnPowerPDU3O6, 6)
aten03.addButton(btnPowerPDU3O7, 7)
aten03.addButton(btnPowerPDU3O8, 8)

# aten01.addButton(btnPowerPDU1_ALL, )
aten04.addButton(btnPowerPDU4O1, 1)
aten04.addButton(btnPowerPDU4O2, 2)
aten04.addButton(btnPowerPDU4O3, 3)
aten04.addButton(btnPowerPDU4O4, 4)
aten04.addButton(btnPowerPDU4O5, 5)
aten04.addButton(btnPowerPDU4O6, 6)
aten04.addButton(btnPowerPDU4O7, 7)
aten04.addButton(btnPowerPDU4O8, 8)

# aten01.addButton(btnPowerPDU1_ALL, )
aten05.addButton(btnPowerPDU5O1, 1)
aten05.addButton(btnPowerPDU5O2, 2)
aten05.addButton(btnPowerPDU5O3, 3)
aten05.addButton(btnPowerPDU5O4, 4)
aten05.addButton(btnPowerPDU5O5, 5)
aten05.addButton(btnPowerPDU5O6, 6)
aten05.addButton(btnPowerPDU5O7, 7)
aten05.addButton(btnPowerPDU5O8, 8)

# aten01.addButton(btnPowerPDU1_ALL, )
aten06.addButton(btnPowerPDU6O1, 1)
aten06.addButton(btnPowerPDU6O2, 2)
aten06.addButton(btnPowerPDU6O3, 3)
aten06.addButton(btnPowerPDU6O4, 4)
aten06.addButton(btnPowerPDU6O5, 5)
aten06.addButton(btnPowerPDU6O6, 6)
aten06.addButton(btnPowerPDU6O7, 7)
aten06.addButton(btnPowerPDU6O8, 8)


@event(
    [
        btnPowerPDU1O1,
        btnPowerPDU1O2,
        btnPowerPDU1O3,
        btnPowerPDU1O4,
        btnPowerPDU1O5,
        btnPowerPDU1O6,
        btnPowerPDU1O7,
        btnPowerPDU1O8,
    ],
    "Pressed",
)
def btnPowerPDU1EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU1O1:
        aten01.toggleOutletState(nOut=1)
    elif button == btnPowerPDU1O2:
        aten01.toggleOutletState(nOut=2)
    elif button == btnPowerPDU1O3:
        aten01.toggleOutletState(nOut=3)
    elif button == btnPowerPDU1O4:
        aten01.toggleOutletState(nOut=4)
    elif button == btnPowerPDU1O5:
        aten01.toggleOutletState(nOut=5)
    elif button == btnPowerPDU1O6:
        aten01.toggleOutletState(nOut=6)
    elif button == btnPowerPDU1O7:
        aten01.toggleOutletState(nOut=7)
    elif button == btnPowerPDU1O8:
        aten01.toggleOutletState(nOut=8)


@event(
    [
        btnPowerPDU2O1,
        btnPowerPDU2O2,
        btnPowerPDU2O3,
        btnPowerPDU2O4,
        btnPowerPDU2O5,
        btnPowerPDU2O6,
        btnPowerPDU2O7,
        btnPowerPDU2O8,
    ],
    "Pressed",
)
def btnPowerPDU2EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU2O1:
        aten02.toggleOutletState(nOut=1)
    elif button == btnPowerPDU2O2:
        aten02.toggleOutletState(nOut=2)
    elif button == btnPowerPDU2O3:
        aten02.toggleOutletState(nOut=3)
    elif button == btnPowerPDU2O4:
        aten02.toggleOutletState(nOut=4)
    elif button == btnPowerPDU2O5:
        aten02.toggleOutletState(nOut=5)
    elif button == btnPowerPDU2O6:
        aten02.toggleOutletState(nOut=6)
    elif button == btnPowerPDU2O7:
        aten02.toggleOutletState(nOut=7)
    elif button == btnPowerPDU2O8:
        aten02.toggleOutletState(nOut=8)


@event(
    [
        btnPowerPDU3O1,
        btnPowerPDU3O2,
        btnPowerPDU3O3,
        btnPowerPDU3O4,
        btnPowerPDU3O5,
        btnPowerPDU3O6,
        btnPowerPDU3O7,
        btnPowerPDU3O8,
    ],
    "Pressed",
)
def btnPowerPDU3EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU3O1:
        aten03.toggleOutletState(nOut=1)
    elif button == btnPowerPDU3O2:
        aten03.toggleOutletState(nOut=2)
    elif button == btnPowerPDU3O3:
        aten03.toggleOutletState(nOut=3)
    elif button == btnPowerPDU3O4:
        aten03.toggleOutletState(nOut=4)
    elif button == btnPowerPDU3O5:
        aten03.toggleOutletState(nOut=5)
    elif button == btnPowerPDU3O6:
        aten03.toggleOutletState(nOut=6)
    elif button == btnPowerPDU3O7:
        aten03.toggleOutletState(nOut=7)
    elif button == btnPowerPDU3O8:
        aten03.toggleOutletState(nOut=8)


@event(
    [
        btnPowerPDU4O1,
        btnPowerPDU4O2,
        btnPowerPDU4O3,
        btnPowerPDU4O4,
        btnPowerPDU4O5,
        btnPowerPDU4O6,
        btnPowerPDU4O7,
        btnPowerPDU4O8,
    ],
    "Pressed",
)
def btnPowerPDU4EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU4O1:
        aten04.toggleOutletState(nOut=1)
    elif button == btnPowerPDU4O2:
        aten04.toggleOutletState(nOut=2)
    elif button == btnPowerPDU4O3:
        aten04.toggleOutletState(nOut=3)
    elif button == btnPowerPDU4O4:
        aten04.toggleOutletState(nOut=4)
    elif button == btnPowerPDU4O5:
        aten04.toggleOutletState(nOut=5)
    elif button == btnPowerPDU4O6:
        aten04.toggleOutletState(nOut=6)
    elif button == btnPowerPDU4O7:
        aten04.toggleOutletState(nOut=7)
    elif button == btnPowerPDU4O8:
        aten04.toggleOutletState(nOut=8)


@event(
    [
        btnPowerPDU5O1,
        btnPowerPDU5O2,
        btnPowerPDU5O3,
        btnPowerPDU5O4,
        btnPowerPDU5O5,
        btnPowerPDU5O6,
        btnPowerPDU5O7,
        btnPowerPDU5O8,
    ],
    "Pressed",
)
def btnPowerPDU5EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU5O1:
        aten05.toggleOutletState(nOut=1)
    elif button == btnPowerPDU5O2:
        aten05.toggleOutletState(nOut=2)
    elif button == btnPowerPDU5O3:
        aten05.toggleOutletState(nOut=3)
    elif button == btnPowerPDU5O4:
        aten05.toggleOutletState(nOut=4)
    elif button == btnPowerPDU5O5:
        aten05.toggleOutletState(nOut=5)
    elif button == btnPowerPDU5O6:
        aten05.toggleOutletState(nOut=6)
    elif button == btnPowerPDU5O7:
        aten05.toggleOutletState(nOut=7)
    elif button == btnPowerPDU5O8:
        aten05.toggleOutletState(nOut=8)


@event(
    [
        btnPowerPDU6O1,
        btnPowerPDU6O2,
        btnPowerPDU6O3,
        btnPowerPDU6O4,
        btnPowerPDU6O5,
        btnPowerPDU6O6,
        btnPowerPDU6O7,
        btnPowerPDU6O8,
    ],
    "Pressed",
)
def btnPowerPDU6EventHandler(button: Button, state):
    print(button.Name, state)
    if button == btnPowerPDU6O1:
        aten06.toggleOutletState(nOut=1)
    elif button == btnPowerPDU6O2:
        aten06.toggleOutletState(nOut=2)
    elif button == btnPowerPDU6O3:
        aten06.toggleOutletState(nOut=3)
    elif button == btnPowerPDU6O4:
        aten06.toggleOutletState(nOut=4)
    elif button == btnPowerPDU6O5:
        aten06.toggleOutletState(nOut=5)
    elif button == btnPowerPDU6O6:
        aten06.toggleOutletState(nOut=6)
    elif button == btnPowerPDU6O7:
        aten06.toggleOutletState(nOut=7)
    elif button == btnPowerPDU6O8:
        aten06.toggleOutletState(nOut=8)
