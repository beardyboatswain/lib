#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List, Dict

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label
from extronlib.system import MESet

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('time', __name__)


class PseudoSeamless(VideoControlProxyMeta):
    def __init__(self):
        super().__init__()

        self.wiring = dict()

        # seamless matrix
        self.sm_matrix = None
        self.sm_states = dict()
        self.sm_out_size = 0

        # matrix with break video switching
        self.bv_matrix = None
        self.bv_in_size = 0
        self.bv_outs = list()
        self.bv_states = dict()

        # virtual matrix
        self.vrt_matrix = None
        self.states = dict()

    def add_break_video_matrix(self, matrix: VideoControlProxyMeta, outs: List[int]) -> None:
        '''
        matrix: VideoControlProxyMeta
        outs: List[int] - list of outputs, connected to seamlesmatrix
        '''
        self.bv_matrix = matrix
        self.bv_matrix.addFbCallbackFunction(self.break_video_matrix_fb)
        self.bv_in_size = self.bv_matrix.inSize
        self.bv_outs = outs
        for i_out in outs:
            self.bv_states[i_out] = self.bv_matrix.getTie(i_out)

    def add_seamless_matrix(self, matrix: VideoControlProxyMeta) -> None:
        self.sm_matrix = matrix
        self.sm_out_size = self.sm_matrix.outSize
        for i_out in range(1, self.sm_out_size + 1):
            self.sm_states[i_out] = self.sm_matrix.getTie(i_out)
    
    def add_wiring(self, wiring: Dict[int, int]) -> None:
        '''
        wiring - dict which has next format {seamless_matrix_input: connected_to_break_video_matrix_output, ...}
        '''
        self.wiring = wiring

    def break_video_matrix_fb(self, n_out: int, n_in: int) -> None:
        self.bv_states[n_out] = n_in
        self.update_states()

    def seamless_matrix_fb(self, n_out: int, n_in: int) -> None:
        self.sm_states[n_out] = n_in
        self.update_states()

    def update_states(self) -> None:
        if self.sm_states and self.bv_states:
            for i_out in range(1, self.sm_out_size + 1):
                sm_current_out_state = self.sm_states.get(i_out)
                bv_current_out = self.wiring.get(sm_current_out_state)
                bv_current_out_state = self.bv_states.get(bv_current_out)
                self.states[i_out] = bv_current_out_state
                dbg.print('sm_out[{}] < sm_in[{}] < bv_out[{}] < bv_in[{}]'.format(i_out,
                                                                                   sm_current_out_state,
                                                                                   bv_current_out,
                                                                                   bv_current_out_state))
                self.executeCallbackFunctions(i_out, self.states[i_out])

    def setTie(self, nOut: int, nIn: int):
        pass
        # todo
        # смотрим, какой вход бесподрывника идет на выход
        # если этот вход не совпадает с новым, то смотрим есть ли нужный линк уже на одном из входов
        # и переключаем его
        # иначе занимаем вход бесподрывника который давно не комутировался (нужен LIFO) 
        # затем переключаем этот вход на выход
        # ина
            
    def getTie(self, nOut: int) -> int:
        """
        Retrun input number switched to output outN
        """
        return self.states.get(nOut)

    def addFbCallbackFunction(self, fbCallbackFunction: Callable[[int, int], None]):
        if (callable(fbCallbackFunction)):
            self.fbCallbackFunctions.append(fbCallbackFunction)

    def executeCallbackFunctions(self, nOut: int, nIn: int):
        for func in self.fbCallbackFunctions:
            func(nOut, nIn)
