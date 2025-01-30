#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from typing import Union


# from extronlib.interface import EthernetClientInterface, EthernetServerInterfaceEx, ClientObject
from extronlib.interface import SerialInterface
from extronlib.system import Wait, Timer

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger("no", __name__)


class AutoSerialConnection(SerialInterface):
    '''
            **Arguments**:
        * **Host** (*extronlib.device*) - handle to Extron device class that instantiated this interface class
        * **Port** (*string*) - port name (e.g.  '*COM1*', '*IRS1*')
        * (*optional*) **Baud** (*int*) - baudrate
        * (*optional*) **Data** (*int*) - number of data bits
        * (*optional*) **Parity** (*string*) - '*None*', '*Odd*' or '*Even*'
        * (*optional*) **Stop** (*int*) - number of stop bits
        * (*optional*) **FlowControl** (*string*) - '*HW*', '*SW*', or '*Off*'
        * (*optional*) **CharDelay** (*float*) - time between each character sent to the connected device
        * (*optional*) **Mode** (*string*) - mode of the port, '*RS232*', '*RS422*' or '*RS485*'
    '''

    def __init__(self,
                 host: str,
                 port: str,
                 baud: int = 9600,
                 data: int = 8,
                 parity: str = 'None',
                 stop: int = 1,
                 flowcontrol: str = 'Off',
                 chardelay: float = 0,
                 mode: str = 'RS232',
                 buffer_delay: int = 0,
                 pollstring: str = '',
                 pollfrequency: int = 60,
                 login: str = '',
                 password: str = ''
                 ):

        super().__init__(Host=host,
                         Port=port,
                         Baud=baud,
                         Data=data,
                         Parity=parity,
                         Stop=stop,
                         FlowControl=flowcontrol,
                         CharDelay=chardelay,
                         Mode=mode
                         )

        self.host = host
        self.port = port
        self.baud = baud
        self.data = data
        self.parity = parity
        self.stop = stop
        self.flowcontrol = flowcontrol
        self.chardelay = chardelay
        self.mode = mode
        self.login = login
        self.password = password

        self.ReceiveData = self._ReceiveData
        self.Online = self._Connected
        self.Offline = self._Disconnected

        self.func = dict()
        self.tx_buf = list()

        self.buf_delay = buffer_delay
        self.buf_timer = Timer(self.buf_delay, self._bufferTimerHandler)

        self.poll_string = pollstring
        self.poll_frequency = pollfrequency

        self.polling_timer = Timer(self.poll_frequency, self._PollingEngine)
        self.polling_timer.Stop()

    def send(self, string):
        if (self.buf_delay > 0):
            self.tx_buf.append(string)
            if (self.buf_timer.State in ('Paused', 'Stopped')):
                self.buf_timer.Restart()
            dbg.print("Added to buffer")
        else:
            self.Send(string)

    def _bufferTimerHandler(self, timer_name, timer_count):
        dbg.print("Send from buffer: Timer {} - Count {}".format(timer_name, timer_count))
        if (len(self.tx_buf) > 0):
            self._sendFromBuffer()
        else:
            self.buf_timer.Stop()

    def _sendFromBuffer(self):
        msg = self.tx_buf[0]
        self.tx_buf = self.tx_buf[1:]
        self.Send(msg)
        dbg.print("TX to [{}] : [{}]".format(self.port, msg))
        dbg.print("Sent from buffer")

    def subscribe(self, action, function):
        self.func[action] = function

    def set_poll_string(self, pollstring):
        self.poll_string = pollstring

    def set_poll_frequency(self, pollfrequency):
        self.poll_frequency = pollfrequency
        self.polling_timer.Change(self.poll_frequency)
        self.polling_timer.Restart()

    def _ReceiveData(self, interface, data):
        dbg.print("RX from [{}] : [{}]".format(self.port, data))
        try:
            self.func["ReceiveData"](interface, data)
        except BaseException as err:
            dbg.print("Callback [ReceiveData] error [{}]: {}".format(self.port, err))

    def _Connected(self, interface, state):
        dbg.print("Connected to [{}]".format(self.port))
        self.ConnectedFlag = True
        self.polling_timer.Restart()
        try:
            self.func["Connected"](interface, state)
        except BaseException as err:
            dbg.print("Callback [Connected] error [{}]: {}".format(self.port, err))

    def _Disconnected(self, interface, state):
        dbg.print("Disconnected from [{}]".format(self.port))
        self.ConnectedFlag = False
        self.polling_timer.Stop()
        try:
            self.func["Disconnected"](interface, state)
        except BaseException as err:
            dbg.print("Callback [Disconnected] error [{}]: {}".format(self.port, err))

    def _PollingEngine(self, timer: Timer, count: int):
        if (self.poll_string != ''):
            self.send(self.poll_string)
            self.polling_timer.Restart()
        else:
            self.polling_timer.Stop()
