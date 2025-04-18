#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod


class MatrixControlProxyMeta(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.callback_functions = list()
        self.inSize = 0
        self.outSize = 0
        self.states = dict()

    @abstractmethod
    def set_tie(self, n_out: int, n_in: int):
        """
        Switch input inN to output outN
        """
        pass

    @abstractmethod
    def get_tie(self, n_out: int) -> int:
        """
        Retrun input number switched to output outN
        """
        pass

    @abstractmethod
    def add_callback_functions(self, callback_function: Callable[[int, int], None]):
        """
        Set function for FB
        callbackFunction(outNFb: int, inNFb: int) -> None
        inNFb switched to output outNFb
        """

    @abstractmethod
    def execute_callback_functions(self, n_out: int, nIn: int):
        """
        Execute all callback functions
        """
        pass


VideoControlProxyMeta = MatrixControlProxyMeta
'''
VideoControlProxyMeta is the previous name for meta-class for maatrix control
This alias was made for backward compatibility.
Use MatrixControlProxyMeta instead of VideoControlProxyMeta in the future.
'''


class SwitcherControlProxyMeta(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fb_callback_functions = list()

    @abstractmethod
    def set_tie(self, n_in: int, n_out: int = 1):
        """
        Switch input inN to output
        """
        pass

    @abstractmethod
    def get_tie(self, n_out: int) -> int:
        """
        Return input number switched to output
        """
        pass

    @abstractmethod
    def add_fb_callback_function(self, fb_callback_function: Callable[[int], None]):
        """
        Set function for FB
        callbackFunction(outNFb: int, inNFb: int) -> None
        inNFb switched to output outNFb
        """

    @abstractmethod
    def execute_callback_functions(self, n_out: int, n_in: int):
        """
        Execute all callback functions
        """
        pass
