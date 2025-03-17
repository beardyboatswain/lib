#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List, Dict

from extronlib import event
from extronlib.device import UIDevice
from extronlib.ui import Button, Label
from extronlib.system import MESet
from extronlib.system import Timer, Wait

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta

from lib.var.states import sStates, sPressed, sReleased

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('time', __name__)


class FixedSizeUniqueList:
    def __init__(self, max_size):
        """
        Инициализирует список LIFO фиксированного размера с уникальными id.
        
        Args:
            max_size (int): Максимальное количество элементов в списке.
        """
        self.max_size = max_size
        self.items = []
    
    def add(self, item_id):
        """
        Добавляет элемент в список. Если элемент уже существует, перемещает его в начало.
        Если список полон, удаляет старейший элемент.
        
        Args:
            item_id (int): Идентификатор элемента для добавления.
        """
        # Проверка, что item_id является целым числом
        if not isinstance(item_id, int):
            raise ValueError("item_id должен быть целым числом")
        
        # Если элемент уже в списке, удаляем его оттуда
        if item_id in self.items:
            self.items.remove(item_id)
        
        # Добавляем элемент в начало списка
        self.items.insert(0, item_id)
        
        # Если размер списка превышает максимальный, удаляем последний элемент
        if len(self.items) > self.max_size:
            self.items.pop()

    def set_max_size(self, new_max_size: int) -> None:
        self.max_size = new_max_size
        self.items = self.items[:new_max_size]
    
    def get_items(self):
        """
        Возвращает список всех элементов в текущем порядке.
        
        Returns:
            list: Список элементов.
        """
        return self.items.copy()
    
    def __str__(self):
        return str(self.items)


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
        self.bv_outs_lifo = FixedSizeUniqueList(1)

        # virtual matrix
        self.vrt_matrix = None
        self.states = dict()

        self.break_time = 0.5

        self.print_states_timer = Timer(20, self.print_states)

    def set_break_time(self, break_time: float) -> None:
        '''
        Set time between switching the break video matrix and the seamless matrix
        '''
        self.break_time = break_time

    def add_break_video_matrix(self, matrix: VideoControlProxyMeta, outs: List[int]) -> None:
        '''
        matrix: VideoControlProxyMeta
        outs: List[int] - list of outputs, connected to seamlesmatrix
        '''
        self.bv_matrix = matrix
        self.bv_matrix.addFbCallbackFunction(self.break_video_matrix_fb)
        self.bv_in_size = self.bv_matrix.inSize
        self.bv_outs = outs
        self.bv_outs_lifo.set_max_size(len(outs))
        for item in outs:
            self.bv_outs_lifo.add(item)

        for i_out in outs:
            self.bv_states[i_out] = self.bv_matrix.getTie(i_out)

    def add_seamless_matrix(self, matrix: VideoControlProxyMeta) -> None:
        self.sm_matrix = matrix
        self.sm_out_size = self.sm_matrix.outSize
        self.sm_matrix.addFbCallbackFunction(self.seamless_matrix_fb)
        for i_out in range(1, self.sm_out_size + 1):
            self.sm_states[i_out] = self.sm_matrix.getTie(i_out)
    
    def add_wiring(self, wiring: Dict[int, int]) -> None:
        '''
        wiring - dict which has next format {seamless_matrix_input: connected_to_break_video_matrix_output, ...}
        '''
        self.wiring = wiring

    def break_video_matrix_fb(self, n_out: int, n_in: int) -> None:
        if (n_out in self.bv_outs):
            self.bv_states[n_out] = n_in
        # dbg.print('BV Matrux state updated: bv_out[{}] < bv_in[{}]'.format(n_out, n_in))
        self.update_states()

    def seamless_matrix_fb(self, n_out: int, n_in: int) -> None:
        self.sm_states[n_out] = n_in
        # dbg.print('SM Matrux state updated: sm_out[{}] < sm_in[{}]'.format(n_out, n_in))
        self.update_states()

    def update_states(self) -> None:
        # for i_out in self.bv_states.keys():
        #     dbg.print('bv_out[{}] < bv_in[{}]'.format(i_out, self.bv_states.get(i_out)))
        # for i_out in self.sm_states.keys():
        #     dbg.print('sm_out[{}] < sm_in[{}]'.format(i_out, self.sm_states.get(i_out)))
        if self.sm_states and self.bv_states:
            for i_out in range(1, self.sm_out_size + 1):
                sm_current_out_state = self.sm_states.get(i_out)
                bv_current_out = self.wiring.get(sm_current_out_state)
                bv_current_out_state = self.bv_states.get(bv_current_out)
                self.states[i_out] = bv_current_out_state
                # dbg.print('sm_out[{}] < sm_in[{}] < bv_out[{}] < bv_in[{}]'.format(i_out,
                #                                                                    sm_current_out_state,
                #                                                                    bv_current_out,
                #                                                                    bv_current_out_state))
                self.executeCallbackFunctions(i_out, self.states[i_out])

    def print_states(self, timer: Timer, count: int) -> None:
        dbg.print('States:')
        for i_out in self.states.keys():
            dbg.print('in[{}] >> out[{}]'.format(self.states.get(i_out), i_out))
        
        dbg.print('Break Video Matrix:')
        for i_out in self.bv_states.keys():
            dbg.print('in[{}] >> out[{}]'.format(self.bv_states.get(i_out), i_out))

        dbg.print('Seamless Matrix:')
        for i_out in self.sm_states.keys():
            dbg.print('in[{}] >> out[{}]'.format(self.sm_states.get(i_out), i_out))

    def setTie(self, nOut: int, nIn: int):
        dbg.print('Set tie on SEAMLESS: in[{}] >> out[{}]'.format(nIn, nOut))
        if self.states.get(nOut) == nIn:
            dbg.print('Tie already set')
        elif nIn in self.bv_states.values():
            dbg.print('Tie is on the one of outputs of bv_matrix')
            # нужно найти, на каком выходе 
            needed_link_bv_out = 0
            for i_out in self.bv_states.keys():
                if self.bv_states.get(i_out) == nIn:
                    needed_link_bv_out = i_out
            dbg.print('BV Matrix: in[{}] >> out[{}]'.format(nIn, needed_link_bv_out))
            # нужно найти, на каком выходе бесподрывника
            needed_link_sm_in = 0
            for i_in in self.wiring.keys():
                if self.wiring.get(i_in) == needed_link_bv_out:
                    needed_link_sm_in = i_in
            dbg.print('BW Matrix out[{}] lincked to SM Matix in[{}]'.format(needed_link_bv_out, needed_link_sm_in))
            # коммутируем бесподрывник
            self.sm_matrix.setTie(nOut, needed_link_sm_in)
            dbg.print('Switch in[{}] >> out[{}] on SM Matrix'.format(needed_link_sm_in, nOut))
        else:
            dbg.print('Tie is NOT on the one of outputs of bv_matrix')
            # нужно найти, какой выход подрывного коммутировался раньше других
            last_out_n = self.bv_outs_lifo.get_items()[-1]
            self.bv_outs_lifo.add(last_out_n)
            dbg.print('Far used out: {}'.format(last_out_n))
            # переключаем на этот выход
            self.bv_matrix.setTie(last_out_n, nIn)
            dbg.print('Switch in[{}] >> out[{}] on BV Matrix'.format(nIn, last_out_n))
            # нужно найти, на каком выходе бесподрывника
            needed_link_sm_in = 0
            for i_in in self.wiring.keys():
                if self.wiring.get(i_in) == last_out_n:
                    needed_link_sm_in = i_in
            dbg.print('BW Matrix out[{}] lincked to SM Matix in[{}]'.format(last_out_n, needed_link_sm_in))
            
            # коммутируем бесподрывник
            @Wait(self.break_time)
            def seamless_matrix_switch():
                self.sm_matrix.setTie(nOut, needed_link_sm_in)
                dbg.print('Switch in[{}] >> out[{}] on SM Matrix'.format(needed_link_sm_in, nOut))

            
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
