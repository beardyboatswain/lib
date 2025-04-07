from extronlib.interface import SerialInterface, EthernetClientInterface
from re import compile, search
from math import floor
from extronlib.system import Wait, ProgramLog


class DeviceClass:
    def __init__(self):

        self.Unidirectional = 'False'
        self.connectionCounter = 15
        self.DefaultResponseTimeout = 0.3
        self.Subscription = {}
        self.ReceiveData = self.__ReceiveData
        self.__receiveBuffer = b''
        self.__maxBufferSize = 2048
        self.__matchStringDict = {}
        self.counter = 0
        self.connectionFlag = True
        self.initializationChk = True
        self.Debug = False
        self.deviceUsername = 'Username'
        self.devicePassword = None
        self.Models = {
            'XTP II CrossPoint 1600': self.extr_15_1269_1600,
            'XTP II CrossPoint 3200': self.extr_15_1269_3200,
            'XTP II CrossPoint 6400': self.extr_15_1269_6400,
        }

        self.Commands = {
            'ConnectionStatus': {'Status': {}},
            'AnalogOutputVolumeEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'AudioMute': {'Parameters': ['Output'], 'Status': {}},
            'AudioMuteEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'EndpointTie': {'Parameters': ['Input'], 'Status': {}},
            'InputExecutiveModeEndpoint': {'Parameters': ['Input'], 'Status': {}},
            'OutputExecutiveModeEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'OutputImageResetEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'HDCPInputStatusEndpoint': {'Parameters': ['Input', 'Sub Input'], 'Status': {}},
            'ExecutiveMode': {'Status': {}},
            'FreezeEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'GlobalAudioMute': {'Status': {}},
            'GlobalVideoMute': {'Status': {}},
            'HDCPInputAuthorization': {'Parameters': ['Input'], 'Status': {}},
            'HDCPInputAuthorizationEndpoint': {'Parameters': ['Input', 'Sub Input'], 'Status': {}},
            'HDCPInputStatus': {'Parameters': ['Input'], 'Status': {}},
            'HDCPOutputStatus': {'Parameters': ['Output'], 'Status': {}},
            'InputAudioSwitchMode': {'Parameters': ['Input'], 'Status': {}},
            'InputAudioSwitchModeEndpoint': {'Parameters': ['Input', 'Sub Input'], 'Status': {}},
            'InputSignalStatus': {'Parameters': ['Input'], 'Status': {}},
            'InputSignalStatusEndpoint': {'Parameters': ['Input', 'Sub Input'], 'Status': {}},
            'InputTieStatus': {'Parameters': ['Input', 'Output'], 'Status': {}},
            'MatrixTieCommand': {'Parameters': ['Input', 'Output', 'Tie Type'], 'Status': {}},
            'OutputTieStatus': {'Parameters': ['Output', 'Tie Type'], 'Status': {}},
            'PowerSupplyStatus': {'Parameters': ['Number'], 'Status': {}},
            'PresetRecall': {'Status': {}},
            'PresetSave': {'Status': {}},
            'RefreshMatrix': {'Status': {}},
            'Relay': {'Parameters': ['Output', 'Relay'], 'Status': {}},
            'RelayPulse': {'Parameters': ['Output', 'Relay'], 'Status': {}},
            'TestPattern': {'Status': {}},
            'VideoMute': {'Parameters': ['Output'], 'Status': {}},
            'VideoMuteEndpoint': {'Parameters': ['Output'], 'Status': {}},
            'Volume': {'Parameters': ['Output'], 'Status': {}},
            'XTPInputPower': {'Parameters': ['Input'], 'Status': {}},
            'XTPOutputPower': {'Parameters': ['Output'], 'Status': {}},
        }

        self.VerboseDisabled = True
        self.PasswdPromptCount = 0
        self.Authenticated = 'Not Needed'

        self.refresh_matrix = False

        if self.Unidirectional == 'False':
            self.AddMatchString(compile(rb'VolR(\d{2})\*([1-2])\*(\d{2})\r\n'), self.__MatchAnalogOutputVolumeEndpoint, None)
            self.AddMatchString(compile(rb'Amt(0[1-9]|[1-5][0-9]|6[0-4])\*([0-3])\r\n'), self.__MatchAudioMute, None)
            self.AddMatchString(compile(rb'AmtR(\d+)\*([1-4])\*([0-3])\r\n'), self.__MatchAudioMuteEndpoint, None)
            self.AddMatchString(compile(b'Exec([0-2])\r\n'), self.__MatchExecutiveMode, None)
            self.AddMatchString(compile(rb'ExeT(0[1-9]|[1-2][0-9]|3[0-2])\*([0-2])\r\n'), self.__MatchInputExecutiveModeEndpoint, None)
            self.AddMatchString(compile(rb'ExeR(0[1-9]|[1-2][0-9]|3[0-2])\*([0-2])\r\n'), self.__MatchOutputExecutiveModeEndpoint, None)
            self.AddMatchString(compile(rb'Etie(0[1-9]|[1-5][0-9]|6[0-4])\*([1-3])\*([1-3])\r\n'), self.__MatchEndpointTie, None)
            self.AddMatchString(compile(rb'FrzR(\d+)\*([1-2])\*([0-1])\r\n'), self.__MatchFreezeEndpoint, None)
            self.AddMatchString(compile(rb'AfmtI(\d+)\*([0-3])\r\n'), self.__MatchInputAudioSwitchMode, None)
            self.AddMatchString(compile(rb'AfmtT(\d+)\*([1-4])\*([0-3])\r\n'), self.__MatchInputAudioSwitchModeEndpoint, None)
            self.AddMatchString(compile(rb'HdcpE(0[1-9]|[1-5][0-9]|6[0-4])\*(0|1)\r\n'), self.__MatchHDCPInputAuthorization, None)
            self.AddMatchString(compile(rb'HdcpTE(0[1-9]|[1-2][0-9]|3[0-2])\*([1-4])\*(0|1)\r\n'), self.__MatchHDCPInputAuthorizationEndpoint, None)
            self.AddMatchString(compile(rb'HdcpI00\*([012]+)\r\n'), self.__MatchHDCPInputStatus, None)
            self.AddMatchString(compile(rb'HdcpT(0[1-9]|[1-2][0-9]|3[0-2])\*([1-4])\*([012])\r\n'), self.__MatchHDCPInputStatusEndpoint, None)
            self.AddMatchString(compile(rb'HdcpO00\*([0-7]+)\r\n'), self.__MatchHDCPOutputStatus, None)
            self.AddMatchString(compile(rb'Frq0+\*([0-1]+)\r\n'), self.__MatchInputSignalStatus, None)
            self.AddMatchString(compile(rb'LsT(0[1-9]|[1-2][0-9]|3[0-2])\*([1-4])\*([0-1])\r\n'), self.__MatchInputSignalStatusEndpoint, None)
            self.AddMatchString(compile(b'Vmt[0-1]\r\n'), self.__MatchGlobalMute, None)
            self.AddMatchString(compile(b'Amt[0-3]\r\n'), self.__MatchGlobalMute, None)
            self.AddMatchString(compile(b'Mut([0-7]+)\r\n'), self.__MatchMute, None)
            self.AddMatchString(compile(rb'Rely(0[1-9]|[1-5][0-9]|6[0-4])\*([12])\*(1|0)\r\n'), self.__MatchRelay, None)
            self.AddMatchString(compile(rb'Tst([01]\d)\r\n'), self.__MatchTestPattern, None)
            self.AddMatchString(compile(rb'Vmt(\d+)\*([0-1])\r\n'), self.__MatchVideoMute, None)
            self.AddMatchString(compile(rb'VmtR(\d+)\*([1-2])\*([0-1])\r\n'), self.__MatchVideoMuteEndpoint, None)
            self.AddMatchString(compile(rb'Out(\d{2}) Vol(\d{2})\r\n'), self.__MatchVolume, None)
            self.AddMatchString(compile(rb'PoecI00\*(?P<power>[01]{0,64})\r\n'), self.__MatchXTPInputPower, 'Polled')
            self.AddMatchString(compile(rb'PoecI(?P<input>[0-9]{2})\*(?P<power>0|1)\*(?P<amount>00|13)\*(?P<status>[0-4])\r\n'), self.__MatchXTPInputPower, 'Unsolicited')
            self.AddMatchString(compile(rb'PoecO00\*(?P<power>[01]{0,64})\r\n'), self.__MatchXTPOutputPower, 'Polled')
            self.AddMatchString(compile(rb'PoecO(?P<output>[0-9]{2})\*(?P<power>0|1)\*(?P<amount>00|13)\*(?P<status>[0-4])\r\n'), self.__MatchXTPOutputPower, 'Unsolicited')
            self.AddMatchString(compile(rb'Sts00\*(.*?)(?P<power>[01]{2,4})\r\n'), self.__MatchPowerSupplyStatus, None)
            self.AddMatchString(compile(b'Qik\r\n'), self.__MatchQik, None)
            self.AddMatchString(compile(rb'PrstR\d+\r\n'), self.__MatchQik, None)  # Response to a Set Preset Recall command
            self.AddMatchString(compile(rb'Vgp00 Out(\d{2})\*([0-9 -]*)Vid\r\n'), self.__MatchAllMatrixTie, 'Video')
            self.AddMatchString(compile(rb'Vgp00 Out(\d{2})\*([0-9 -]*)Aud\r\n'), self.__MatchAllMatrixTie, 'Audio')
            self.AddMatchString(compile(rb'(?:Out(\d+) In(\d+) (All|Vid|Aud|RGB))|(?:In(\d+) (All|Vid|Aud|RGB))\r\n'), self.__MatchOutputTieStatus, None)
            self.AddMatchString(compile(rb'E(\d+)\r\n'), self.__MatchErrors, None)
            self.AddMatchString(compile(b'Vrb3\r\n'), self.__MatchVerboseMode, None)

            if 'Serial' not in self.ConnectionType:
                self.AddMatchString(compile(b'Password:'), self.__MatchPassword, None)
                self.AddMatchString(compile(b'Login Administrator\r\n'), self.__MatchLoginAdmin, None)
                self.AddMatchString(compile(b'Login User\r\n'), self.__MatchLoginUser, None)

    def SetPassword(self, value, qualifier):

        self.Send(self.devicePassword + '\r\n')
   
    def __MatchPassword(self, match, tag):
        self.PasswdPromptCount += 1
        if self.PasswdPromptCount > 1:
            self.Error(['Log in failed. Please supply proper Admin password'])
            self.Authenticated = 'None'
        else:
            self.SetPassword(None, None)

    def __MatchLoginAdmin(self, match, tag):

        self.Authenticated = 'Admin'
        self.PasswdPromptCount = 0

    def __MatchLoginUser(self, match, tag):

        self.Authenticated = 'User'
        self.PasswdPromptCount = 0
        self.Error(['Logged in as User. May have limited functionality.'])

    def __MatchVerboseMode(self, match, qualifier):
        self.OnConnected()

        self.VerboseDisabled = False
        self.SetRefreshMatrix('All', None)

    def __MatchGlobalMute(self, match, tag):
        self.UpdateMute(None, None)

    def UpdateMute(self, value, qualifier):
        self.Send('wvm\r')

    def __MatchMute(self, match, tag):

        stat = match.group(1).decode()
        output = 1

        for i in stat:
            if i == '0':
                self.WriteStatus('AudioMute', 'Off', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'Off', {'Output': str(output)})
            elif i == '1':
                self.WriteStatus('AudioMute', 'Off', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'On', {'Output': str(output)})
            elif i == '2':
                self.WriteStatus('AudioMute', 'Digital', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'Off', {'Output': str(output)})
            elif i == '3':
                self.WriteStatus('AudioMute', 'Digital', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'On', {'Output': str(output)})
            elif i == '4':
                self.WriteStatus('AudioMute', 'Analog', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'Off', {'Output': str(output)})
            elif i == '5':
                self.WriteStatus('AudioMute', 'Analog', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'On', {'Output': str(output)})
            elif i == '6':
                self.WriteStatus('AudioMute', 'On', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'Off', {'Output': str(output)})
            elif i == '7':
                self.WriteStatus('AudioMute', 'On', {'Output': str(output)})
                self.WriteStatus('VideoMute', 'On', {'Output': str(output)})
            output += 1

    def __MatchQik(self, match, tag):

        self.SetRefreshMatrix('All', None)

    def UpdateAllMatrixTie(self, value, qualifier):

        self.audio_status_counter = 0
        self.video_status_counter = 0
        self.matrix_tie_status = [['Untied' for _ in range(self.OutputSize)] for _ in range(self.InputSize)]

        self.__SetHelper(None, 'w0*1*1vc\r', None, None)
        self.__SetHelper(None, 'w0*1*2vc\r', None, None)

        if self.OutputSize > 16:
            self.__SetHelper(None, 'w0*17*1vc\r', None, None)
            self.__SetHelper(None, 'w0*17*2vc\r', None, None)
        if self.OutputSize > 32:            
            self.__SetHelper(None, 'w0*33*1vc\r', None, None)
            self.__SetHelper(None, 'w0*33*2vc\r', None, None)
            @Wait(0.5)
            def UpdateMatrix(self):            
                self.__SetHelper(None, 'w0*49*1vc\r', None, None)
                self.__SetHelper(None, 'w0*49*2vc\r', None, None)


    
    def InputTieStatusHelper(self, tie, output=None):

        if tie == 'Individual':
            output_range = range(output - 1, output)
        else:
            output_range = range(self.OutputSize)
        for input_ in range(self.InputSize):
            for output in output_range:
                self.WriteStatus('InputTieStatus', self.matrix_tie_status[input_][output], {'Input': str(input_ + 1), 'Output': str(output + 1)})

    def OutputTieStatusHelper(self, tie, output=None):

        AudioList = set()
        VideoList = set()

        if tie == 'Individual':
            output_range = range(output - 1, output)
        else:
            output_range = range(self.OutputSize)
        for input_ in range(self.InputSize):
            for output in output_range:
                tietype = self.matrix_tie_status[input_][output]
                if tietype == 'Audio/Video':
                    for tie_type in ['Audio', 'Video', 'Audio/Video']:
                        self.WriteStatus('OutputTieStatus', str(input_ + 1), {'Output': str(output + 1), 'Tie Type': tie_type})
                    AudioList.add(output)
                    VideoList.add(output)
                elif tietype == 'Audio':
                    self.WriteStatus('OutputTieStatus', '0', {'Output': str(output + 1), 'Tie Type': 'Audio/Video'})
                    self.WriteStatus('OutputTieStatus', str(input_ + 1), {'Output': str(output + 1), 'Tie Type': 'Audio'})
                    AudioList.add(output)
                elif tietype == 'Video':
                    self.WriteStatus('OutputTieStatus', '0', {'Output': str(output + 1), 'Tie Type': 'Audio/Video'})
                    self.WriteStatus('OutputTieStatus', str(input_ + 1), {'Output': str(output + 1), 'Tie Type': 'Video'})
                    VideoList.add(output)
        for o in output_range:
            if o not in VideoList:
                self.WriteStatus('OutputTieStatus', '0', {'Output': str(o + 1), 'Tie Type': 'Video'})
            if o not in AudioList:
                self.WriteStatus('OutputTieStatus', '0', {'Output': str(o + 1), 'Tie Type': 'Audio'})
            if o not in VideoList and o not in AudioList:
                self.WriteStatus('OutputTieStatus', '0', {'Output': str(o + 1), 'Tie Type': 'Audio/Video'})

    def __MatchAllMatrixTie(self, match, tag):

        current_output = int(match.group(1))
        input_list = match.group(2).decode().split()

        av_counter_max = 16 if self.refresh_matrix else self.OutputSize
        opposite_tag = 'Video' if tag == 'Audio' else 'Audio'

        for i in input_list:
            if tag == 'Audio':
                self.audio_status_counter += 1
            elif tag == 'Video':
                self.video_status_counter += 1

            if i != '--':
                if i != '00':
                    if self.matrix_tie_status[int(i) - 1][int(current_output - 1)] == opposite_tag:
                        self.matrix_tie_status[int(i) - 1][int(current_output - 1)] = 'Audio/Video'
                    else:
                        self.matrix_tie_status[int(i) - 1][int(current_output - 1)] = tag

                current_output += 1

        if self.audio_status_counter == av_counter_max and self.video_status_counter == av_counter_max:
            self.refresh_matrix = False
            if self.InputSize == 16:
                self.InputTieStatusHelper('All')
            self.OutputTieStatusHelper('All')
  
    def SetAnalogOutputVolumeEndpoint(self, value, qualifier):

        channel = int(qualifier['Output'])
        suboutput = 1
        if channel < 1 or channel > self.OutputSize:
            self.Discard('Invalid Command for SetAnalogOutputVolumeEndpoint')
        elif value < -64 or value > 0:
            self.Discard('Invalid Command for SetAnalogOutputVolumeEndpoint')
        else:
            self.__SetHelper('AnalogOutputVolumeEndpoint', '\x1bR{0}*{1}*{2}v\r'.format(channel, suboutput, value + 64), value, qualifier)

    def UpdateAnalogOutputVolumeEndpoint(self, value, qualifier):

        channel = int(qualifier['Output'])
        suboutput = 1
        if channel < 1 or channel > self.OutputSize:
            self.Discard('Invalid Command for UpdateAnalogOutputVolumeEndpoint')
        else:
            self.__UpdateHelper('AnalogOutputVolumeEndpoint', '\x1bR{0}*{1}v\r'.format(channel, suboutput), value, qualifier)

    def __MatchAnalogOutputVolumeEndpoint(self, match, qualifier):

        self.WriteStatus('AnalogOutputVolumeEndpoint', int(match.group(3)) - 64, {'Output': str(int(match.group(1)))})

    def SetAudioMute(self, value, qualifier):

        AudioMuteState = {
            'Off': '0',
            'On': '3',
        }

        channel = int(qualifier['Output'])
        if 1 <= channel <= self.OutputSize:
            self.__SetHelper('AudioMute', '{0}*{1}z'.format(channel, AudioMuteState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetAudioMute')

    def UpdateAudioMute(self, value, qualifier):

        channel = int(qualifier['Output'])
        if 1 <= channel <= self.OutputSize:
            self.__UpdateHelper('AudioMute', '{0}z'.format(channel), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateAudioMute')

    def __MatchAudioMute(self, match, qualifier):

        AudioMuteName = {
            '0': 'Off',
            '3': 'On',
        }

        self.WriteStatus('AudioMute', AudioMuteName[match.group(2).decode()], {'Output': str(int(match.group(1)))})

    def SetAudioMuteEndpoint(self, value, qualifier):

        AudioMuteState = {
            'Off': '0',
            'On': '3',
            'Analog': '2',
            'Digital': '1',
        }
        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__SetHelper('AudioMuteEndpoint', '\x1bR{0}*{1}*{2}z\r'.format(channel, suboutput, AudioMuteState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetAudioMuteEndpoint')

    def UpdateAudioMuteEndpoint(self, value, qualifier):

        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__UpdateHelper('AudioMuteEndpoint', '\x1bR{0}*{1}z\r'.format(channel, suboutput), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateAudioMuteEndpoint')

    def __MatchAudioMuteEndpoint(self, match, qualifier):

        AudioMuteName = {
            '0': 'Off',
            '3': 'On',
            '2': 'Analog',
            '1': 'Digital'
        }

        self.WriteStatus('AudioMuteEndpoint', AudioMuteName[match.group(3).decode()], {'Output': str(int(match.group(1)))})

    def SetEndpointTie(self, value, qualifier):

        endpoint = int(value)
        input_ = qualifier['Input']

        if 1 <= int(input_) <= self.InputSize and 1 <= endpoint <= 3:
            EndpointTieCmdString = '\x1B{0}*{1}*3ETIE\r'.format(input_, endpoint)
            self.__SetHelper('EndpointTie', EndpointTieCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetEndpointTie')

    def UpdateEndpointTie(self, value, qualifier):

        input_ = qualifier['Input']
        if 1 <= int(input_) <= self.InputSize:
           
            EndpointTieStatusCmdString = '\x1B{0}ETIE\r'.format(input_)
            self.__UpdateHelper('EndpointTie', EndpointTieStatusCmdString, value, qualifier)
        else:
            self.Discard('Device Is Busy for UpdateEndpointTie')     

    def __MatchEndpointTie(self, match, qualifier):

        self.WriteStatus('EndpointTie', match.group(2).decode(), {'Input': str(int(match.group(1).decode()))})

    def SetExecutiveMode(self, value, qualifier):

        ExecutiveModeState = {
            'Mode 1': '1',
            'Mode 2': '2',
            'Off': '0'
        }
        self.__SetHelper('ExecutiveMode', '\x1B{0}EXEC\r'.format(ExecutiveModeState[value]), value, qualifier)

    def UpdateExecutiveMode(self, value, qualifier):

        self.__UpdateHelper('ExecutiveMode', '\x1BEXEC\r', value, qualifier)

    def __MatchExecutiveMode(self, match, qualifier):

        ExecutiveModeName = {
            '1': 'Mode 1',
            '2': 'Mode 2',
            '0': 'Off'
        }
        self.WriteStatus('ExecutiveMode', ExecutiveModeName[match.group(1).decode()], None)

    def SetFreezeEndpoint(self, value, qualifier):

        VideoMuteState = {
            'Enable': '1',
            'Disable': '0',
        }
        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__SetHelper('FreezeEndpoint', '\x1bR{0}*{1}*{2}F\r'.format(channel, suboutput, VideoMuteState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetFreezeEndpoint')

    def UpdateFreezeEndpoint(self, value, qualifier):

        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__UpdateHelper('FreezeEndpoint', '\x1bR{0}*{1}F\r'.format(channel, suboutput), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateFreezeEndpoint')

    def __MatchFreezeEndpoint(self, match, qualifier):

        VideoMuteName = {
            '0': 'Disable',
            '1': 'Enable',
        }

        self.WriteStatus('FreezeEndpoint', VideoMuteName[match.group(3).decode()], {'Output': str(int(match.group(1)))})

    def SetGlobalAudioMute(self, value, qualifier):

        AudioMuteState = {
            'Off': '0',
            'On': '3',
        }
        self.__SetHelper('GlobalAudioMute', '{0}*z'.format(AudioMuteState[value]), value, qualifier)

    def SetGlobalVideoMute(self, value, qualifier):

        VideoMuteState = {
            'Off': '0',
            'On': '1',
        }
        self.__SetHelper('GlobalVideoMute', '{0}*b'.format(VideoMuteState[value]), value, qualifier)

    def SetHDCPInputAuthorization(self, value, qualifier):

        states = {
            'On': '1',
            'Off': '0'
        }

        input_ = qualifier['Input']
        if 1 <= int(input_) <= self.InputSize:
            HDCPInputAuthorizationCmdString = '\x1BE{0}*{1}HDCP\r'.format(input_.zfill(2), states[value])
            self.__SetHelper('HDCPInputAuthorization', HDCPInputAuthorizationCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetHDCPInputAuthorization')

    def UpdateHDCPInputAuthorization(self, value, qualifier):

        input_ = qualifier['Input']
        if 1 <= int(input_) <= self.InputSize:
            commandstring = '\x1BE{0}HDCP\r'.format(input_)
            self.__UpdateHelper('HDCPInputAuthorization', commandstring, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateHDCPInputAuthorization')

    def __MatchHDCPInputAuthorization(self, match, qualifier):

        states = {
            '1': 'On',
            '0': 'Off'
        }

        input_ = int(match.group(1).decode())
        value = match.group(2).decode()

        self.WriteStatus('HDCPInputAuthorization', states[value], {'Input': str(input_)})

    def SetHDCPInputAuthorizationEndpoint(self, value, qualifier):

        states = {
            'On': '1',
            'Off': '0'
        }

        input_ = qualifier['Input']
        subinput = qualifier['Sub Input']
        if 1 <= int(input_) <= self.InputSize:
            if 1 <= int(subinput) <= 3:
                HDCPInputAuthorizationCmdString = '\x1BTE{0}*{1}*{2}HDCP\r'.format(input_.zfill(2), subinput, states[value])
                self.__SetHelper('HDCPInputAuthorizationEndpoint', HDCPInputAuthorizationCmdString, value, qualifier)
            else:
                self.Discard('Invalid Command for SetHDCPInputAuthorizationEndpoint')
        else:
            self.Discard('Invalid Command for SetHDCPInputAuthorizationEndpoint')

    def UpdateHDCPInputAuthorizationEndpoint(self, value, qualifier):

        input_ = qualifier['Input']
        subinput = qualifier['Sub Input']
        if 1 <= int(input_) <= self.InputSize:
            if 1 <= int(subinput) <= 3:
                commandstring = '\x1BTE{0}*{1}HDCP\r'.format(input_, subinput)
                self.__UpdateHelper('HDCPInputAuthorizationEndpoint', commandstring, value, qualifier)
            else:
                self.Discard('Invalid Command for UpdateHDCPInputAuthorizationEndpoint')
        else:
            self.Discard('Invalid Command for UpdateHDCPInputAuthorizationEndpoint')

    def __MatchHDCPInputAuthorizationEndpoint(self, match, qualifier):

        states = {
            '1': 'On',
            '0': 'Off'
        }

        input_ = int(match.group(1).decode())
        subinput = int(match.group(2).decode())
        value = match.group(3).decode()

        self.WriteStatus('HDCPInputAuthorizationEndpoint', states[value], {'Input': str(input_), 'Sub Input': str(subinput)})

    def UpdateHDCPInputStatus(self, value, qualifier):
              
        if 1 <= int(qualifier['Input']) <= self.InputSize:
            self.__UpdateHelper('HDCPInputStatus', 'wI*HDCP\r', value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateHDCPInputStatus')
       
    def __MatchHDCPInputStatus(self, match, qualifier):

        HDCPInputStatus = {
            '0': 'No Source Connected',
            '2': 'No HDCP Content',
            '1': 'HDCP Content'
        }

        signal = match.group(1).decode()
        inputNumber = 1
        for input_ in signal:
            self.WriteStatus('HDCPInputStatus', HDCPInputStatus[input_], {'Input': str(inputNumber)})
            inputNumber += 1

    def UpdateHDCPInputStatusEndpoint(self, value, qualifier):

        if 1 <= int(qualifier['Input']) <= self.InputSize:
            if 1 <= int(qualifier['Sub Input']) <= 3:
                self.__UpdateHelper('HDCPInputStatusEndpoint', 'wT{0}*{1}HDCP\r'.format(qualifier['Input'], qualifier['Sub Input']), value, qualifier)
            else:
                self.Discard('Invalid Command for UpdateHDCPInputStatusEndpoint')
        else:
            self.Discard('Invalid Command for UpdateHDCPInputStatusEndpoint')

    def __MatchHDCPInputStatusEndpoint(self, match, qualifier):

        HDCPInputStatus = {
            '0': 'No Source Connected',
            '2': 'No HDCP Content',
            '1': 'HDCP Content'
        }

        state = match.group(3).decode()
        inputNumber = int(match.group(1).decode())
        subinput = match.group(2).decode()
        self.WriteStatus('HDCPInputStatusEndpoint', HDCPInputStatus[state], {'Input': str(inputNumber), 'Sub Input': subinput})

    def UpdateHDCPOutputStatus(self, value, qualifier):

        if 1 <= int(qualifier['Output']) <= self.OutputSize:
            self.__UpdateHelper('HDCPOutputStatus', 'wO*HDCP\r', value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateHDCPOutputStatus')
       
    def __MatchHDCPOutputStatus(self, match, qualifier):

        HDCPOutputStatus = {
            '0': 'No monitor connected',
            '1': 'Monitor connected, not encrypted',
            '2': 'No monitor connected',
            '3': 'Monitor connected, not encrypted',
            '4': 'No monitor connected',
            '5': 'Monitor connected, not encrypted',
            '6': 'No monitor connected',
            '7': 'Monitor connected, currently encrypted'
        }

        signal = match.group(1).decode()
        outputNumber = 1
        for output in signal:
            self.WriteStatus('HDCPOutputStatus', HDCPOutputStatus[output], {'Output': str(outputNumber)})
            outputNumber += 1

    def SetInputAudioSwitchMode(self, value, qualifier):

        InputAudioSwitchModeState = {
            'Auto': '0',
            'Digital': '1',
            'Local 2 Ch Audio': '2',
            'Digital Multi-Ch Audio': '3',

        }
        channel = int(qualifier['Input'])
        if 1 <= channel <= self.InputSize:
            self.__SetHelper('InputAudioSwitchMode', '\x1bI{0}*{1}AFMT\r'.format(channel, InputAudioSwitchModeState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetInputAudioSwitchMode')

    def UpdateInputAudioSwitchMode(self, value, qualifier):

        channel = int(qualifier['Input'])
        if 1 <= channel <= self.InputSize:
            self.__UpdateHelper('InputAudioSwitchMode', '\x1bI{0}AFMT\r'.format(channel), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateInputAudioSwitchMode')

    def __MatchInputAudioSwitchMode(self, match, qualifier):

        InputAudioSwitchModeName = {
            '0': 'Auto',
            '1': 'Digital',
            '2': 'Local 2 Ch Audio',
        }

        self.WriteStatus('InputAudioSwitchMode', InputAudioSwitchModeName[match.group(2).decode()], {'Input': str(int(match.group(1)))})

    def SetInputAudioSwitchModeEndpoint(self, value, qualifier):

        InputAudioSwitchModeState = {
            'Auto': '0',
            'Digital': '1',
            'Local 2 Ch Audio': '2',
        }
        channel = int(qualifier['Input'])
        subinput = int(qualifier['Sub Input'])
        if 1 <= channel <= self.InputSize:
            if 1 <= subinput <= 3:
                self.__SetHelper('InputAudioSwitchModeEndpoint', '\x1bT{0}*{1}*{2}AFMT\r'.format(channel, subinput, InputAudioSwitchModeState[value]), value, qualifier)
            else:
                self.Discard('Invalid Command for SetInputAudioSwitchModeEndpoint')
        else:
            self.Discard('Invalid Command for SetInputAudioSwitchModeEndpoint')

    def UpdateInputAudioSwitchModeEndpoint(self, value, qualifier):

        channel = int(qualifier['Input'])
        subinput = int(qualifier['Sub Input'])
        if 1 <= channel <= self.InputSize:
            if 1 <= subinput <= 3:
                self.__UpdateHelper('InputAudioSwitchModeEndpoint', '\x1bT{0}*{1}AFMT\r'.format(channel, subinput), value, qualifier)
            else:
                self.Discard('Invalid Command for UpdateInputAudioSwitchModeEndpoint')
        else:
            self.Discard('Invalid Command for UpdateInputAudioSwitchModeEndpoint')

    def __MatchInputAudioSwitchModeEndpoint(self, match, qualifier):

        InputAudioSwitchModeName = {
            '0': 'Auto',
            '1': 'Digital',
            '2': 'Local 2 Ch Audio',
        }

        self.WriteStatus('InputAudioSwitchModeEndpoint', InputAudioSwitchModeName[match.group(3).decode()], {'Input': str(int(match.group(1))), 'Sub Input': str(int(match.group(2)))})

    def SetInputExecutiveModeEndpoint(self, value, qualifier):

        ExecutiveModeState = {
            'Mode 1': '1',
            'Mode 2': '2',
            'Off': '0'
        }
        self.__SetHelper('InputExecutiveModeEndpoint', '\x1BT{0}*{1}X\r'.format(qualifier['Input'], ExecutiveModeState[value]), value, qualifier)

    def UpdateInputExecutiveModeEndpoint(self, value, qualifier):

        self.__UpdateHelper('InputExecutiveModeEndpoint', '\x1BT{0}X\r'.format(qualifier['Input']), value, qualifier)

    def __MatchInputExecutiveModeEndpoint(self, match, qualifier):

        ExecutiveModeName = {
            '1': 'Mode 1',
            '2': 'Mode 2',
            '0': 'Off'
        }

        inp = int(match.group(1).decode())
        self.WriteStatus('InputExecutiveModeEndpoint', ExecutiveModeName[match.group(2).decode()], {'Input': str(inp)})

    def SetOutputExecutiveModeEndpoint(self, value, qualifier):

        ExecutiveModeState = {
            'Mode 1': '1',
            'Mode 2': '2',
            'Off': '0'
        }
        self.__SetHelper('OutputExecutiveModeEndpoint', '\x1BR{0}*{1}X\r'.format(qualifier['Output'], ExecutiveModeState[value]), value, qualifier)

    def UpdateOutputExecutiveModeEndpoint(self, value, qualifier):

        self.__UpdateHelper('OutputExecutiveModeEndpoint', '\x1BR{0}X\r'.format(qualifier['Output']), value, qualifier)

    def __MatchOutputExecutiveModeEndpoint(self, match, qualifier):

        ExecutiveModeName = {
            '1': 'Mode 1',
            '2': 'Mode 2',
            '0': 'Off'
        }

        inp = int(match.group(1).decode())
        self.WriteStatus('OutputExecutiveModeEndpoint', ExecutiveModeName[match.group(2).decode()], {'Output': str(inp)})

    def SetOutputImageResetEndpoint(self, value, qualifier):

        output_ = qualifier['Output']
        suboutput = 1
        if 1 <= int(output_) <= self.OutputSize:
            OutputImageResetEndpointCmdString = 'wR{0}*{1}*2AADJ\r'.format(output_, suboutput)
            self.__SetHelper('OutputImageResetEndpoint', OutputImageResetEndpointCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetOutputImageResetEndpoint')

    def UpdateInputSignalStatus(self, value, qualifier):

        self.__UpdateHelper('InputSignalStatus', '0LS', value, qualifier)

    def __MatchInputSignalStatus(self, match, qualifier):

        InputSignalStatus = {
            '1': 'Active',
            '0': 'Not Active'
        }

        signal = match.group(1).decode()
        inputNumber = 1
        for input_ in signal:
            self.WriteStatus('InputSignalStatus', InputSignalStatus[input_], {'Input': str(inputNumber)})
            inputNumber += 1

    def UpdateInputSignalStatusEndpoint(self, value, qualifier):

        channel = int(qualifier['Input'])
        subinput = int(qualifier['Sub Input'])
        if 1 <= channel <= self.InputSize:
            if 1 <= subinput <= 4:
                self.__UpdateHelper('InputSignalStatusEndpoint', '\x1bT{0}*{1}LS\r'.format(channel, subinput), value, qualifier)
            else:
                self.Discard('Invalid Command for UpdateInputSignalStatusEndpoint')
        else:
            self.Discard('Invalid Command for UpdateInputSignalStatusEndpoint')

    def __MatchInputSignalStatusEndpoint(self, match, qualifier):

        InputSignalStatus = {
            '1': 'Active',
            '0': 'Not Active'
        }
        signal = match.group(3).decode()
        inputNumber = int(match.group(1).decode())
        subinput = match.group(2).decode()
        self.WriteStatus('InputSignalStatusEndpoint', InputSignalStatus[signal], {'Input': str(inputNumber), 'Sub Input': subinput})

    def SetMatrixTieCommand(self, value, qualifier):

        TieTypeValues = {
            'Audio': '\x24',
            'Video': '\x26',
            'Audio/Video': '\x21'
        }

        input_ = int(qualifier['Input'])
        output = qualifier['Output']
        tieType = qualifier['Tie Type']
        outrange = ['All']
        for i in range(1, self.OutputSize + 1):
            outrange.append(str(i))

        if output not in outrange:
            self.Discard('Invalid Command for SetMatrixTieCommand')
        elif input_ < 0 or input_ > self.InputSize:
            self.Discard('Invalid Command for SetMatrixTieCommand')
        else:
            output = '' if output == 'All' else output
            self.__SetHelper('MatrixTieCommand', '{0}*{1}{2}'.format(input_, output, TieTypeValues[tieType]), input_, qualifier)

    def __MatchOutputTieStatus(self, match, qualifier):
        if match.group(1):
            self.__MatchIndividualTie(match, None)
        else:
            self.__MatchAllTie(match, None)

    def __MatchIndividualTie(self, match, qualifier):

        TieTypeStates = {
            'Aud': 'Audio',
            'Vid': 'Video',
            'RGB': 'Video',
            'All': 'Audio/Video'
        }
        output = int(match.group(1))
        input_ = int(match.group(2))
        tietype = TieTypeStates[match.group(3).decode()]

        if tietype == 'Audio/Video':
            for i in range(self.InputSize):
                current_tie = self.matrix_tie_status[i][output - 1]
                if i != input_ - 1 and current_tie in ['Audio', 'Video', 'Audio/Video']:
                    self.matrix_tie_status[i][output - 1] = 'Untied'
                elif i == input_ - 1:
                    self.matrix_tie_status[i][output - 1] = 'Audio/Video'
        elif tietype in ['Video', 'Audio']:
            for i in range(self.InputSize):
                current_tie = self.matrix_tie_status[i][output - 1]
                opTag = 'Audio' if tietype == 'Video' else 'Video'
                if i == input_ - 1:
                    if current_tie == opTag or current_tie == 'Audio/Video':
                        self.matrix_tie_status[i][output - 1] = 'Audio/Video'
                    else:
                        self.matrix_tie_status[i][output - 1] = tietype
                elif input_ == 0 or i != input_ - 1:
                    if current_tie == tietype:
                        self.matrix_tie_status[i][output - 1] = 'Untied'
                    elif current_tie == 'Audio/Video':
                        self.matrix_tie_status[i][output - 1] = opTag

        self.OutputTieStatusHelper('Individual', output)
        if self.InputSize == 16:
            self.InputTieStatusHelper('Individual', output)

    def __MatchAllTie(self, match, qualifier):

        TieTypeStates = {
            'Aud': 'Audio',
            'Vid': 'Video',
            'RGB': 'Video',
            'All': 'Audio/Video'
        }
        new_input = int(match.group(4))
        tietype = TieTypeStates[match.group(5).decode()]

        if tietype in ['Audio', 'Video']:
            op_tie_type = 'Audio' if tietype == 'Video' else 'Video'
            for output in range(self.OutputSize):
                for input_ in range(self.InputSize):
                    if input_ == new_input - 1:
                        if self.matrix_tie_status[input_][output] == op_tie_type:
                            self.matrix_tie_status[input_][output] = 'Audio/Video'
                        else:
                            self.matrix_tie_status[input_][output] = tietype
                    else:
                        if self.matrix_tie_status[input_][output] == 'Audio/Video':
                            self.matrix_tie_status[input_][output] = op_tie_type
                        elif self.matrix_tie_status[input_][output] != op_tie_type:
                            self.matrix_tie_status[input_][output] = 'Untied'

        elif tietype == 'Audio/Video':
            for output in range(self.OutputSize):
                for input_ in range(self.InputSize):
                    if input_ == new_input - 1:
                        self.matrix_tie_status[input_][output] = 'Audio/Video'
                    else:
                        self.matrix_tie_status[input_][output] = 'Untied'

        if self.InputSize == 16:
            self.InputTieStatusHelper('All')
        self.OutputTieStatusHelper('All')

    def UpdatePowerSupplyStatus(self, value, qualifier):

        PowerSupplyStatusCmdString = 'S\r'
        self.__UpdateHelper('PowerSupplyStatus', PowerSupplyStatusCmdString, value, qualifier)
      
    def __MatchPowerSupplyStatus(self, match, tag):

        ValueStateValues = {
            '1': 'Installed/Normal',
            '0': 'Not Installed/Failed'
        }
        max_ = len(match.group('power').decode())
        if max_ in [2, 4]:
            for number in range(0, 4):
                qualifier = {'Number': str(number + 1)}
                if number < max_:
                    value = ValueStateValues[match.group('power').decode()[number]]
                else:
                    value = 'Not Installed/Failed'
                self.WriteStatus('PowerSupplyStatus', value, qualifier)

    def SetPresetRecall(self, value, qualifier):

        if 0 < int(value) < 33:
            self.__SetHelper('PresetRecall', '\x1BR{0}PRST\r'.format(value), value, qualifier)
        else:
            self.Discard('Invalid Command for SetPresetRecall')

    def SetPresetSave(self, value, qualifier):

        if 0 < int(value) < 33:
            self.__SetHelper('PresetSave', '\x1BS{0}PRST\r'.format(value), value, qualifier)
        else:
            self.Discard('Invalid Command for SetPresetSave')

    def SetRefreshMatrix(self, value, qualifier):

        state = {
            '1 - 16': 'w0*1*1vc\rw0*1*2vc\r',
            '17 - 32': 'w0*17*1vc\rw0*17*2vc\r',
            '33 - 48': 'w0*33*1vc\rw0*33*2vc\r',
            '49 - 64': 'w0*49*1vc\rw0*49*2vc\r'
        }

        if not value or value == 'All':
            self.UpdateAllMatrixTie(value, qualifier)
        elif value in state:
            self.refresh_matrix = True
            self.audio_status_counter = 0
            self.video_status_counter = 0
            self.__SetHelper('RefreshMatrix', state[value], value, qualifier)  
        else:
            self.Discard('Invalid Command for SetRefreshMatrix')

    def SetRelay(self, value, qualifier):

        RelayState = {
            'Close': '1',
            'Open': '0',
        }

        output = int(qualifier['Output'])
        relay = int(qualifier['Relay'])

        if 1 <= output <= self.OutputSize and 1 <= relay <= 2:
            self.__SetHelper('Relay', 'w{0}*{1}*{2}RELY\r'.format(output, relay, RelayState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetRelay')

    def UpdateRelay(self, value, qualifier):

        output = int(qualifier['Output'])
        relay = int(qualifier['Relay'])

        if 1 <= output <= self.OutputSize and 1 <= relay <= 2:
            self.__UpdateHelper('Relay', 'w{0}*{1}RELY\r'.format(output, relay), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateRelay')

    def __MatchRelay(self, match, qualifier):

        RelayState = {
            '1': 'Close',
            '0': 'Open',
        }
        output = int(match.group(1))
        relay = int(match.group(2))
        self.WriteStatus('Relay', RelayState[match.group(3).decode()], {'Output': str(output), 'Relay': str(relay)})

    def SetRelayPulse(self, value, qualifier):

        output = int(qualifier['Output'])
        relay = int(qualifier['Relay'])

        if 1 <= output <= self.OutputSize and 1 <= relay <= 2 and 0.1 <= value <= 1048.5:
            self.__SetHelper('RelayPulse', 'w{0}*{1}*3*{2}RELY\r'.format(output, relay, floor((value * 62.5) + 0.5)), value, qualifier)
        else:
            self.Discard('Invalid Command for SetRelayPulse')

    def SetTestPattern(self, value, qualifier):

        ValueStateValues = {
            'Black Screen, No Audio (720p @ 50 Hz)': '2',
            'Black Screen, No Audio (720p @ 60 Hz)': '4',
            'Black Screen, No Audio (1080p @ 60 Hz)': '6',
            'Black Screen, Audio (720p @ 50 Hz)': '8',
            'Black Screen, Audio (720p @ 60 Hz)': '10',
            'Black Screen, Audio (1080p @ 60 Hz)': '12',
            'Color Bars, No Audio (720p @ 50 Hz)': '1',
            'Color Bars, No Audio (720p @ 60 Hz)': '3',
            'Color Bars, No Audio (1080p @ 60 Hz)': '5',
            'Color Bars, Audio (720p @ 50 Hz)': '7',
            'Color Bars, Audio (720p @ 60 Hz)': '9',
            'Color Bars, Audio (1080p @ 60 Hz)': '11',
            'Off': '0'
        }

        TestPatternCmdString = '\x1B{0}TEST\r'.format(ValueStateValues[value])
        self.__SetHelper('TestPattern', TestPatternCmdString, value, qualifier)

    def UpdateTestPattern(self, value, qualifier):

        TestPatternCmdString = '\x1BTEST\r'
        self.__UpdateHelper('TestPattern', TestPatternCmdString, value, qualifier)

    def __MatchTestPattern(self, match, tag):

        ValueStateValues = {
            '02': 'Black Screen, No Audio (720p @ 50 Hz)',
            '04': 'Black Screen, No Audio (720p @ 60 Hz)',
            '06': 'Black Screen, No Audio (1080p @ 60 Hz)',
            '08': 'Black Screen, Audio (720p @ 50 Hz)',
            '10': 'Black Screen, Audio (720p @ 60 Hz)',
            '12': 'Black Screen, Audio (1080p @ 60 Hz)',
            '01': 'Color Bars, No Audio (720p @ 50 Hz)',
            '03': 'Color Bars, No Audio (720p @ 60 Hz)',
            '05': 'Color Bars, No Audio (1080p @ 60 Hz)',
            '07': 'Color Bars, Audio (720p @ 50 Hz)',
            '09': 'Color Bars, Audio (720p @ 60 Hz)',
            '11': 'Color Bars, Audio (1080p @ 60 Hz)',
            '00': 'Off'
        }

        value = ValueStateValues[match.group(1).decode()]
        self.WriteStatus('TestPattern', value, None)

    def SetVideoMute(self, value, qualifier):

        VideoMuteState = {
            'Off': '0',
            'On': '1',
        }
        channel = int(qualifier['Output'])
        if 1 <= channel <= self.OutputSize:
            self.__SetHelper('VideoMute', '{0}*{1}b'.format(channel, VideoMuteState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetVideoMute')

    def UpdateVideoMute(self, value, qualifier):

        channel = int(qualifier['Output'])
        if 1 <= channel <= self.OutputSize:
            self.__UpdateHelper('VideoMute', '{0}b'.format(channel), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateVideoMute')

    def __MatchVideoMute(self, match, qualifier):

        VideoMuteName = {
            '0': 'Off',
            '1': 'On',
        }

        self.WriteStatus('VideoMute', VideoMuteName[match.group(2).decode()], {'Output': str(int(match.group(1)))})

    def SetVideoMuteEndpoint(self, value, qualifier):

        VideoMuteState = {
            'Off': '0',
            'On': '1',
        }
        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__SetHelper('VideoMuteEndpoint', '\x1bR{0}*{1}*{2}b\r'.format(channel, suboutput, VideoMuteState[value]), value, qualifier)
        else:
            self.Discard('Invalid Command for SetVideoMuteEndpoint')

    def UpdateVideoMuteEndpoint(self, value, qualifier):

        channel = int(qualifier['Output'])
        suboutput = 1
        if 1 <= channel <= self.OutputSize:
            self.__UpdateHelper('VideoMuteEndpoint', '\x1bR{0}*{1}b\r'.format(channel, suboutput), value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateVideoMuteEndpoint')

    def __MatchVideoMuteEndpoint(self, match, qualifier):

        VideoMuteName = {
            '0': 'Off',
            '1': 'On',
        }

        self.WriteStatus('VideoMuteEndpoint', VideoMuteName[match.group(3).decode()], {'Output': str(int(match.group(1)))})

    def SetVolume(self, value, qualifier):

        channel = int(qualifier['Output'])
        if 1 <= channel <= self.OutputSize and -64 <= value <= 0:
            self.__SetHelper('Volume', '{0}*{1}v'.format(channel, value + 64), value, qualifier)
        else:
            self.Discard('Invalid Command for SetVolume')

    def UpdateVolume(self, value, qualifier):

        channel = int(qualifier['Output'])
        if channel < 1 or channel > self.OutputSize:
            self.Discard('Invalid Command for UpdateVolume')
        else:
            self.__UpdateHelper('Volume', '{0}v'.format(channel), value, qualifier)

    def __MatchVolume(self, match, qualifier):

        self.WriteStatus('Volume', int(match.group(2)) - 64, {'Output': str(int(match.group(1)))})

    def SetXTPInputPower(self, value, qualifier):

        ValueStateValues = {
            'On': '1',
            'Off': '0'
        }

        input_ = qualifier['Input']
        if 1 <= int(input_) <= self.InputSize:
            XTPInputPowerCmdString = 'wI{0}*{1}POEC\r'.format(input_, ValueStateValues[value])
            self.__SetHelper('XTPInputPower', XTPInputPowerCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetXTPInputPower')

    def UpdateXTPInputPower(self, value, qualifier):

        input_ = qualifier['Input']

        if 1 <= int(input_) <= self.InputSize:
            XTPInputPowerCmdString = 'wIPOEC\r'
            self.__UpdateHelper('XTPInputPower', XTPInputPowerCmdString, value, qualifier)
        else:
            self.Discard('Device Is Busy for UpdateXTPInputPower')        

    def __MatchXTPInputPower(self, match, tag):

        ValueStateValues = {
            '1': 'On',
            '0': 'Off'
        }
        if tag == 'Polled':
            input_ = 1
            for value in match.group('power').decode():
                if input_ > self.InputSize:
                    break
                self.WriteStatus('XTPInputPower', ValueStateValues[value], {'Input': str(input_)})
                input_ += 1
        elif tag == 'Unsolicited':
            input_ = match.group('input').decode().lstrip('0')
            if 1 <= int(input_) <= self.InputSize:
                self.WriteStatus('XTPInputPower', ValueStateValues[match.group('power').decode()], {'Input': input_})

    def SetXTPOutputPower(self, value, qualifier):

        ValueStateValues = {
            'On': '1',
            'Off': '0'
        }

        output = qualifier['Output']

        if 1 <= int(output) <= self.OutputSize:
            XTPOutputPowerCmdString = 'wO{0}*{1}POEC\r'.format(output, ValueStateValues[value])
            self.__SetHelper('XTPOutputPower', XTPOutputPowerCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetXTPOutputPower')

    def UpdateXTPOutputPower(self, value, qualifier):

        output = qualifier['Output']

        if 1 <= int(output) <= self.OutputSize:
            XTPOutputPowerCmdString = 'wOPOEC\r'
            self.__UpdateHelper('XTPOutputPower', XTPOutputPowerCmdString, value, qualifier)
        else:
            self.Discard('Device Is Busy for UpdateXTPOutputPower')
      
    def __MatchXTPOutputPower(self, match, tag):

        ValueStateValues = {
            '1': 'On',
            '0': 'Off'
        }
        if tag == 'Polled':
            output = 1
            for value in match.group('power').decode():
                if output > self.OutputSize:
                    break
                self.WriteStatus('XTPOutputPower', ValueStateValues[value], {'Output': str(output)})
                output += 1
        elif tag == 'Unsolicited':
            output = match.group('output').decode().lstrip('0')
            if 1 <= int(output) <= self.OutputSize:
                self.WriteStatus('XTPOutputPower', ValueStateValues[match.group('power').decode()], {'Output': output})

    def __MatchErrors(self, match, tag):

        DEVICE_ERROR_CODES = {
            '1': 'Invalid input channel number (out of range)',
            '10': 'Invalid command',
            '11': 'Invalid preset number (out of range)',
            '12': 'Invalid output number (out of range)',
            '13': 'Invalid value (out of range)',
            '14': 'Invalid command for this configuration',
            '17': 'Timeout (caused only by direct write of global presets)',
            '22': 'Busy',
            '24': 'Privilege violation (Users have access to all view and read commands [other than the administrator password], and can create ties, presets, and audio mutes',
            '25': 'Device not present',
            '26': 'Maximum number of connections exceeded',
            '27': 'Invalid event number',
            '28': 'Bad filename / file not found'
        }
        value = match.group(1).decode()
        if value in DEVICE_ERROR_CODES:
            self.Error([DEVICE_ERROR_CODES[value]])
        else:
            self.Error(['Unrecognized error code: ' + match.group(0).decode()])

    def __SetHelper(self, command, commandstring, value, qualifier):
        self.Debug = True
        if self.VerboseDisabled:
            @Wait(1)
            def SendVerbose():
                self.Send('w3cv\r\n')
                self.Send(commandstring)
        else:
            self.Send(commandstring)

    def __UpdateHelper(self, command, commandstring, value, qualifier):
        if self.initializationChk:
            self.OnConnected()
            self.initializationChk = False

        self.counter = self.counter + 1
        if self.counter > self.connectionCounter and self.connectionFlag:
            self.OnDisconnected()

        if self.Authenticated in ['User', 'Admin', 'Not Needed']:
            if self.Unidirectional == 'True':
                self.Discard('Inappropriate Command ' + command)
            else:
                if self.VerboseDisabled:
                    @Wait(1)
                    def SendVerbose():
                        self.Send('w3cv\r\n')
                        self.Send(commandstring)
                else:
                    self.Send(commandstring)
        else:
            self.Discard('Inappropriate Command ' + command)

    def OnConnected(self):
        self.connectionFlag = True
        self.WriteStatus('ConnectionStatus', 'Connected')
        self.counter = 0       

    def OnDisconnected(self):
        self.WriteStatus('ConnectionStatus', 'Disconnected')
        self.connectionFlag = False

        if 'Serial' not in self.ConnectionType:
            self.Authenticated = 'Not Needed'
            self.PasswdPromptCount = 0

        self.VerboseDisabled = True
        self.refresh_matrix = False
        
    def extr_15_1269_1600(self):

        self.InputSize = 16
        self.OutputSize = 16

    def extr_15_1269_3200(self):

        self.InputSize = 32
        self.OutputSize = 32

    def extr_15_1269_6400(self):

        self.InputSize = 64
        self.OutputSize = 64

    ######################################################
    # RECOMMENDED not to modify the code below this point
    ######################################################

    # Send Control Commands
    def Set(self, command, value, qualifier=None):
        method = getattr(self, 'Set%s' % command, None)
        if method is not None and callable(method):
            method(value, qualifier)
        else:
            raise AttributeError(command + 'does not support Set.')

    # Send Update Commands

    def Update(self, command, qualifier=None):
        method = getattr(self, 'Update%s' % command, None)
        if method is not None and callable(method):
            method(None, qualifier)
        else:
            raise AttributeError(command + 'does not support Update.')

    # This method is to tie an specific command with a parameter to a call back method
    # when its value is updated. It sets how often the command will be query, if the command
    # have the update method.
    # If the command doesn't have the update feature then that command is only used for feedback
    def SubscribeStatus(self, command, qualifier, callback):
        Command = self.Commands.get(command, None)
        if Command:
            if command not in self.Subscription:
                self.Subscription[command] = {'method': {}}

            Subscribe = self.Subscription[command]
            Method = Subscribe['method']

            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except BaseException:
                        if Parameter in qualifier:
                            Method[qualifier[Parameter]] = {}
                            Method = Method[qualifier[Parameter]]
                        else:
                            return

            Method['callback'] = callback
            Method['qualifier'] = qualifier
        else:
            raise KeyError('Invalid command for SubscribeStatus ' + command)

    # This method is to check the command with new status have a callback method then trigger the callback
    def NewStatus(self, command, value, qualifier):
        if command in self.Subscription:
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
            Command = self.Commands[command]
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except BaseException:
                        break
            if 'callback' in Method and Method['callback']:
                Method['callback'](command, value, qualifier)

    # Save new status to the command
    def WriteStatus(self, command, value, qualifier=None):
        self.counter = 0
        if not self.connectionFlag:
            self.OnConnected()
        Command = self.Commands[command]
        Status = Command['Status']
        if qualifier:
            for Parameter in Command['Parameters']:
                try:
                    Status = Status[qualifier[Parameter]]
                except KeyError:
                    if Parameter in qualifier:
                        Status[qualifier[Parameter]] = {}
                        Status = Status[qualifier[Parameter]]
                    else:
                        return
        try:
            if Status['Live'] != value:
                Status['Live'] = value
                self.NewStatus(command, value, qualifier)
        except BaseException:
            Status['Live'] = value
            self.NewStatus(command, value, qualifier)

    # Read the value from a command.
    def ReadStatus(self, command, qualifier=None):
        Command = self.Commands.get(command, None)
        if Command:
            Status = Command['Status']
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Status = Status[qualifier[Parameter]]
                    except KeyError:
                        return None
            try:
                return Status['Live']
            except BaseException:
                return None
        else:
            raise KeyError('Invalid command for ReadStatus: ' + command)

    def __ReceiveData(self, interface, data):
            # Handle incoming data
        self.__receiveBuffer += data
        index = 0    # Start of possible good data

        # check incoming data if it matched any expected data from device module
        for regexString, CurrentMatch in self.__matchStringDict.items():
            while True:
                result = search(regexString, self.__receiveBuffer)
                if result:
                    index = result.start()
                    CurrentMatch['callback'](result, CurrentMatch['para'])
                    self.__receiveBuffer = self.__receiveBuffer[:result.start()] + self.__receiveBuffer[result.end():]
                else:
                    break

        if index:
            # Clear out any junk data that came in before any good matches.
            self.__receiveBuffer = self.__receiveBuffer[index:]
        else:
            # In rare cases, the buffer could be filled with garbage quickly.
            # Make sure the buffer is capped.  Max buffer size set in init.
            self.__receiveBuffer = self.__receiveBuffer[-self.__maxBufferSize:]

    # Add regular expression so that it can be check on incoming data from device.
    def AddMatchString(self, regex_string, callback, arg):
        if regex_string not in self.__matchStringDict:
            self.__matchStringDict[regex_string] = {'callback': callback, 'para': arg}

    def MissingCredentialsLog(self, credential_type):
        if isinstance(self, EthernetClientInterface):
            port_info = 'IP Address: {0}:{1}'.format(self.IPAddress, self.IPPort)
        elif isinstance(self, SerialInterface):
            port_info = 'Host Alias: {0}\r\nPort: {1}'.format(self.Host.DeviceAlias, self.Port)
        else:
            return
        ProgramLog("{0} module received a request from the device for a {1}, "
                   "but device{1} was not provided.\n Please provide a device{1} "
                   "and attempt again.\n Ex: dvInterface.device{1} = '{1}'\n Please "
                   "review the communication sheet.\n {2}"
                   .format(__name__, credential_type, port_info), 'warning')


class SerialClass(SerialInterface, DeviceClass):

    def __init__(self, Host, Port, Baud=9600, Data=8, Parity='None', Stop=1, FlowControl='Off', CharDelay=0, Mode='RS232', Model=None):
        SerialInterface.__init__(self, Host, Port, Baud, Data, Parity, Stop, FlowControl, CharDelay, Mode)
        self.ConnectionType = 'Serial'
        DeviceClass.__init__(self)
        # Check if Model belongs to a subclass
        if len(self.Models) > 0:
            if Model not in self.Models:
                print('Model mismatch')
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'Host Alias: {0}, Port: {1}'.format(self.Host.DeviceAlias, self.Port)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')

    def Discard(self, message):
        self.Error([message])


class SerialOverEthernetClass(EthernetClientInterface, DeviceClass):

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Serial'
        DeviceClass.__init__(self)
        # Check if Model belongs to a subclass
        if len(self.Models) > 0:
            if Model not in self.Models:
                print('Model mismatch')
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'IP Address/Host: {0}:{1}'.format(self.Hostname, self.IPPort)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')

    def Discard(self, message):
        self.Error([message])

    def Disconnect(self):
        EthernetClientInterface.Disconnect(self)
        self.OnDisconnected()


class EthernetClass(EthernetClientInterface, DeviceClass):

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Ethernet'
        DeviceClass.__init__(self)
        # Check if Model belongs to a subclass
        if len(self.Models) > 0:
            if Model not in self.Models:
                print('Model mismatch')
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'IP Address/Host: {0}:{1}'.format(self.Hostname, self.IPPort)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')

    def Discard(self, message):
        self.Error([message])

    def Disconnect(self):
        EthernetClientInterface.Disconnect(self)
        self.OnDisconnected()
