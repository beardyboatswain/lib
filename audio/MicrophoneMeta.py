#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod


class MicrophoneWithBeamsMeta(object):
    """
    Meta Class for controling Microphones which have beamd
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fbCallbackFunctions = list()

    @abstractmethod
    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[list, int, int], None]):
        """
        Set function for FB
        callbackFunction(outNFb: int, inNFb: int) -> None
        inNFb switched to output outNFb
        """

    @abstractmethod
    def executeCallbackFunctions(self):
        """
        Execute all callback functions and send Main Voice Vector as paramtr (list of 4 float)
        """
        pass
