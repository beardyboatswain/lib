#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod


class CameraControlMeta(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        self.id = int()
        self.ip = str()
        self.port = int()
        self.username = str()
        self.password = str()

        self.pan = None
        self.tilt = None
        self.zoom = None

        self.fbCallbackFunctions = list()

    @abstractmethod
    def move(self, direction: str) -> None:
        """
        Move camera or zoom
        """
        pass

    @abstractmethod
    def getPTZ(self) -> dict:
        """
        Retrun PTZ camera position
        Should return dict {"p":<pan_position>, "t":<tilt_position>, "z":<zoom_position>}
        """
        pass

    @abstractmethod
    def setPTZ(self, ptz: dict) -> None:
        """
        Move camera to PTZ position
        ptz: dict - {"p":<pan_position>, "t":<tilt_position>, "z":<zoom_position>}
        """
        pass

    @abstractmethod
    def callInternalPreset(self, presetId: int) -> None:
        """
        Call preset
        presetId: int - preset id
        """
        pass

    # @abstractmethod
    # def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
    #     """
    #     Set function for FB
    #     callbackFunction(outNFb: int, inNFb: int) -> None
    #     inNFb switched to output outNFb
    #     """

    # @abstractmethod
    # def executeCallbackFunctions(self, nOut: int, nIn: int):
    #     """
    #     Execute all callback functions
    #     """
    #     pass
