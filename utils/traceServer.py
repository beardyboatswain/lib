#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import ProgramLog
from time import sleep
import re


class TcpHelperServer(EthernetServerInterfaceEx):
    def __init__(self, IPPort, end='\r\n'):
        self.end = end
        EthernetServerInterfaceEx.__init__(self,
                                           IPPort,
                                           Protocol='TCP',
                                           Interface='Any')
        self.ReceiveData = self.__ReceiveData
        self.Connected = self.__Connected
        self.Disconnected = self.__Connected
        self.rcv = {}
        self.__receiveBuffer = b''
        self.__maxBufferSize = 2048
        self.Subscription = {}
        self.__matchStringDict = {}
        self.Commands = {
            # 'Help': {'Status': {}},
            # 'Reboot': {'Status': {}},
        }
        self.StartListen()

    def __ReceiveData(self, interface, data):
        # Handle incoming data
        self.__receiveBuffer += data
        index = 0    # Start of possible good data

        # check incoming data if it matched any expected
        # data from device module
        for regexString, CurrentMatch in self.__matchStringDict.items():
            while True:
                result = re.search(regexString, self.__receiveBuffer)
                if result:
                    index = result.start()
                    CurrentMatch['callback'](CurrentMatch['command'],
                                             *result.groups())

                    startBuf = self.__receiveBuffer[:result.start()]
                    endBuf = self.__receiveBuffer[result.end():]

                    self.__receiveBuffer = startBuf + endBuf
                else:
                    break

        if index:
            # Clear out any junk data that came in before any good matches.
            self.__receiveBuffer = self.__receiveBuffer[index:]
        else:
            # In rare cases, the buffer could be filled with garbage quickly.
            # Make sure the buffer is capped.  Max buffer size set in init.
            self.__receiveBuffer = self.__receiveBuffer[-self.__maxBufferSize:]

    def __Connected(self, client, state):
        if state == 'Connected':
            from usr.dev.dev import mIPCP
            self.SendAll('Welcome to {} ({})'.format(
                mIPCP.ModelName, mIPCP.SerialNumber))
            # client.Send()
            ProgramLog('[+] Client [{}:{}] connected'.format(
                client.IPAddress, client.ServicePort), 'info')
        else:
            ProgramLog('[-] Client [{}:{}] disconnected'.format(
                client.IPAddress, client.ServicePort), 'info')
            if self.rcv.get(client):
                del self.rcv[client]

    def __req(self, client):
        client.Send('>')

    def __parse(self, client):
        data = self.rcv[client].decode().rstrip().lower()
        if data in ('bye', 'exit', 'quit',):
            client.Disconnect()
            return
        self.__req(client)
        self.rcv[client] = b''

    def SubscribeStatus(self, command, regex_string, callback):
        if regex_string not in self.__matchStringDict:
            self.__matchStringDict[regex_string] = {'command': command,
                                                    'callback': callback,
                                                    'args': None}

            if command not in self.Subscription:
                self.Subscription[command] = {'method': {}}
                Subscribe = self.Subscription[command]
                Method = Subscribe['method']
                Method['callback'] = callback
                Method['qualifier'] = None

    def SendAll(self, *msg):
        txt = ' '.join(list(map(str, msg)))
        for client in self.Clients:
            client.Send("\x02{}\x03".format(txt))
        sleep(.05)


Server = TcpHelperServer(5000)


def Print(*args):
    Server.SendAll(*args)
    # print(*args)
