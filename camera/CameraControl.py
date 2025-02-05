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
from extronlib.system import Timer, Wait, File, MESet
from extronlib.device import UIDevice
from extronlib.ui import Button

import lib.utils.signals as signals
from lib.utils.system_init import InitModule
from lib.var.states import sPressed, sReleased, sHeld, sTapped, sStates

from lib.utils.ipcputils import hexUtils as _h

from lib.video.VideoControlProxyMeta import VideoControlProxyMeta
from lib.camera.CameraControlMeta import CameraControlMeta

import lib.utils.debugger as debugger
dbg = debugger.debuggerNet('no', __name__)


class CameraControlProcessor():
    def __init__(self, firstPreset: int, presetNumber: int, presetFileName: str = "cam_presets_panas.json"):
        """
        firstPreset: int - ID for main preset (general view) Button
        presetNumber: int - number of presets (and preset Buttons)
        """
        self.firstPreset = firstPreset
        self.presetNumber = presetNumber

        self.presets = {}
        self.presetsFileName = presetFileName

        self.cams = dict()
        self.activeCam = None

        self.camInputs = dict()
        self.activeCamOuts = list()

        self.camSwitcher = None

        # add toggle button "Immediately OnAir"
        self.autoCamOnAirFl = True

        # callback functions for active camera commutation
        self.__callbackFbActiveCam = list()

        if File.Exists(self.presetsFileName):
            self.loadPresetsFromFile()
        else:
            for iPreset in range(self.firstPreset, self.firstPreset + self.presetNumber):
                self.presets[iPreset] = {
                    "camera": None,
                    "pan": None,
                    "tilt": None,
                    "zoom": None,
                }
            dbg.print("Generated: {}".format(self.presets))
            self.savePresetsToFile()

    def getFirstPreset(self) -> int:
        """
        Returns the first preset number
        """
        return self.firstPreset

    def getPresetNumber(self):
        """
        Return number of presets
        """
        return self.presetNumber

    def addCamera(self, camera: CameraControlMeta, videoMatrixIn: int = -1) -> None:
        """
        camera: CameraControlMeta - camera object
        videoMatrixIn: int - number of video input for camera on matrix switcher
        """
        self.cams[camera.id] = camera
        self.camInputs[camera.id] = videoMatrixIn

    def setActiveCamera(self, camID: int) -> None:
        if (camID in self.cams.keys()):
            self.activeCam = self.cams.get(camID)
            self.execCallbackFbActiveCam()
            if self.autoCamOnAirFl:
                self.switchCamera(self.activeCam.id)
            return self.activeCam
        else:
            dbg.print("Wrong camID ({}). No such camera in CameraControlProcessor.".format(camID))
            return None

    def addCallbackFbActiveCam(self, callbackFunction: Callable[[CameraControlMeta], None]):
        if callable(callbackFunction):
            self.__callbackFbActiveCam.append(callbackFunction)
        else:
            raise TypeError("Param 'fbCallbackFunction' is not Callable")

    def execCallbackFbActiveCam(self):
        for cFunc in self.__callbackFbActiveCam:
            cFunc(self.activeCam)

    def getCamera(self, camId: int) -> CameraControlMeta:
        if self.cams.get(camId):
            return self.cams.get(camId)
        else:
            return None

    def getCameraBySwitchInput(self, input: int) -> CameraControlMeta:
        for iCamID in self.camInputs:
            if (self.camInputs[iCamID] == input):
                return self.getCamera(iCamID)
        return None

    def getCamerasNumber(self) -> None:
        return len(list(self.cams.keys()))

    def getCamerasId(self) -> list:
        """
        Returns list of int - ids of cameras
        """
        return list(self.cams.keys())

    def savePresetsToFile(self) -> None:
        dbg.print("Save presets: {}".format(self.presets))
        try:
            fileForStore = File(self.presetsFileName, "w")
            json.dump(self.presets, fileForStore)
        except BaseException as err:
            dbg.print("Save error: {}".format(err))
        finally:
            fileForStore.close()

    def loadPresetsFromFile(self) -> None:
        try:
            fileForLoad = File(self.presetsFileName, "r")
            loadedPresets = json.load(fileForLoad)
            # convert json presets keys from str to int
            for iP in loadedPresets:
                self.presets[int(iP)] = loadedPresets[iP]
            dbg.print("Success load presets: {}".format(self.presets))
        except BaseException as err:
            dbg.print("Load error: {}".format(err))
        finally:
            fileForLoad.close()

    def storePreset(self, camId: int, presetId: int) -> bool:
        dbg.print("Save PRESET{} CAM{}".format(presetId, camId))

        if self.cams.get(camId) and self.presets.get(presetId):
            ptz = self.cams[camId].getPTZ()

            self.presets[presetId] = {"camera": camId,
                                      "pan": ptz["p"],
                                      "tilt": ptz["t"],
                                      "zoom": ptz["z"]}
            self.savePresetsToFile()
            return True
        else:
            dbg.print("Preset save failed!")
            return False

    def callPreset(self, presetId: int) -> None:
        if self.presets.get(presetId):
            presetData = self.presets.get(presetId)
            dbg.print("CALL PR[{}] = {}".format(presetId, presetData))
            if self.cams.get(presetData.get("camera")):
                self.cams[presetData.get("camera")].setPTZ({"p": presetData.get("pan"),
                                                            "t": presetData.get("tilt"),
                                                            "z": presetData.get("zoom")})
                dbg.print("PRECET CALL SWITCHING: Cam <{}>, type <{}>".format(presetData.get("camera"), type(presetData.get("camera"))))
                # self.switchCamera(self.cams.get(presetData.get("camera")))
                self.switchCamera(presetData.get("camera"))
        else:
            dbg.print("Error while calling preset: {}. No such preset.".format(presetId))

    def callInternalPreset(self, presetId: int) -> None:
        self.activeCam.callInternalPreset(presetId)
        self.switchCamera(self.activeCam)

    def fbFromSwitcher(self, nOut: int, nIn: int) -> None:
        dbg.print("CAMERA - Out <{}> - In <{}>".format(nOut, nIn))
        if (self.autoCamOnAirFl and (nOut in self.activeCamOuts)):
            self.activeCam = self.getCameraBySwitchInput(nIn)
            self.execCallbackFbActiveCam()

    def addCamSwitcher(self, camSw: VideoControlProxyMeta):
        self.camSwitcher = camSw
        self.camSwitcher.addFbCallbackFunction(self.fbFromSwitcher)

    def addCamSwitcherActiveCamOutput(self, videoOutputs: list) -> None:
        self.activeCamOuts.extend(videoOutputs)

    def switchCamera(self, camId: int):
        camIn = self.camInputs.get(int(camId))
        dbg.print("Trying to switch camera <{}>, input <{}>".format(camId, camIn))
        if (camIn > 0):
            for iOut in self.activeCamOuts:
                dbg.print("Trying to switch camera <{}>, input <{}> -> output <{}>".format(camId, camIn, iOut))
                self.camSwitcher.setTie(nOut=iOut, nIn=camIn)


class CameraControlPanel(object):
    def __init__(self, uiHost: UIDevice, camProcessor: CameraControlProcessor):
        self.uiHost = uiHost
        self.camProcessor = camProcessor
        self.camProcessor.addCallbackFbActiveCam(self.fbCamActive)

        self.dpadBtns = list()
        self.dpadSpeed = {"Up": 20, "Down": 20, "Left": 20, "Right": 20, "Tele": 35, "Wide": 35}

        self.camSelectBtns = list()
        self.camSelectBtnsME = None

        # active cam at the moment
        self.activeCam = None

        # cam, we send cmd to move, use it for stop cmd
        self.movingCam = None

        self.presetBtns = list()
        self.presetSavedBtn = None

    def addDPad(self,
                upBtnId: int,
                downBtnId: int,
                leftBtnId: int,
                rightBtnId: int,
                teleBtnId: int,
                wideBtnId: int) -> None:

        self.dpadBtnID = {"Up": upBtnId,
                          "Down": downBtnId,
                          "Left": leftBtnId,
                          "Right": rightBtnId,
                          "Tele": teleBtnId,
                          "Wide": wideBtnId}

        for iDirect in self.dpadBtnID:
            newButton = Button(self.uiHost, self.dpadBtnID.get(iDirect))
            setattr(newButton, "direction", iDirect)
            self.dpadBtns.append(newButton)

        @event(self.dpadBtns, sStates)
        def camDPadBtnsEventHandler(btn: Button, state: str):
            if state == sPressed:
                btn.SetState(1)
                if self.activeCam:
                    # todo проверить что не меняется при смене пресета на другую камеру
                    self.movingCam = self.activeCam
                    self.activeCam.move(direction=getattr(btn, "direction"), action="Move")
            elif state == sReleased:
                btn.SetState(0)
                if self.movingCam:
                    self.movingCam.move(direction=getattr(btn, "direction"), action="Stop")
                else:
                    self.activeCam.move(direction=getattr(btn, "direction"), action="Stop")

    def addCameraSelector(self, firstCamBtnId: int) -> None:
        btnSelectorId = firstCamBtnId

        for idCam in self.camProcessor.getCamerasId():
            newButton = Button(self.uiHost, btnSelectorId)
            newButton.SetState(0)
            setattr(newButton, "camID", idCam)
            self.camSelectBtns.append(newButton)
            btnSelectorId += 1

        self.camSelectBtnsME = MESet(self.camSelectBtns)

        @event(self.camSelectBtns, sStates)
        def camSelectBtnsEventHandler(btn: Button, state: str):
            if state == sReleased:
                self.setCamActive(getattr(btn, "camID"))

    def setCamActive(self, camID: int):
        self.camProcessor.setActiveCamera(camID)

    def fbCamActive(self, cam: CameraControlMeta):
        self.activeCam = cam
        if (self.activeCam):
            for iBtn in self.camSelectBtns:
                if (getattr(iBtn, "camID") == self.activeCam.id):
                    self.camSelectBtnsME.SetCurrent(iBtn)

    def addPresetButtons(self, presetSavedProbeID: int):
        """
        presetSavedProbeID: int - ID for "Preset Saved" indicator Button
        """
        self.presetSavedBtn = Button(self.uiHost, presetSavedProbeID)
        self.presetSavedBtn.SetVisible(False)

        firstPresetID = self.camProcessor.getFirstPreset()
        lastPresetID = self.camProcessor.getFirstPreset() + self.camProcessor.getPresetNumber()

        for iBtnId in range(firstPresetID, lastPresetID):
            self.presetBtns.append(Button(self.uiHost, iBtnId, holdTime=2))

        @event(self.presetBtns, sStates)
        def btnPresetButtonsEventHandler(btn: Button, state: str):
            presetId = btn.ID

            if state == sPressed:
                btn.SetState(1)
            elif state == sReleased:
                btn.SetState(0)
            elif state == sTapped:
                btn.SetState(1)

                @Wait(0.3)
                def tappedBtnPresetHandler():
                    btn.SetState(0)
                    dbg.print("Preset {} call".format(presetId))
                    signals.emit("*", signal="Preset", params={"action": "Call", "preset": presetId})
                    self.camProcessor.callPreset(presetId)
            elif state == sHeld:
                btn.SetState(0)
                if self.camProcessor.storePreset(self.activeCam.id, presetId):
                    self.presetSavedBtn.SetVisible(True)
                    dbg.print("Preset {} stored".format(presetId))

                    @Wait(2)
                    def savedButtonBlink():
                        self.presetSavedBtn.SetVisible(False)


InitModule(__name__)
