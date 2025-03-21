#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
import re
import time
import threading

from extronlib.interface import EthernetClientInterface
from extronlib.system import Timer, Wait

from lib.drv.gs.extr_matrix_XTPIICrossPointSeries_v1_12_0_1 import EthernetClass
from lib.helpers.AutoEthernetConnection import AutoEthernetConnection, AutoServerConnection
from lib.video.VideoControlProxyMeta import MatrixControlProxyMeta


from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class MatrixXTPExtron(MatrixControlProxyMeta):
    def __init__(self,
                 device: EthernetClass,
                 inSize: int,
                 outSize: int):
        super().__init__()

        self.device = device

        self.deviceRxConnected = 0

        self.inSize = inSize
        self.outSize = outSize
        self.states = dict()
        for i_out in range(1, self.outSize + 1):
            self.states[i_out] = 0
        self.fbFunctions = list()

        self.device.SubscribeStatus('ConnectionStatus', None, self.ConnectEventHandler)

        self.device.SubscribeStatus("OutputTieStatus", None, self.fbOutputTieStatusEventHandler)
        self.device.Connect()

        self.addFbFunction(self.execute_callback_functions)

        self.refreshFbTimer = Timer(60, self.refreshTies)

    def addFbFunction(self, fbCallbackFunc: Callable[[int, int], None]):
        if callable(fbCallbackFunc):
            self.fbFunctions.append(fbCallbackFunc)
        else:
            raise TypeError("Param 'callbackFb' is not Callable")

    def executeFbFunctions(self, nOut: int, nIn: int):
        dbg.print('executeFbFunctions. out {} - in {}'.format(nOut, nIn))
        for cFunc in self.fbFunctions:
            cFunc(nOut, nIn)

    def refreshTies(self, timer: Timer, count: int):
        self.requestTie()

    def requestTie(self, nOut: int = None):
        # dbg.print("requestTies")
        if nOut:
            self.device.Send("{}!\x0d\x0a".format(nOut))
        else:
            for iOut in range(1, self.outSize + 1):
                self.device.Send("{}!\x0d\x0a".format(iOut))
        self.sendFeedbackForAllOuts()

    def set_tie(self, nOut: int, nIn: int):
        tie_tread = threading.Thread(target=self.device.Set, 
                                     args=("MatrixTieCommand", None, {'Input': str(nIn), 'Output': str(nOut), "Tie Type": "Audio/Video"}))
        tie_tread.start()

        fb_tread = threading.Thread(target=self.requestTie, args=(nOut,))
        fb_tread.start()

        # self.device.Set("MatrixTieCommand", None, {'Input': str(nIn), 'Output': str(nOut), "Tie Type": "Audio/Video"})
        # self.requestTie(nOut=nOut)

    def get_tie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def add_callback_functions(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.callback_functions.append(fbCallbackFunction)

    def execute_callback_functions(self, nOut: int, nIn: int):
        for func in self.callback_functions:
            func(nOut, nIn)

    def ConnectEventHandler(self, command, value, qualifier):
        dbg.print("Connection Handler: XTP {}".format(value))
        if value == "Connected":
            self.refreshTies(None, None)

    def fbOutputTieStatusEventHandler(self, command, value, qualifier):
        # dbg.print("Cmd {} - Val {} - Qal {}".format(command, value, qualifier))
        if (command == "OutputTieStatus"):
            inN = int(value)
            outN = int(qualifier['Output'])
            self.states[outN] = inN
            # dbg.print("Matix State: {}".format(self.states))
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.execute_callback_functions(outN, inN)

    def sendFeedbackForAllOuts(self):
        for iOut in self.states:
            inN = self.states[iOut]
            outN = iOut
            if (0 <= inN <= self.inSize) and (0 < outN <= self.outSize):
                self.execute_callback_functions(outN, inN)


class MatrixXTP(MatrixControlProxyMeta):
    def __init__(self,
                 device: AutoEthernetConnection,
                 in_size: int,
                 out_size: int):
        super().__init__()

        self.device = device
        self.tie_type = '!'
        self.oes = '\x0d\x0a'
        self.deviceRxConnected = 0

        self.in_size = in_size
        self.out_size = out_size
        self.states = dict()
        for i_out in range(1, self.out_size + 1):
            self.states[i_out] = 0

        self.fb_functions = list()

        self.device.subscribe('Connected', self.connection_event_handler)
        self.device.subscribe('Disconnected', self.connection_event_handler)
        self.device.subscribe('ReceiveData', self.rx_event_handler)
        self.device.connect()

        self.match_pattern_tie = re.compile('Out([0-9]{2}) In([0-9]{2}) (Aud|Vid|All)')
        self.match_pattern_password = re.compile("Password:")
        self.match_pattern_loginok = re.compile("Login Administrator")

        self.refresh_fb_timer = Timer(60, self.refresh_fb_timer_event_handler)

    def refresh_fb_timer_event_handler(self, timer: Timer, count: int):
        self.set_verbose()
        self.request_tie()

    def set_verbose(self, verbose: int = 3):
        self.device.send('W{}CV{}'.format(verbose, self.oes))

    def request_tie(self, n_out: int = None):
        '''
        if n_out is None - request all ties
        '''
        if n_out:
            self.device.send("{:02}{}{}".format(n_out, self.tie_type, self.oes))
        else:
            for i_out in range(1, self.out_size + 1):
                self.device.send("{:02}{}{}".format(i_out, self.tie_type, self.oes))
            self.send_feedback()

    def set_tie(self, n_out: int, n_in: int):
        tie_tread = threading.Thread(target=self.device.send, 
                                     args=("{:02}*{:02}{}{}".format(n_in, n_out, self.tie_type, self.oes),))
        tie_tread.start()
        
        update_thread = threading.Thread(target=self.update_state, args=(n_out, n_in))
        update_thread.start()

        fb_tread = threading.Thread(target=self.request_tie, args=(n_out,))
        fb_tread.start()

    def update_state(self, n_out: int, n_in: int):
        if (self.states.get(n_out) == n_in):
            return
        else:
            self.states[n_out] = n_in
            self.send_feedback(n_out)
            self.execute_callback_functions(n_out, self.states[n_out])

    def get_tie(self, nOut: int) -> int:
        return self.states.get(nOut)

    def add_callback_functions(self, callback_function: Callable[[int, int], None]):
        if (callable(callback_function)):
            self.callback_functions.append(callback_function)

    def execute_callback_functions(self, nOut: int, nIn: int):
        for func in self.callback_functions:
            func(nOut, nIn)

    def connection_event_handler(self, command, value, qualifier):
        dbg.print("Connection Handler: XTP {}".format(value))
        if value == "Connected":
            self.refresh_fb_timer_event_handler(None, None)

    def send_feedback(self, n_out: int = None):
        if n_out:
            self.execute_callback_functions(n_out, self.states[n_out])
        else:
            for i_out in self.states:
                n_in = self.states[i_out]
                outN = i_out
                if (0 <= n_in <= self.in_size) and (0 < outN <= self.out_size):
                    self.execute_callback_functions(outN, n_in)

    def rxParser(self, rxLines: str):
        dataLines = rxLines

        for rxLine in dataLines.splitlines():
            match_object_tie = self.match_pattern_tie.search(rxLine)
            if match_object_tie:
                out_new = int(match_object_tie.group(1))
                in_new = int(match_object_tie.group(2))
                self.states[out_new] = in_new
                self.update_state(out_new, in_new)
                continue

            match_object_password = self.match_pattern_password.search(rxLine)
            if match_object_password:
                self.device.send(self.device.password + self.oes)
                continue

            match_object_loginok = self.match_pattern_loginok.search(rxLine)
            if match_object_loginok:
                self.set_verbose()
                self.request_tie()
                continue

    def rx_event_handler(self, interface: EthernetClientInterface, data):
        dbg.print('RX Event Handler. Recieved from {}'.format(interface.IPAddress))
        dbg.print(data)  
        self.rxParser(data.decode())