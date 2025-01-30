#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread
import time


class Timeline(Thread):
    def __init__(self, interval, cbfunction, name="nnn"):
        super().__init__(name="TL{}".format(name))
        assert interval > 0, "Timeline: wrong timer interval"
        self.interval = interval
        self.cbfunction = cbfunction  # return callback time
        self.name = name
        self.alive = True
        self.start_time = None
        self.stop_fl = False
        self.interval_new = False
        self.pause_time = None
        self.interval_back = None
        self.actions = []

    def stamp(self, action="Action", diff=None):
        # print("{:10}: {:0.3f} {:0.3f}".format(action, time.time(), (diff if (diff) else 0)))
        pass

    def run(self):
        while self.alive:
            self.start_time = time.time()
            while not self.stop_fl:
                if self.stop_fl:
                    break

                if time.time() - self.start_time > self.interval:
                    real_interval = time.time() - self.start_time

                    if self.pause_time:
                        self.interval = self.interval_back
                        self.pause_time, self.interval_back = 0, 0

                    # try:
                    self.cbfunction(time.time())
                    self.stamp("Timer", real_interval)
                    self.actions.append(real_interval)
                    # except BaseException as err:
                    #     print("Error {}".format(err))

                    if self.interval_new:
                        self.interval = self.interval_new
                        self.interval_new = False

                    break

    def change(self, interval):
        self.interval_new = interval
        self.stamp("Change", time.time() - self.start_time)

    def pause(self):
        self.stop_fl = True
        self.pause_time = self.start_time + self.interval - time.time()
        self.stamp("Pause", time.time() - self.start_time)

    def resume(self):
        if self.pause_time:
            self.interval_back = self.interval
            self.interval = self.pause_time
            self.stop_fl = False
            self.stamp("Resume", time.time() - self.start_time)
        else:
            self.restart()

    def restart(self):
        self.start_time = time.time()
        self.stop_fl = False
        self.stamp("Restart", time.time() - self.start_time)

    def stop(self):
        self.stop_fl = True
        self.stamp("Stop", time.time() - self.start_time)

    def delete(self):
        self.stop()
        self.alive = False
        self.stamp("Delete", time.time() - self.start_time)

        # print time intervals and average deviation
