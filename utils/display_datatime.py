#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extronlib.device import UIDevice
from extronlib.ui import Label
from extronlib.system import Timer

import time

month = {
    "ru": {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    },
    "en": {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    },
}


class ShowDateTime:
    renewDateTemer = None
    renewTimeTimer = None

    def __init__(self,
                 UIDev: UIDevice,
                 dateLabelID: int = 0,
                 timeLabelID: int = 0,
                 renewTimeIinterval: int = 5,
                 lang: str = "ru"):
        self.UIDev = UIDev
        self.renewTimeIinterval = renewTimeIinterval if renewTimeIinterval > 0 else 1
        if dateLabelID > 0:
            self.dateLabel = Label(self.UIDev, dateLabelID)

            def renewDateLabel(timer, count):
                self.dateLabel.SetText(
                    month[lang][int(time.strftime("%m"))] + ", " + time.strftime("%d")
                )

            ShowDateTime.renewDateTemer = Timer(self.renewTimeIinterval, renewDateLabel)
            renewDateLabel(0, 0)

        if timeLabelID > 0:
            self.timeLabel = Label(self.UIDev, timeLabelID)

            def renewTimeLabel(timer, count):
                self.timeLabel.SetText(time.strftime("%H:%M"))

            ShowDateTime.renewTimeTimer = Timer(self.renewTimeIinterval, renewTimeLabel)
            renewTimeLabel(0, 0)
