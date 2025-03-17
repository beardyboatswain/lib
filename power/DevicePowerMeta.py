#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod

# todo: move implementation of add_fb_callback_function and execute_callback_functions to DevicePowerMeta
# todo: lest of callbacks with params to __init__
class DevicePowerMeta(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fbCallbackFunctions = list()

    @abstractmethod
    def set_power(self, nPower: str) -> None:
        """
        Set power state
        nPower: str - new power state, "On" or "Off"
        """
        pass

    @abstractmethod
    def tgl_power(self) -> None:
        """
        Toggle power state
        """
        pass

    @abstractmethod
    def get_power(self) -> str:
        """
        Retrun power state: "On" or "Off"
        """
        pass

    @abstractmethod
    def add_fb_callback_function(self, fbCallbackFunction: Callable[[str], None]):
        """
        Set function for FB
        callbackFunction(powerState: str) -> None
        When power state changes object call callbackFunction(actualPowerState)
        """

    @abstractmethod
    def execute_callback_functions(self):
        """
        Execute all callback functions
        """
        pass
