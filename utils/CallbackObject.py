#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable


class CallbackObject():
    """
    Add to class ability to store and execute callback functions.
    """
    def __init__(self):
        self.callbackMethods = list()

    def addCallback(self, id: int, method: Callable, *args):
        if id:
            self.callbackMethods.append({"id": id, "method": method, "args": args})

    def executeCallback(self, id: int = None):
        for cm in self.callbackMethods:
            if (id):
                if (cm["id"] == id):
                    cm["method"](*cm["args"])
            else:
                cm["method"](*cm["args"])
