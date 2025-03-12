#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class IPDev(object):
    '''
    # Usefull interface for ip devices
    # example
    moxa = IPDev("192.168.10.12", 23)

    print(moxa.port)
    print(moxa.ip)

    moxa.ip = "10.12.123.22"
    moxa.port = 4022

    print(moxa.ip)
    print(moxa.port)
    '''
    def __init__(self, ip: str, port: int, login: str = None, password: str = None) -> None:
        self._ip = ip
        self._port = port
        self._login = login
        self._password = password

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):
        # написать проверку ip-адреса по регулярке
        if (ip):
            self._ip = ip
        else:
            raise TypeError("Missing required positional argument: ip={}".format(ip))

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        # написать проверку порта (чтобы в указанные рамки попадал)
        if (port):
            self._port = port
        else:
            raise TypeError("Missing required positional argument: port={}".format(port))

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, login):
        if (login):
            self._login = login
        else:
            raise TypeError("Missing required positional argument: login={}".format(login))

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if (password):
            self._password = password
        else:
            raise TypeError("Missing required positional argument: password={}".format(password))


class HexUtils:
    def line_string_to_hexstring(_t: str) -> str:
        """Return HEX representation of _t"""
        toH = ""
        for i in _t:
            toH += "\\x" + "{:02X}".format(ord(i))
        return toH
    
    def line_bytes_to_hexstring(s: bytes) -> str:
        '''
        s = b'\xaa\x14\x01\x01 6' 
        '''
        return ''.join(f'\\x{c:02x}' for c in s) 
    
    def hexToString(x: int, frmt: str = "") -> str:
        if (frmt == ""):
            return "{:X}".format(0xD2F5)
        elif (frmt == "0x"):
            return "0x{:X}".format(0xD2F5)
