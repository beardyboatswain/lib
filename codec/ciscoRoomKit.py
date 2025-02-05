#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, Union
import re

from extronlib import event
from extronlib.device import UIDevice
from extronlib.system import Timer, Wait
from extronlib.ui import Button
from extronlib.interface import SerialInterface

from lib.helpers.AutoEthernetConnection import AutoEthernetConnection
from lib.helpers.AutoSerialConnection import AutoSerialConnection

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)


class ciscoRoomKit(object):
    model_name = 'Cisco RoomKit Plus'

    def __init__(self, dev: Union[AutoEthernetConnection, AutoSerialConnection], id: str = "CiscoCodec"):
        self.dev = dev
        self.h_id = id

        self.rx_buf = str()
        self.standby_st = "On"
        self.mic_mute_st = "On"
        self.presentation_st = 'Off'
        self.presentation_mode_st = 'Off'

        self.fb_callback_functions = dict()

        self.command_eos = '\x0d'
        self.feedback_eos = '\x0d\x0a'
        self.commands = {'Standby': {'get': 'xStatus Standby State',
                                     'set': lambda n_state: 'xCommand Standby {}'.format(n_state),
                                     'register': 'xFeedback register /Status/Standby',
                                     'regexp': '\*s Standby State: (Standby|EnteringStandby|Halfwake|Off)'},
                         'Firmware': {'get': 'xStatus SystemUnit Software Version'},
                         'MicrophonesMute': {'get': 'xStatus Audio Microphones Mute',
                                             'set': lambda n_state:
                                                    'xCommand Audio Microphones {}'.format('Mute' if (n_state == 'On') else 'Unmte'),
                                             'register': 'xFeedback register /Status/Audio/Microphones/Mute',
                                             'regexp': '\*s Audio Microphones Mute: (On|Off)'},
                         'Login': {'regexp': 'login:'},
                         'Password': {'regexp': 'Password:'},
                         'LoginSucceful': {'regexp': '\*r Login successful'},
                         'FirmwareVersion': {'get': 'xstatus SystemUnit Software Version'},
                         'Presentation': {'set': lambda n_state, n_mode='LocalRemote': 'xcommand Presentation {} {}'.format(n_state, 'SendingMode: {}'.format(n_mode) if n_state == 'Start' else ''),
                                          'regexp': '\*s Conference Presentation Mode: (Sending|Receiving|Off)',
                                          'register': 'xFeedback register /Status/Conference/Presentation/Mode'},
                         'PresentationLocalRemote': {'regexp': '\*s Conference Presentation LocalInstance \d{1,2} SendingMode: (LocalOnly|LocalRemote)',
                                                     'register': 'xFeedback register /Status/Conference/Presentation/LocalInstance'},
                         'PresentationStopped': {'regexp': '\*s Conference Presentation LocalInstance \d{1,2} \(ghost=True\):'}
                         }

        self.dev.set_poll_string(self.commands['Standby']['get'] + self.command_eos)
        self.dev.set_poll_frequency(15)

        self.refresh_fb_interval = 60    # ---------------------------------------------- 60
        self.refresh_fb_timer = Timer(self.refresh_fb_interval, self.refresh_rfb)
        # self.refresh_fb_timer.Stop()

    def add_fb_callback_function(self, dict_id: str, fb_callback_function: Callable[[str], None]):
        if callable(fb_callback_function):
            if not self.fb_callback_functions.get(dict_id):
                self.fb_callback_functions[dict_id] = list()
            self.fb_callback_functions[dict_id].append(fb_callback_function)
        else:
            raise TypeError("Param 'fb_callback_function' is not Callable")

    def execute_callback_functions(self, dict_id: str, param: any):
        if self.fb_callback_functions.get(dict_id):
            for cFunc in self.fb_callback_functions.get(dict_id):
                cFunc(param)

    def connect_event_handler(self, interface, state):
        dbg.print("{} {} is {}!".format(self.h_id, self.dev.ip, state))
        if (state == 'Connected'):
            self.send_cmd(" ")

    def start_polling_device(self):
        self.refresh_fb_timer.Restart()
        self.register_feedback()
        self.refresh_rfb(0, 0)

    def send_cmd(self, cmd, eos: str = None):
        if eos:
            self.dev.send(cmd + eos)
        else:
            self.dev.send(cmd + self.command_eos)

    def register_feedback(self):
        for cmd in self.commands.keys():
            if ('register' in self.commands.get(cmd).keys()):
                self.send_cmd(self.commands.get(cmd).get('register'))
                dbg.print('FB Register: {}'.format(self.commands.get(cmd).get('register')))

    def refresh_rfb(self, timer, counter):
        for cmd in self.commands.keys():
            if ('get' in self.commands.get(cmd).keys()):
                self.send_cmd(self.commands.get(cmd).get('get'))

    # todo: проверить что эта функция работает - писал не глядя
    def set(self, cmd: str, value: str) -> None:
        self.send_cmd(self.commands.get(cmd).get('set')(value))

    def rx_parser(self, rx_lines: str):
        for line in rx_lines.split(self.feedback_eos):
            # dbg.print('Parse line [{}]'.format(line))
            for cmd in self.commands.keys():
                if ('regexp' in self.commands.get(cmd).keys()):
                    fb_re_pattern = re.compile(self.commands.get(cmd).get('regexp'))
                    fb_match_object = fb_re_pattern.search(line)
                    if fb_match_object:
                        if (cmd == 'Login'):
                            self.send_cmd(self.dev.login)
                            break
                        elif (cmd == 'Password'):
                            self.send_cmd(self.dev.password)
                            break
                        elif (cmd == 'LoginSucceful'):
                            dbg.print("Login successfull!")
                            self.start_polling_device()
                            break
                        elif (cmd == 'Standby'):
                            new_standby_state = 'Off' if (fb_match_object.group(1) in ('Off', 'EnteringStandby')) else 'On'
                            if (self.standby_st == new_standby_state):
                                pass
                            else:
                                self.standby_st = new_standby_state
                                dbg.print("Standby: {}".format(self.standby_st))
                                self.execute_callback_functions('Standby', self.standby_st)
                            break
                        elif (cmd == 'MicrophonesMute'):
                            mic_mute_st = fb_match_object.group(1)
                            if (self.mic_mute_st == mic_mute_st):
                                pass
                            else:
                                self.mic_mute_st = mic_mute_st
                                dbg.print("Mic Mute: {}".format(self.mic_mute_st))
                                self.execute_callback_functions('MicrophonesMute', self.mic_mute_st)
                                break
                        elif (cmd == 'PresentationLocalRemote'):
                            presentation_mode_st = fb_match_object.group(1)
                            if (self.presentation_mode_st == presentation_mode_st):
                                pass
                            else:
                                if (presentation_mode_st == 'LocalOnly'):
                                    self.presentation_mode_st = presentation_mode_st
                                    self.presentation_st = 'Preview'
                                dbg.print("Presentation:{}, Mode:{}".format(self.presentation_st, self.presentation_mode_st))
                                self.execute_callback_functions('Presentation', self.presentation_mode_st)
                                break
                        elif (cmd == 'Presentation'):
                            presentation_st = fb_match_object.group(1)
                            if (self.presentation_st == presentation_st):
                                pass
                            else:
                                if (presentation_st in ['Sending', 'Receiving']):
                                    self.presentation_mode_st = 'LocalRemote'
                                    self.presentation_st = presentation_st
                                elif (presentation_st == 'Off') and (self.presentation_st == 'Receiving'):
                                    self.presentation_mode_st = 'Off'
                                    self.presentation_st = presentation_st
                                dbg.print("Presentation:{}, Mode:{}".format(self.presentation_st, self.presentation_mode_st))
                                self.execute_callback_functions('Presentation', self.presentation_mode_st)
                                break
                        elif (cmd == 'PresentationStopped'):
                            presentation_st = 'Off'
                            if (self.presentation_st == presentation_st):
                                pass
                            else:
                                self.presentation_mode_st = 'Off'
                                self.presentation_st = 'Off'
                                dbg.print("Presentation:{}, Mode:{}".format(self.presentation_st, self.presentation_mode_st))
                                self.execute_callback_functions('Presentation', self.presentation_mode_st)
                                break

    def rx_event_handler(self, interface, data: bytes):
        # dbg.print("{} recieved:\n{} ".format(self.h_id, data.decode()))
        self.rx_parser(data.decode())


class ciscoRoomKitSerial(ciscoRoomKit):
    def __init__(self, dev: AutoSerialConnection):
        super().__init__(dev)

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', super().rx_event_handler)


class ciscoRoomKitSerialOverEthernet(ciscoRoomKit):
    def __init__(self, dev: AutoEthernetConnection):
        super().__init__(dev)

        self.dev.subscribe('Connected', self.connect_event_handler)
        self.dev.subscribe('Disconnected', self.connect_event_handler)
        self.dev.subscribe('ReceiveData', super().rx_event_handler)

        self.dev.connect()

    # def connectEventHandler(self, interface, state):
    #     dbg.print("Connection Handler: {} {}".format(interface, state))
    #     if (state == 'Connected'):
    #         dbg.print("{}:{} - Connected".format(self.dev.ip, self.dev.port))
    #     elif (state == 'Disconnected'):
    #         dbg.print("{}:{} - Disconnected".format(self.dev.ip, self.dev.port))
