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
    def setPTZangles(self, ptz: dict) -> None:
        '''
        Set PTZ angles in degrees
        Recalc degrees into cam representation and call self.setPTZ()
        '''
        pass
        # cZoom = 0x555 + int((ptz["z"] + zoomOffset) * ((0xFFF - 0x555) / zoomMax))
        # cPan = int(0x8000 + ((0xD2F5 - 0x8000) / 175) * ptz["p"])
        # # cTilt = int(0x8000 + ((0x8000 - 0x5555) / 90) * ptz["t"])
        # self.setPTZ({"p": cPan, "t": cTilt, "z": cZoom})

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
