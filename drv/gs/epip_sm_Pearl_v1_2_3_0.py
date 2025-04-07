from re import compile
import base64
import urllib.error
import urllib.request
from extronlib.interface import SerialInterface, EthernetClientInterface
import re

class DeviceHTTPClass:
    def __init__(self, ipAddress, port, deviceUsername=None, devicePassword=None):

        self.Unidirectional = 'False'
        self.connectionCounter = 15
        self.DefaultResponseTimeout = 0.3
        
        self.RootURL = 'http://{0}:{1}/'.format(ipAddress, port)
        if deviceUsername is not None and devicePassword is not None:
            self.authentication = b'Basic ' + base64.b64encode(deviceUsername.encode() + b':' + devicePassword.encode())
        else:
            self.authentication = None
        self.Opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler()) 

        self.Subscription = {}
        self.counter = 0
        self.connectionFlag = True
        self.initializationChk = True
        self.Debug = False
        self.IPAddress = ipAddress
        self.DefaultPort = port
        self.deviceUsername = deviceUsername
        self.devicePassword = devicePassword
        self.Models = {}
        
        self.Http_Port = port


        self.Commands = {
            'ConnectionStatus': {'Status': {}},
            'AnnounceByTCP': { 'Status': {}},
            'AnnounceHostString': {'Status': {}},
            'AnnounceNameString': {'Status': {}},
            'AnnouncePasswordString': {'Status': {}},
            'AnnouncePortString': {'Status': {}},
            'AnnounceUsernameString': {'Status': {}},
            'Broadcast': {'Parameters':['Channel'], 'Status': {}},
            'ChannelLayout': {'Parameters':['Channel'], 'Status': {}},
            'FirmwareVersion': { 'Status': {}},
            'PublishType': {'Parameters':['Channel'], 'Status': {}},
            'Recording': {'Parameters':['Channel'], 'Status': {}},
            'SetMPEGTSRTPUDPSettings': { 'Status': {}},
            'SetRTMPPushSettings': { 'Status': {}},
            'SetRTPUDPSettings': { 'Status': {}},
            'SetRTSPAnnounceSettings': { 'Status': {}},
            'Streaming': {'Parameters':['Channel'], 'Status': {}},
            'UnicastAddressString': {'Status': {}},
            'UnicastAudioPortString': {'Status': {}},
            'UnicastMPEGTSPortString': {'Status': {}},
            'UnicastVideoPortString': {'Status': {}},
        }


        self.FirmwareVersion = compile('firmware_version\s{0,1}=\s{0,1}FIRMWARE_VERSION="(.+?)"\s*')
        self.ChannelLayout = compile('active_layout\s*=\s*(\d+)')
        self.PublishType = compile('publish_type\s{0,1}=\s{0,1}([0-6])\s*')
        self.Recording = compile('rec_enabled\s*=\s*(on|)')
        self.Broadcast = compile('bcast_disabled\s*=\s*(on|)')
        self.stream = compile('publish_enabled\s*=\s*(on|off)')
            
        self.ipRegEx = compile('((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9]))')

        self.AnnounceByTCPCmdString = ''
        self.AnnounceHostString = ''
        self.AnnounceNameString = ''
        self.AnnouncePasswordString = ''
        self.AnnouncePortString = ''
        self.AnnounceUsernameString = ''
        self.UnicastAddressString = ''
        self.UnicastAudioPortString = ''
        self.UnicastMPEGTSPortString = ''
        self.UnicastVideoPortString = ''        

    def SetAnnounceByTCP(self, value, qualifier):

        ValueStateValues = {
            'On'  : 'on',
            'Off' : ''
        }

        self.AnnounceByTCPCmdString = ValueStateValues[value]
        
    def SetAnnounceHostString(self, value, qualifier):
        ValueConstraints = {
            'Min': 0,
            'Max': 15
        }

        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.AnnounceHostString = value
        else:
            print('Invalid String for SetAnnounceHostString')

    def SetAnnounceNameString(self, value, qualifier):
        self.AnnounceNameString = value

    def SetAnnouncePasswordString(self, value, qualifier):
        self.AnnouncePasswordString = value

    def SetAnnouncePortString(self, value, qualifier):
        ValueConstraints = {
            'Min': 4,
            'Max': 5
        }
        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.AnnouncePortString = value
        else:
            print('Invalid String for SetAnnouncePortString')

    def SetAnnounceUsernameString(self, value, qualifier):
        self.AnnounceUsernameString = value
        
    def SetBroadcast(self, value, qualifier):

        ValueStateValues = {
            'Enabled'   : '',
            'Disabled'  : 'on'
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10 and value in ValueStateValues:
            BroadcastCmdString = [Channel, 'bcast_disabled={0}'.format(ValueStateValues[value])]
            self.__SetUrlHelper('Broadcast', value, qualifier, url=BroadcastCmdString)
        else:
            self.Discard('Invalid Command for SetBroadcast')

    def UpdateBroadcast(self, value, qualifier):

        ValueStateValues = {
            ''   : 'Enabled',
            'on' : 'Disabled'
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10:
            BroadcastCmdString = [Channel, 'bcast_disabled']
            res = self.__UpdateUrlHelper('Broadcast', value, qualifier, url=BroadcastCmdString)
            if res:
                try:
                    mGroup = self.Broadcast.search(res)
                    value = ValueStateValues[mGroup.group(1)]
                    self.WriteStatus('Broadcast', value, qualifier)
                except (KeyError, IndexError, AttributeError):
                    self.Error(['Broadcast: Invalid/unexpected response'])

    def SetChannelLayout(self, value, qualifier):

        Channel = qualifier['Channel']        
        if 1 <= int(Channel) <= 10 and 0 <= int(value) <= 255:
            ChannelLayoutCmdStringParams = [Channel, 'active_layout={0}'.format(value)]
            self.__SetUrlHelper('ChannelLayout',value, qualifier, url=ChannelLayoutCmdStringParams)
        else:
            self.Discard('Invalid Command for SetChannelLayout')

    def UpdateChannelLayout(self, value, qualifier):

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10:
            ChannelLayoutCmdStringParams = [Channel, 'active_layout']
            res = self.__UpdateUrlHelper('ChannelLayout',value, qualifier, url=ChannelLayoutCmdStringParams)
            if res:
                try:
                    mGroup = self.ChannelLayout.search(res)
                    value = mGroup.group(1)
                    if 0 <= int(value) <= 255:
                        self.WriteStatus('ChannelLayout', value, qualifier)
                    else:
                        self.Error(['Channel Layout (Range): Invalid/unexpected response'])
                except (KeyError, IndexError, AttributeError, TypeError):
                    self.Error(['Channel Layout: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdateChannelLayout')

    def UpdateFirmwareVersion(self, value, qualifier):

        FirmwareVersionCmdStringParams = [0,'firmware_version']
        res = self.__UpdateUrlHelper('FirmwareVersion', value, qualifier, url=FirmwareVersionCmdStringParams)
        if res:
            try:
                mGroup = self.FirmwareVersion.search(res)
                value = mGroup.group(1)
                self.WriteStatus('FirmwareVersion', value, qualifier)
            except (KeyError, IndexError, AttributeError):
                self.Error(['Firmware: Invalid/unexpected response'])

    def SetPublishType(self, value, qualifier):

        ValueStateValues = {
            'Do not publish'                    : '0', 
            'Epiphan.tv'                        : '1', 
            'RTSP Announce'                     : '2', 
            'Multicast RTP/UDP'                 : '3', 
            'Multicast MPEG-TS over UDP'        : '4', 
            'Multicast MPEG-TS over RTP/UDP'    : '5', 
            'RTMP push'                         : '6'
        }

        Channel = qualifier['Channel']        
        if 1 <= int(Channel) <= 10 and value in ValueStateValues:
            PublishTypeCmdStringParams = [Channel, 'publish_type={0}'.format(ValueStateValues[value])]
            self.__SetUrlHelper('PublishType',value, qualifier, url=PublishTypeCmdStringParams)
        else:
            self.Discard('Invalid Command for SetPublishType')

    def UpdatePublishType(self, value, qualifier):

        ValueStateValues = {
            '0' : 'Do not publish', 
            '1' : 'Epiphan.tv', 
            '2' : 'RTSP Announce', 
            '3' : 'Multicast RTP/UDP', 
            '4' : 'Multicast MPEG-TS over UDP', 
            '5' : 'Multicast MPEG-TS over RTP/UDP', 
            '6' : 'RTMP push'
        }
        
        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10:
            PublishTypeCmdStringParams = [Channel, 'publish_type']
            res = self.__UpdateUrlHelper('PublishType',value, qualifier, url=PublishTypeCmdStringParams)
            if res:
                try:
                    mGroup = self.PublishType.search(res)
                    value = mGroup.group(1)
                    self.WriteStatus('PublishType', ValueStateValues[value], qualifier)
                except (KeyError, IndexError, AttributeError):
                    self.Error(['Publish Type: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdatePublishType')

    def SetRecording(self, value, qualifier):

        ValueStateValues = {
            'Enabled'   : 'on',
            'Disabled'  : ''
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10 and value in ValueStateValues:
            RecordingCmdStringParams = [Channel, 'rec_enabled={0}'.format(ValueStateValues[value])]
            self.__SetUrlHelper('Recording', value, qualifier, url=RecordingCmdStringParams)
        else:
            self.Discard('Invalid Command for SetRecording')

    def UpdateRecording(self, value, qualifier):

        ValueStateValues = {
            'on'    : 'Enabled',
            ''      : 'Disabled'
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10:
            RecordingCmdStringParams = [Channel, 'rec_enabled']
            res = self.__UpdateUrlHelper('Recording', value, qualifier, url=RecordingCmdStringParams)            
            if res:
                try:
                    mGroup = self.Recording.search(res)
                    value = ValueStateValues[mGroup.group(1)]
                    self.WriteStatus('Recording', value, qualifier)
                except (KeyError, IndexError, AttributeError):
                    self.Error(['Update Recording: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdateRecording')

    def SetSetMPEGTSRTPUDPSettings(self, value, qualifier):

        ValueConstraints = {
            'Min' : 1000,
            'Max' : 65535,
            'Not' : (5557,)
        }

        address = self.UnicastAddressString
        if address:
            try:
                ipRegExResult = self.ipRegEx.search(address)
                if ipRegExResult:
                    ip = ipRegExResult.group(0)
                    UnicastAddressCmdStringParams = ''.join(['unicast_address=', ip, '&'])
                else:
                    UnicastAddressCmdStringParams = ''
            except (KeyError, IndexError):
                    UnicastAddressCmdStringParams = ''             
        else:
            UnicastAddressCmdStringParams = ''
        
        MPort = self.UnicastMPEGTSPortString
        if MPort and 4 <= len(MPort) <= 5:
            try:
                if ValueConstraints['Min'] <= int(MPort) <= ValueConstraints['Max'] and \
                int(MPort) not in ValueConstraints['Not']:				
                    UnicastMPortCmdStringParams = ''.join(['unicast_mport=', MPort, '&'])
                else:
                    UnicastMPortCmdStringParams = ''
            except (KeyError, IndexError):
                UnicastMPortCmdStringParams = ''
        else:
            UnicastMPortCmdStringParams = '' 
        
        FullCmdString = ''.join([UnicastMPortCmdStringParams, UnicastAddressCmdStringParams])
        if FullCmdString and 1 <= int(value) <= 10:
            SetMPEGTSRTPUDPSettingsCmdString = [value, FullCmdString[:-1]]    
            self.__SetUrlHelper('SetMPEGTSRTPUDPSettings', value, qualifier, url=SetMPEGTSRTPUDPSettingsCmdString)
        else:
            self.Discard('Invalid Command for SetSetMPEGTSRTPUDPSettings')

    def SetSetRTMPPushSettings(self, value, qualifier):

        ValueConstraints = {
            'Min' : 1000,
            'Max' : 65535,
            'Not' : (5557,)
        }

        Host = self.AnnounceHostString
        if Host:
            try:
                ipRegExResult = self.ipRegEx.search(Host)
                if ipRegExResult:
                    ip = ipRegExResult.group(0)
                    HostCmdStringParams = ''.join(['announce_host=', ip, '&'])
                else:
                    HostCmdStringParams = ''
            except (KeyError, IndexError):
                    HostCmdStringParams = ''             
        else:
            HostCmdStringParams = ''
            
        AnnounceName = self.AnnounceNameString
        if AnnounceName:
            AnnounceNameCmdStringParams = ''.join(['announce_name=', AnnounceName, '&'])
        else:
            AnnounceNameCmdStringParams = ''
            
        Password = qualifier
        if Password:
            PasswordCmdStringParams = ''.join(['announce_password=' , Password, '&'])
        else:
            PasswordCmdStringParams = ''
            
        Port = self.AnnouncePortString
        if Port and 4 <= len(Port) <= 5:
            try:
                if ValueConstraints['Min'] <= int(Port) <= ValueConstraints['Max'] and \
                    int(Port) not in ValueConstraints['Not']:				
                    PortCmdStringParams = ''.join(['announce_port=', Port, '&'])
                else:
                    PortCmdStringParams = ''
            except (KeyError, IndexError):
                PortCmdStringParams = ''
        else:
            PortCmdStringParams = ''
            
        Username = self.AnnounceUsernameString
        if Username:
            UsernameCmdStringParams = ''.join(['announce_username=' , Username, '&'])
        else:
            UsernameCmdStringParams = ''

        FullCmdString = ''.join([HostCmdStringParams, AnnounceNameCmdStringParams, PasswordCmdStringParams, PortCmdStringParams, UsernameCmdStringParams])
        if FullCmdString and 1 <= int(value) <= 10:
            SetRTMPPushSettingsCmdString = [value, FullCmdString[:-1]]
            self.__SetUrlHelper('SetRTMPPushSettings', value, qualifier, url=SetRTMPPushSettingsCmdString)
        else:
            self.Discard('Invalid Command for SetSetRTMPPushSettings')

    def SetSetRTPUDPSettings(self, value, qualifier):

        ValueConstraints = {
            'Min' : 1000,
            'Max' : 65535,
            'Not' : (5557,)
        }
        
        address = self.UnicastAddressString
        if address:
            try:
                ipRegExResult = self.ipRegEx.search(address)
                if ipRegExResult:
                    ip = ipRegExResult.group(0)
                    UnicastAddressCmdStringParams = ''.join(['unicast_address=', ip, '&'])
                else:
                    UnicastAddressCmdStringParams = ''
            except (KeyError, IndexError):
                UnicastAddressCmdStringParams = ''             
        else:
            UnicastAddressCmdStringParams = ''
            
        AudioPort = self.UnicastAudioPortString
        if AudioPort and 4 <= len(AudioPort) <= 5:
            try:
                if ValueConstraints['Min'] <= int(AudioPort) <= ValueConstraints['Max'] and int(AudioPort) not in ValueConstraints['Not']:				
                    UnicastAudioCmdStringParams = ''.join(['unicast_aport=', AudioPort, '&'])
                else:
                    UnicastAudioCmdStringParams = ''
            except (KeyError, IndexError):
                UnicastAudioCmdStringParams = ''
        else:
            UnicastAudioCmdStringParams = '' 

        VideoPort = self.UnicastVideoPortString
        if VideoPort and 4 <= len(VideoPort) <= 5:
            try:
                if ValueConstraints['Min'] <= int(VideoPort) <= ValueConstraints['Max'] and int(VideoPort) not in ValueConstraints['Not']:				
                    UnicastVideoCmdStringParams = ''.join(['unicast_vport=', VideoPort, '&'])
                else:
                    UnicastVideoCmdStringParams = ''
            except (KeyError, IndexError):
                UnicastVideoCmdStringParams = ''
        else:
            UnicastVideoCmdStringParams = ''            
            
        FullCmdString = ''.join([UnicastAddressCmdStringParams, UnicastAudioCmdStringParams, UnicastVideoCmdStringParams])
        if FullCmdString and 1 <= int(value) <= 10:
            SetRTPUDPSettingsCmdString = [value, FullCmdString[:-1]]
            self.__SetUrlHelper('SetRTPUDPSettings', value, qualifier, url=SetRTPUDPSettingsCmdString)
        else:
            self.Discard('Invalid Command for SetSetRTPUDPSettings')

    def SetSetRTSPAnnounceSettings(self, value, qualifier):

        ValueConstraints = {
            'Min' : 1000,
            'Max' : 65535,
            'Not' : (5557,)
        }
        
        Host = self.AnnounceHostString
        if Host:
            try:
                ipRegExResult = self.ipRegEx.search(Host)
                if ipRegExResult:
                    ip = ipRegExResult.group(0)
                    HostCmdStringParams = ''.join(['announce_host=', ip, '&'])
                else:
                    HostCmdStringParams = ''
            except (KeyError, IndexError):
                HostCmdStringParams = ''             
        else:
            HostCmdStringParams = ''
            
        By_TCP = self.AnnounceByTCPCmdString
        if By_TCP:
            By_TCPCmdStringParams = ''.join(['announce_by_tcp=', By_TCP, '&'])
        else:
            By_TCPCmdStringParams = ''
            
        AnnounceName = self.AnnounceNameString
        if AnnounceName:
            AnnounceNameCmdStringParams = ''.join(['announce_name=', AnnounceName, '&'])
        else:
            AnnounceNameCmdStringParams = ''
            
        Password = self.AnnouncePasswordString
        if Password:
            PasswordCmdStringParams = ''.join(['announce_password=', Password, '&'])
        else:
            PasswordCmdStringParams = ''
            
        Port = self.AnnouncePortString
        if Port and 4 <= len(value) <= 5:
            try:
                if ValueConstraints['Min'] <= int(Port) <= ValueConstraints['Max'] and int(Port) not in ValueConstraints['Not']:				
                    PortCmdStringParams = ''.join(['announce_port=' , Port, '&'])
                else:
                    PortCmdStringParams = ''
            except (KeyError, IndexError):
                PortCmdStringParams = ''
        else:
            PortCmdStringParams = ''

        Username = self.AnnounceUsernameString
        if Username:
            UsernameCmdStringParams = ''.join(['announce_username=' , Username, '&'])
        else:
            UsernameCmdStringParams = ''
        
        FullCmdString = ''.join([HostCmdStringParams, By_TCPCmdStringParams, AnnounceNameCmdStringParams, PasswordCmdStringParams, PortCmdStringParams, UsernameCmdStringParams])
        if FullCmdString and 1 <= int(value) <= 10:
            SetRTSPAnnounceSettingsCmdString = [value, FullCmdString[:-1]]
            self.__SetUrlHelper('SetRTSPAnnounceSettings', value, qualifier, url=SetRTSPAnnounceSettingsCmdString)
        else:
            self.Discard('Invalid Command for SetSetRTSPAnnounceSettings')

    def SetStreaming(self, value, qualifier):

        ValueStateValues = {
            'On'  : 'on',
            'Off' : 'off'
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10 and value in ValueStateValues:
            StreamingCmdString = [Channel, 'publish_enabled={0}'.format(ValueStateValues[value])]
            self.__SetUrlHelper('Streaming', value, qualifier, url=StreamingCmdString)
        else:
            self.Discard('Invalid Command for SetStreaming')

    def UpdateStreaming(self, value, qualifier):

        ValueStateValues = {
            'on'  : 'On', 
            'off' : 'Off'
        }

        Channel = qualifier['Channel']
        if 1 <= int(Channel) <= 10:
            StreamingCmdString = [Channel, 'publish_enabled']
            res = self.__UpdateUrlHelper('Streaming', value, qualifier, url=StreamingCmdString)
            if res:
                try:
                    mGroup = self.stream.search(res)
                    value = ValueStateValues[mGroup.group(1)]
                    self.WriteStatus('Streaming', value, qualifier)
                except (KeyError, AttributeError):
                    self.Error(['Streaming: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdateStreaming')   
            
    def SetUnicastAddressString(self, value, qualifier):
        ValueConstraints = {
            'Min': 0,
            'Max': 15
        }

        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.UnicastAddressString = value
        else:
            print('Invalid String for SetUnicastAddressString')

    def SetUnicastAudioPortString(self, value, qualifier):
        ValueConstraints = {
            'Min': 4,
            'Max': 5
        }

        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.UnicastAudioPortString = value
        else:
            print('Invalid String for SetUnicastAudioPortString')

    def SetUnicastMPEGTSPortString(self, value, qualifier):
        ValueConstraints = {
            'Min': 4,
            'Max': 5
        }

        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.UnicastMPEGTSPortString = value
        else:
            print('Invalid String for SetUnicastMPEGTSPortString')

    def SetUnicastVideoPortString(self, value, qualifier):
        ValueConstraints = {
            'Min': 4,
            'Max': 5
        }

        if ValueConstraints['Min'] <= len(value) <= ValueConstraints['Max']:
            self.UnicastVideoPortString = value
        else:
            print('Invalid String for SetUnicastVideoPortString')
            

    def __CheckResponseForErrors(self, sourceCmdName, response):
        return response.read().decode()

    def __SetUrlHelper(self, command, value, qualifier, url, data=None, queryDisallowTime=0):

        rootURL = self.RootURL.replace('http', 'https') if self.Http_Port == 443 else self.RootURL
        channelStr = url[0]
        commandStr = url[1]
        url = 'admin/channel{0}/set_params.cgi?{1}'.format(channelStr, commandStr)
        req = urllib.request.Request('{0}{1}'.format(rootURL, url), method = 'GET')
        try:
            res = self.Opener.open(req)
        except urllib.error.HTTPError as err:
            self.Error(['{0} {1} - {2}'.format(command, err.code, err.reason)])
            res = b''
        except urllib.error.URLError as err:
            self.Error(['{0} {1}'.format(command, err.reason)])
            res = b''
        except Exception as err:
            res = b''
        else:
            if res.status not in (200, 202):
                self.Error(['{0} {1} - {2}'.format(command, res.status, res.msg)])
                res = b''
            else:
                res = self.__CheckResponseForErrors(command, res)

        return res
   
    def __UpdateUrlHelper(self, command, value, qualifier, url, data=None):

        rootURL = self.RootURL.replace('http', 'https') if self.Http_Port == 443 else self.RootURL
        channelStr = url[0]
        commandStr = url[1]
        url = 'admin/channel{0}/get_params.cgi?{1}'.format(channelStr,commandStr)
        req = urllib.request.Request('{0}{1}'.format(rootURL, url), method = 'GET')
        try:
            res = self.Opener.open(req)
        except urllib.error.HTTPError as err:
            self.Error(['{0} {1} - {2}'.format(command, err.code, err.reason)])
            res = b''
        except urllib.error.URLError as err:
            self.Error(['{0} {1}'.format(command, err.reason)])
            if command == 'FirmwareVersion':
                res = b''
        except Exception as err:
            if command == 'FirmwareVersion':
                res = b''
        else:
            if res.status not in (200, 202):
                self.Error(['{0} {1} - {2}'.format(command, res.status, res.msg)])
                res = b''
            else:
                res = self.__CheckResponseForErrors(command, res)

        return res
   
    def OnConnected(self):
        self.connectionFlag = True
        self.WriteStatus('ConnectionStatus', 'Connected')
        self.counter = 0


    def OnDisconnected(self):
        self.WriteStatus('ConnectionStatus', 'Disconnected')
        self.connectionFlag = False

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
                self.Subscription[command] = {'method':{}}
        
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
        
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
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
        if command in self.Subscription :
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
            Command = self.Commands[command]
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
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
        except:
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
            except:
                return None
        else:
            raise KeyError('Invalid command for ReadStatus: ' + command)


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


class DeviceSerialClass:
    def __init__(self):

        self.Unidirectional = 'False'
        self.connectionCounter = 15
        self.DefaultResponseTimeout = 0.3
        self.Subscription = {}
        self.counter = 0
        self.connectionFlag = True
        self.initializationChk = True
        self.Debug = False
        self.Models = {}


        self.Commands = {
            'ConnectionStatus': {'Status': {}},
            'ChannelLayout': {'Parameters':['Channel or Recorder'], 'Status': {}},
            'FreeSpace': { 'Status': {}},
            'Record': {'Parameters':['Channel or Recorder'], 'Status': {}},
            'RecordingStatus': {'Parameters':['Channel or Recorder'], 'Status': {}},
            'RecordingTime': {'Parameters':['Channel or Recorder'], 'Status': {}},
            'Snapshot': {'Parameters':['Channel or Recorder'], 'Status': {}},
        }
        
        self.regexExp = {
            'RecordingTime'     : re.compile(b'Rectime\.(\d{1,2}) (\d+)\r\n'),
            'FreeSpace'         : re.compile(b'Freespace (\d+)\r\n'),
            'RecordingStatus'   : re.compile(b'Status\.(\d{1,2}) (Stopped|Running|Uninitialized)\r\n')
        }
    def SetChannelLayout(self, value, qualifier):

        channel = qualifier['Channel or Recorder']

        if 0 <= int(value) <= 255:
            if channel == 'All':
                ChannelLayoutCmdString = 'active_layout={0}\n'.format(value)
                self.__SetHelper('ChannelLayout', ChannelLayoutCmdString, value, qualifier)
            elif 1 <= int(channel) <= 10:
                    ChannelLayoutCmdString = 'SET.{0}.active_layout={1}\n'.format(channel, value)
                    self.__SetHelper('ChannelLayout', ChannelLayoutCmdString, value, qualifier)
                    self.__SetHelper('ChannelLayout', 'SAVECFG\n', value, qualifier)
            else:
                self.Discard('Invalid Command for SetChannelLayout')
        else:
            self.Discard('Invalid Command for SetChannelLayout')


    def UpdateFreeSpace(self, value, qualifier):

        FreeSpaceCmdString = 'FREESPACE\n'
        res = self.__UpdateHelper('FreeSpace', FreeSpaceCmdString, value, qualifier)
        if res:
            try:
                match = re.search(self.regexExp['FreeSpace'], res)
                value = match.group(1).decode()
                self.WriteStatus('FreeSpace', value, qualifier)
            except (KeyError, IndexError, ValueError):
                self.Error(['Free Space: Invalid/unexpected response'])

    def SetRecord(self, value, qualifier):

        ValueStateValues = {
            'Start' : 'START', 
            'Stop' : 'STOP'
        }

        channel = qualifier['Channel or Recorder']
        if channel == 'All' and value in ValueStateValues:
            RecordCmdString = ValueStateValues[value] + '\n'
            self.__SetHelper('Record', RecordCmdString, value, qualifier)
        elif 1 <= int(channel) <= 10 and value in ValueStateValues:
            RecordCmdString = ValueStateValues[value] + '.{0}\n'.format(channel)
            self.__SetHelper('Record', RecordCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetRecord')
            
    def UpdateRecordingStatus(self, value, qualifier):

        ValueStateValues = {
            'Running'       : 'Running', 
            'Stopped'       : 'Stopped', 
            'Uninitialized' : 'Uninitialized'
        }

        channel = qualifier['Channel or Recorder']
        if 1 <= int(channel) <= 10:
            RecordingStatusCmdString = 'STATUS.{0}\n'.format(channel)
            res = self.__UpdateHelper('RecordingStatus', RecordingStatusCmdString, value, qualifier)
            if res:
                try:
                    qualifier = {}
                    match = re.search(self.regexExp['RecordingStatus'], res)
                    qualifier['Channel or Recorder'] = match.group(1).decode()
                    value = ValueStateValues[match.group(2).decode()]
                    self.WriteStatus('RecordingStatus', value, qualifier)
                except (KeyError, IndexError):
                    self.Error(['Recording Status: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdateRecordingStatus')

    def UpdateRecordingTime(self, value, qualifier):

        channel = qualifier['Channel or Recorder']
        if 1 <= int(channel) <= 10:
            RecordingTimeCmdString = 'RECTIME.{0}\n'.format(channel)
            res = self.__UpdateHelper('RecordingTime', RecordingTimeCmdString, value, qualifier)
            if res:
                try:
                    qualifier = {}
                    match = re.search(self.regexExp['RecordingTime'], res)
                    qualifier['Channel or Recorder'] = match.group(1).decode()
                    value = match.group(2).decode()
                    self.WriteStatus('RecordingTime', value, qualifier)
                except (KeyError, IndexError):
                    self.Error(['Recording Time: Invalid/unexpected response'])
        else:
            self.Discard('Invalid Command for UpdateRecordingTime')

    def SetSnapshot(self, value, qualifier):

        channel = qualifier['Channel or Recorder']
        if channel == 'All':
            SnapshotCmdString = 'SNAPSHOT\n'
            self.__SetHelper('Snapshot', SnapshotCmdString, value, qualifier)
        elif 1 <= int(channel) <= 10:
            SnapshotCmdString = 'SNAPSHOT.{0}\n'.format(channel)
            self.__SetHelper('Snapshot', SnapshotCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetSnapshot')
    def __CheckResponseForErrors(self, sourceCmdName, response):

        return response

    def __SetHelper(self, command, commandstring, value, qualifier):
        self.Debug = True

        if command == 'ChannelLayout' and 'SET' in commandstring:
            self.SendAndWait(commandstring, 0.1) #Customer Tested
        else:
            self.Send(commandstring)


    def __UpdateHelper(self, command, commandstring, value, qualifier):
    
        if self.initializationChk:
            self.OnConnected()
            self.initializationChk = False

        self.counter = self.counter + 1
        if self.counter > self.connectionCounter and self.connectionFlag:
            self.OnDisconnected()

        if self.Unidirectional == 'True':
            self.Discard('Inappropriate Command ' + command)
            return ''
        else:
            res = self.SendAndWait(commandstring, self.DefaultResponseTimeout)
            if not res:
                if command == 'FreeSpace':
                    return ''
            else:
                return self.__CheckResponseForErrors(command + ':' + commandstring.strip(), res)

            

    def OnConnected(self):
        self.connectionFlag = True
        self.WriteStatus('ConnectionStatus', 'Connected')
        self.counter = 0


    def OnDisconnected(self):
        self.WriteStatus('ConnectionStatus', 'Disconnected')
        self.connectionFlag = False

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
                self.Subscription[command] = {'method':{}}
        
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
        
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
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
        if command in self.Subscription :
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
            Command = self.Commands[command]
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
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
        except:
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
            except:
                return None
        else:
            raise KeyError('Invalid command for ReadStatus: ' + command)


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

class SerialClass(SerialInterface, DeviceSerialClass):

    def __init__(self, Host, Port, Baud=19200, Data=8, Parity='None', Stop=1, FlowControl='Off', CharDelay=0, Mode='RS232', Model =None):
        SerialInterface.__init__(self, Host, Port, Baud, Data, Parity, Stop, FlowControl, CharDelay, Mode)
        self.ConnectionType = 'Serial'
        DeviceSerialClass.__init__(self)
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

class SerialOverEthernetClass(EthernetClientInterface, DeviceSerialClass):

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Serial'
        DeviceSerialClass.__init__(self) 
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

class HTTPClass(DeviceHTTPClass):
    def __init__(self, ipAddress, port, deviceUsername=None, devicePassword=None, Model=None):
        self.ConnectionType = 'HTTP'
        DeviceHTTPClass.__init__(self, ipAddress, port, deviceUsername, devicePassword)
        # Check if Model belongs to a subclass      
        if len(self.Models) > 0:
            if Model not in self.Models:
                print('Model mismatch')             
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'IP Address/Host: {0}'.format(self.RootURL)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')
  
    def Discard(self, message):
        self.Error([message])