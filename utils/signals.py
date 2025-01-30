#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
The implementation of the event model

example programm:
file: main.py

import lib.utils.signals as signals

@signals.on()
def foo(signal,params):
    print('hello from main file',signal,params)

signals.emit('__main__',params={'projector':'is on'})
"""


# import threading
class __Mem():
    _mh = []
    _hd = {}


def on(signals=None, debug=None):
    """ decorator function, returns a function with two parameters - a signal 
        and a parameter

    signals=None - executed in any case
    signals='x' - only performed when a certain signal is received
    signals=['x','y'] - executed only when receiving a certain signal from 
                        the list"""
    def decorator(handler):
        __Mem._mh.append(dict(function=handler,
                              module=handler.__module__,
                              signals=signals,
                              debug=debug))
        return handler
    return decorator


def emit(*modules, signal=None, params=None, isthread=False):
    """event triggering function

    module -  required parameter - module name (for main file = main)
    signal - optional parameter, specifies the name of the signal at
             which the function should operate
    params - parameters passed to the function
    isthread - flag indicating whether to perform the function 
               in a separate thread (boolean)"""
    for module in modules:
        for h in __Mem._mh:
            if (module in [h['module'], '*']):
                # if (h['module'] in module) or (module == '*'):
                if signal and h['signals']:
                    if signal in h['signals']:
                        # print(f'func={h["function"]}')
                        # threading is in Disallowed Non-built-in Modules 
                        # threading.Thread(target=h['function'], args=(signal, params)).start() if isthread else h['function'](signal, params)
                        if h['debug']:
                            h['debug'].print('ORIGINAL SIGNAL: S[{}] P[{}]'.format(signal, params))
                        h['function'](signal, params)
                elif h['signals'] and not signal:
                    continue
                else:
                    if h['debug']:
                        h['debug'].print('ORIGINAL SIGNAL: S[{}] P[{}]'.format(signal, params))
                    h['function'](signal, params)
