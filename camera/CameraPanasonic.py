#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from abc import ABCMeta, abstractmethod

import re
import json
import urllib.error
import urllib.request
import base64

from extronlib import event, Version
from extronlib.system import Timer, Wait, File
from extronlib.device import UIDevice
from extronlib.ui import Button

import lib.utils.signals as signals

from lib.utils.ipcputils import HexUtils as _h

from lib.drv.gs.gs_pana_camera_AW_HE_UE_Series_v1_6_1_1 import HTTPClass as PanaHTTPClass

from lib.camera.CameraControlMeta import CameraControlMeta

from lib.utils.debugger import debuggerNet as debugger
dbg = debugger('no', __name__)

# UpperCase only
# pan D2F5 (+52f5) - full right +175  - 121 - 1degree
# pan 2D09 (-52F7) - full left  -175  - 121 - 1degree
# tilt 8E38 (+0E38) - full up   +30   - 121 - 1degree
# tilt 5555 (-2AAB) - full down -90   - 121 - 1degree
# zoom 0x0555 - min zoom - wide
# zoom 0x0fff - max zoom - tele


class CameraControlPanasonic(CameraControlMeta):
    ptzCommands = {"Up": "Tilt",
                   "Down": "Tilt",
                   "Left": "Pan",
                   "Right": "Pan",
                   "Wide": "Zoom",
                   "Tele": "Zoom"}

    ptzSpeed = {"Tilt": 15,
                "Pan": 15,
                "Zoom": 25}

    dpadSpeed = {"Up": 20, "Down": 20, "Left": 20, "Right": 20, "Tele": 35, "Wide": 35}

    def __init__(self,
                 id: int,
                 ip: str,
                 port: int,
                 username: str,
                 password: str,
                 model: str = "AW-UE40WEJ") -> None:

        self.dev = PanaHTTPClass(ipAddress=ip, port=port, deviceUsername=username, devicePassword=password, Model=model)

        self.id = id
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.model = model

        self.pan = None
        self.tilt = None
        self.zoom = None

        self.active = False

        self.cameraPanTiltMatchPattern = re.compile("aPC([0-9,A-F]{4})([0-9,A-F]{4})")
        self.cameraZoomMatchPattern = re.compile("gz([0-9,A-F]{3})")

        self.pollInterval = 10
        self.cameraPollTimer = Timer(self.pollInterval, self.pollCamera)

        self.dbg = debugger('time', 'CameraControlPanasonic')

    def send(self, cmd: str) -> None:
        try:
            urlS = "http://{}:{}/cgi-bin/aw_ptz?{}".format(self.ip, self.port, cmd)
            '''
            http://10.213.142.43:80/cgi-bin/aw_ptz?%23APS795D7AC8252&res=1
            http://10.213.142.43:80/cgi-bin/aw_ptz?%23APC&res=1
            http://10.213.142.43:80/cgi-bin/aw_ptz?%23APSD20061231A2&res=1 
            '''
            headers = {}
            headers['Authorization'] = b'Basic ' + base64.b64encode(self.username.encode() + b':' + self.password.encode())

            my_request = urllib.request.Request(urlS, headers=headers)

            opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler())

            resp = opener.open(my_request, timeout=10)

            camAnswer = resp.read()
            dbg.print("URL = <{}>\tANSW = <{}>".format(urlS, camAnswer))
            self.cameraPositionHandler(camAnswer)
        except Exception as err:
            dbg.print("Error: {}".format(err))

    def pollCamera(self, timer: str, count: int):
        self.send("cmd=%23APC&res=1")
        self.send("cmd=%23GZ&res=1")

    def callInternalPreset(self, presetId: int):
        self.send("cmd=%23R{:02}&res=1".format(presetId - 1))

    def cameraPositionHandler(self, rx: str) -> None:
        cCam = 0
        cPan = 0
        cTilt = 0
        cZoom = 0

        rxLines = rx.decode()
        for rxLine in rxLines.splitlines():

            cameraMatchObject = self.cameraPanTiltMatchPattern.search(rxLine)
            if cameraMatchObject:
                cPan = cameraMatchObject.group(1)
                cTilt = cameraMatchObject.group(2)

                dbg.print('Cam[{}] Pan[{}] Tilt[{}]'.format(cCam, cPan, cTilt))
                self.pan = int(cPan, base=16)
                self.tilt = int(cTilt, base=16)

                signals.emit("trackSystemCameraPresetControl",
                             signal="cam_position",
                             params={"Camera": cCam, "Pan": cPan, "Tilt": cTilt})

            cameraMatchObject = self.cameraZoomMatchPattern.search(rxLine)
            if cameraMatchObject:
                cZoom = cameraMatchObject.group(1)
                dbg.print('Cam[{}] Zoom[{}]'.format(cCam, cZoom))
                self.zoom = int(cZoom, base=16)

                signals.emit("trackSystemCameraPresetControl",
                             signal="cam_position",
                             params={"Camera": cCam, "Zoom": cZoom})

    def move(self, direction: str, action: str) -> None:
        """
        Move camera
        directoin: str - One of "Up", "Down", "Left", "Right", "Tele", "Wide"
        action: str - One of "Move" or "Stop"
        """
        PanTiltZoomConstraints = {"Min": 1, "Max": 49}

        speed = self.dpadSpeed.get(direction)
        camCmd = ""

        if (speed < PanTiltZoomConstraints["Min"] or speed > PanTiltZoomConstraints["Max"]):
            dbg.print("Invalid Command for SetPanTilt")
            return
        elif direction in ["Left", "Right", "Up", "Down"]:
            if action == "Stop":
                camCmd = "cmd=%23PTS5050&res=1"
            else:
                if direction == "Left":
                    camCmd = "cmd=%23P{0}&res=1".format(str(50 - speed).zfill(2))
                elif direction == "Right":
                    camCmd = "cmd=%23P{0}&res=1".format(str(50 + speed).zfill(2))
                elif direction == "Up":
                    camCmd = "cmd=%23T{0}&res=1".format(str(50 + speed).zfill(2))
                elif direction == "Down":
                    camCmd = "cmd=%23T{0}&res=1".format(str(50 - speed).zfill(2))
                else:
                    dbg.print("Cam {}, wrong PT command!")
                    return
        elif direction in ["Tele", "Wide"]:
            if action == "Stop":
                camCmd = "cmd=%23Z50&res=1"
            else:
                if direction == "Tele":
                    camCmd = "cmd=%23Z{0}&res=1".format(str(50 + speed).zfill(2))
                elif direction == "Wide":
                    camCmd = "cmd=%23Z{0}&res=1".format(str(50 - speed).zfill(2))

        try:
            dbg.print("CAM MOVE")
            self.send(camCmd)
            if (action == "Stop"):
                @Wait(0.5)
                def RequestNewPosition():
                    self.pollCamera("Poll", 1)
        except BaseException as err:
            dbg.print("Error while sending command to move cam: {}".format(err))

    def getPTZ(self) -> dict:
        return {"p": self.pan, "t": self.tilt, "z": self.zoom}

    def setPTZ(self, ptz: tuple) -> None:
        """
        Move camera to PTZ position
        ptz: dict - {"p":<pan_position>, "t":<tilt_position>, "z":<zoom_position>}
        """
        cPan = ptz.get("p")
        cTilt = ptz.get("t")
        cZoom = ptz.get("z")

        self.dbg.print("Camera {} - SetPTZ: {} ({}, {}, {})".format(self.ip, ptz, cPan, cTilt, cZoom))

        if (cPan and cTilt and cZoom):
            # скорость для пресетов от 0x0 до 0x31 (1 - 49)
            cSpeed = 0x1D

            self.dbg.print("cmd=%23AXZ{:03X}&res=1".format(cZoom))
            self.send("cmd=%23AXZ{:03X}&res=1".format(cZoom))

            if (self.model.find("40") > 0) or (self.model.find("42") > 0) or (self.model.find("50") > 0):
                self.dbg.print("CMD: cmd=%23APS{:04X}{:04X}{:02X}2&res=1".format(cPan, cTilt, cSpeed))
                self.send("cmd=%23APS{:04X}{:04X}{:02X}2&res=1".format(cPan, cTilt, cSpeed))
            elif (self.model.find("20") > 0):
                self.send("cmd=%23APC{}{}&res=1".format(cPan, cTilt))

            @Wait(2)
            def RequestNewPosition():
                self.pollCamera("Poll", 1)

    def setPTZangles(self, ptz: dict) -> None:
        '''
        Set PTZ angles in degrees
        '''
        zoomMax = 20000
        zoomOffset = 800 # default offset 800, было 350

        cZoom = 0x555 + int((ptz["z"] + zoomOffset) * ((0xFFF - 0x555) / zoomMax))
        cPan = int(0x8000 + ((0xD2F5 - 0x8000) / 175) * ptz["p"])
        cTilt = int(0x8000 + ((0x8000 - 0x5555) / 90) * ptz["t"])
        dbg.print("PANA - STREIGT PTZ: {}".format(ptz))
        dbg.print("PANA - STREIGT C PTZ: p<{}>  t<{}>  z<{}>".format(cPan, cTilt, cZoom))
        self.setPTZ({"p": cPan, "t": cTilt, "z": cZoom})


"""
        # UpperCase only
        # pan D2F5 (+52f5) - full right +175  - 121 - 1degree
        # pan 2D09 (-52F7) - full left  -175  - 121 - 1degree
        # tilt 8E38 (+0E38) - full up   +30   - 121 - 1degree
        # tilt 5555 (-2AAB) - full down -90   - 121 - 1degree
        # zoom 0x0555 - min zoom - wide
        # zoom 0x0fff - max zoom - tele

        cCamera = params["PTZ"]["cam"][1]
        ptz = {
            "pan": params["PTZ"]["pan"],
            "tilt": params["PTZ"]["tilt"],
            "zoom": params["PTZ"]["zoom"],
        }

        # ptz = params['ptz']

        zoomMax = 16000
        zoomOffset = 350  # default offset 800

        if params.get("Preset"):
            cPan = ptz["pan"]
            cTilt = ptz["tilt"]
            cZoom = ptz["zoom"]
            dbg.print("PANA - PRESET PTZ: {}".format(ptz))
            dbg.print(
                "PANA - PRESET C PTZ: p<{}>  t<{}>  z<{}>".format(cPan, cTilt, cZoom)
            )
        else:
            # cZoom = int(((ptz['zoom'] - zoomOffset)*(0x0fff - 0x0555))/zoomMax)
            cZoom = 0x555 + int(
                (ptz["zoom"] + zoomOffset) * ((0xFFF - 0x555) / zoomMax)
            )
            cPan = int(0x8000 + ((0xD2F5 - 0x8000) / 175) * ptz["pan"])
            cTilt = int(0x8000 + ((0x8000 - 0x5555) / 90) * ptz["tilt"])
            dbg.print("PANA - STREIGT PTZ: {}".format(ptz))
            dbg.print(
                "PANA - STREIGT C PTZ: p<{}>  t<{}>  z<{}>".format(cPan, cTilt, cZoom)
            )

        dbg.print(
            "CAMERA PAN<0x{:04X}> TILT<0x{:03X}> ZOOM<0x{:04X}>".format(
                cPan, cTilt, cZoom
            )
        )
        callStaightPosition(cCamera, {"pan": cPan, "tilt": cTilt, "zoom": cZoom})

        # Отправить камере zoom
        dbg.print("CMD: #AXZ{:03X}\x0d".format(cZoom))
        cCamera.Send("#AXZ{:03X}\x0d".format(cZoom))
        # Отправить камере pan и tilt
        # #APC[pan][tilt]
        # #APS[PanPos][TiltPos][Speed 0x0-0x1D][SpeedMode 0(slow),2(fast)]
        dbg.print("CMD: #APS{:04X}{:04X}{:02X}2\x0d".format(cPan, cTilt, cSpeed))
        cCamera.Send("#APS{:04X}{:04X}{:02X}2\x0d".format(cPan, cTilt, cSpeed))
        # !!! отправляем сигнал всем заинтересованным в смене камеры
        signals.emit('*', signal='active_cam', params={'cam':camera, 'autopos': True})



    elif signal == "RX":
        # dbg.print("SIG<{}> PARA<{}>".format(signal, params))
        cameraPositionHandler(params["Camera"] - camPortOffset, params["RX"])
"""