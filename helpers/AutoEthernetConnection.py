#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from typing import Union

# from extronlib.interface import EthernetClientInterface, EthernetServerInterfaceEx, ClientObject
from extronlib.interface import EthernetClientInterface, EthernetServerInterfaceEx
from extronlib.system import Wait, Timer

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger("no", __name__)


class AutoEthernetConnection(EthernetClientInterface):
    def __init__(self,
                 host: str,
                 ipport: int,
                 protocol: str = "TCP",
                 service_port: int = 0,
                 pollstring: str = "",
                 pollfrequency: float = 5,
                 buffer_delay: float = 0,
                 reconnect_interval: float = 5,
                 login: str = "",
                 password: str = ""
                 ):

        super().__init__(host, ipport, Protocol=protocol, ServicePort=service_port)

        self.ip = host
        self.port = ipport

        self.buf_delay = buffer_delay

        self.login = login
        self.password = password

        self.ReceiveData = self._ReceiveData
        self.Connected = self._Connected
        self.Disconnected = self._Disconnected
        self.ConnectedFlag = False

        self.func = dict()
        self.tx_buf = list()

        self.buf_timer = Timer(self.buf_delay, self._bufferTimerHandler)

        self.pollstring = pollstring
        self.pollfrequency = pollfrequency
        self.reconnect_interval = reconnect_interval

        self.pollingtimer = Timer(self.pollfrequency, self._PollingEngine)
        self.autoconnecttimer = Wait(self.reconnect_interval, self._AutoConnect)

    def __del__(self):
        super().Disconnect()

    def connect(self):
        return self.Connect(1)

    def disconnect(self):
        super().Disconnect()

    def set_poll_string(self, pollstring: Union[str, bytes]):
        self.pollstring = pollstring

    def set_poll_frequency(self, pollfrequency):
        self.pollfrequency = pollfrequency
        self.pollingtimer.Change(self.pollfrequency)
        self.pollingtimer.Restart()

    def send(self, string):

        if (self.buf_delay > 0):
            self.tx_buf.append(string)
            if (self.buf_timer.State in ('Paused', 'Stopped')):
                self.buf_timer.Restart()
            dbg.print("Added to buffer")
        else:
            self.Send(string)

    def _bufferTimerHandler(self, tName, tCount):
        dbg.print("Send from buffer: Timer {} - Count {}".format(tName, tCount))
        if (len(self.tx_buf) > 0):
            self._sendFromBuffer()
        else:
            self.buf_timer.Stop()

    def _sendFromBuffer(self):
        msg = self.tx_buf[0]
        self.tx_buf = self.tx_buf[1:]
        self.Send(msg)
        dbg.print("TX to [{}:{}] : [{}]".format(self.ip, self.port, msg))
        dbg.print("Sent from buffer")

    def subscribe(self, action, function):
        self.func[action] = function

    def setpollstring(self, pollstring):
        self.pollstring = pollstring

    def _ReceiveData(self, interface, data):
        dbg.print("RX from [{}:{}] : [{}]".format(self.ip, self.port, data))
        try:
            self.func["ReceiveData"](interface, data)
        except BaseException as err:
            dbg.print("Callback [ReceiveData] error [{}:{}]: {}".format(self.ip, self.port, err))

    def _Connected(self, interface, state):
        dbg.print("Connected to [{}:{}]".format(self.ip, self.port))
        self.ConnectedFlag = True
        self.autoconnecttimer.Cancel()
        self.pollingtimer.Restart()
        try:
            self.func["Connected"](interface, state)
        except BaseException as err:
            dbg.print(
                "Callback [Connected] error [{}:{}]: {}".format(self.ip, self.port, err)
            )

    def _Disconnected(self, interface, state):
        dbg.print("Disconnected from [{}:{}]".format(self.ip, self.port))
        self.pollingtimer.Stop()
        self.ConnectedFlag = False
        self.autoconnecttimer.Restart()
        try:
            self.func["Disconnected"](interface, state)
        except BaseException as err:
            dbg.print(
                "Callback [Disconnected] error [{}:{}]: {}".format(
                    self.ip, self.port, err
                )
            )

    def _PollingEngine(self, timer: Timer, count: int):
        if (self.pollstring != ''):
            self.send(self.pollstring)
            dbg.print('Sended: {}'.format(self.pollstring))
        self.pollingtimer.Restart()

    def _AutoConnect(self):
        dbg.print("Connection - Attempting to connect to [{}:{}]".format(self.ip, self.port))
        try:
            res = self.connect()
            if res in ['Connected', 'ConnectedAlready']:
                dbg.print("Connection result - {} to [{}:{}]".format(res, self.ip, self.port))
            else:
                if self.autoconnecttimer:
                    self.autoconnecttimer.Restart()
        except BaseException as err:
            dbg.print("Rise exception. Connection [{}:{}] error: {}".format(self.ip, self.port, err))


class AutoServerConnection(EthernetServerInterfaceEx):
    def __init__(self,
                 ipport,
                 protocol='TCP',
                 interface='Any',
                 maxclients=5):
        super().__init__(IPPort=ipport, Protocol=protocol, Interface=interface, MaxClients=maxclients)

        self.ReceiveData = self.__ReceiveData
        self.Connected = self.__Connected
        self.Disconnected = self.__Connected
        self.rcv = {}

        self.func = {}

        self.__receiveBuffer = b''
        self.__maxBufferSize = 2048
        self.Subscription = {}

        self.StartListen()

    def __ReceiveData(self, client, data):
        dbg.print("SERVER RX: {}".format(data))
        try:
            self.func["ReceiveData"](client, data)
        except BaseException as err:
            dbg.print("Callback [ReceiveData] error [{}]: {}".format(client, err))

    # def __Connected(self, client: ClientObject, state: str):
    def __Connected(self, client, state: str):
        if state == 'Connected':
            try:
                self.func["Connected"](client, state)
            except BaseException as err:
                dbg.print("Callback [Connected] error [{}]: {}".format(client, err))

            client.Send('Welcome!')
            dbg.print('[+] Client [{}:{}] connected'.format(client.IPAddress, client.ServicePort))
        else:
            try:
                self.func["Disconnected"](client, state)
            except BaseException as err:
                dbg.print("Callback [ReceiveData] error [{}]: {}".format(client, err))

            dbg.print('[-] Client [{}:{}] disconnected'.format(client.IPAddress, client.ServicePort))
            if self.rcv.get(client):
                del self.rcv[client]

    def subscribe(self, action, function):
        self.func[action] = function

    def send(self, string: str):
        # self.sendToAll(string.encode('utf-8'))
        self.sendToAll(string)
        dbg.print("TX to [All]: {}".format(string))

    def sendToAll(self, *msg):
        # txt = " ".join(list(map(str, msg)))
        for iMsg in msg:
            for client in self.Clients:
                # client.Send("{}".format(txt))
                client.Send(str(iMsg))
                # client.Send(msg)
        sleep(.05)
