#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from typing import Callable
import re

from extronlib.system import Timer, Wait
from extronlib import event

import lib.utils.signals as signals

import lib.helpers.AutoEthernetConnection as AECon
from extronlib.interface import EthernetServerInterfaceEx

from lib.utils.debugger import debuggerNet


class CommandServer(object):
    def __init__(self, ipport: int) -> None:
        self.server = AECon.AutoServerConnection(ipport=ipport)
        self.connected = 0

        self.dbg = debuggerNet("time", __name__)
        self.log = self.dbg.print

        self.server.subscribe('Connected', self.connectEventHandler)
        self.server.subscribe('Disconnected', self.connectEventHandler)
        self.server.subscribe('ReceiveData', self.rxEventHandler)
        self.server.StartListen()

    def rxEventHandler(self, client, data: bytes) -> None:
        rxLine = data.decode()
        self.log('Server Rx: {}'.format(rxLine))

        # self.server.send("<OK>\n")
        msg = ""

        # This simulates a keepalive message received from the client.  Check
        # for missed keepalives in checkTimer()
        if (rxLine.find('ping') > -1):               # Record last keepalive time
            self.connected = time.monotonic()
            msg += "pong" + str(self.connected) + "\n"
            self.server.send(msg.encode('utf8'))

        # This simulates a condition where the server has determined to end the
        # session and close the connection.
        elif (rxLine.find('starttracking') > -1):
            self.log('Start tracking signal received: {}'.format(rxLine))
            msg += 'Start tracking signal received: {}'.format(rxLine)
            self.server.send(msg.encode('utf8'))
            signals.emit('*', signal='tracking', params={'action': 'start'})
        elif (rxLine.find('stoptracking') > -1):
            self.log('Stop tracking signal received: {}'.format(rxLine))
            msg += 'Stop tracking signal received: {}'.format(rxLine)
            self.server.send(msg.encode('utf8'))
            signals.emit('*', signal='tracking', params={'action': 'stop'})

        elif (rxLine.find('disconnect') > -1):                  # Disconnect on data
            self.log('Disconnect signal received.')
            msg += "Chiao!\n"
            self.server.send(msg.encode('utf8'))
            client.Disconnect()
        elif (rxLine.find('@Got:') > -1):                  # Send preset to client
            pass
        else:
            self.server.send(msg.encode('utf8'))

    # def connectEventHandler(self, client: ClientObject, state: str) -> None:
    def connectEventHandler(self, client, state: str) -> None:
        if (state == 'Connected'):
            self.log('Client connected ({}).'.format(client.IPAddress))
            self.server.send('Hello.\n')
            self.connected = time.monotonic()        # Reset the keepalive time
        elif (state == 'Disconnected'):
            self.log('Server/Client disconnected.')
            self.connected = 0                    # Clear the keepalive

    def send_msg(self, msg: str) -> None:
        if (self.connected != 0):
            self.server.send(msg + '\n')
        # self.log("Sended Beam: {}".format(beam))
