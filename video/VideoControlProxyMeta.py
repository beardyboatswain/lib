#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod


class VideoControlProxyMeta(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fbCallbackFunctions = list()

    @abstractmethod
    def setTie(self, nOut: int, nIn: int):
        """
        Switch input inN to output outN
        """
        pass

    @abstractmethod
    def getTie(self, nOut: int) -> int:
        """
        Retrun input number switched to output outN
        """
        pass

    @abstractmethod
    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        """
        Set function for FB
        callbackFunction(outNFb: int, inNFb: int) -> None
        inNFb switched to output outNFb
        """

    @abstractmethod
    def executeCallbackFunctions(self, nOut: int, nIn: int):
        """
        Execute all callback functions
        """
        pass


class SwitcherControlProxyMeta(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fbCallbackFunctions = list()

    @abstractmethod
    def setTie(self, nIn: int, nOut: int = 1):
        """
        Switch input inN to output
        """
        pass

    @abstractmethod
    def getTie(self) -> int:
        """
        Retrun input number switched to output
        """
        pass

    @abstractmethod
    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int], None]):
        """
        Set function for FB
        callbackFunction(outNFb: int, inNFb: int) -> None
        inNFb switched to output outNFb
        """

    @abstractmethod
    def executeCallbackFunctions(self, nOut: int, nIn: int):
        """
        Execute all callback functions
        """
        pass
