

from Extron2.BaseDriver import BaseDriver
import re
import Extron.Timer as CallBackTimer
import time
from collections import defaultdict


class aten_31_2250(BaseDriver):
    """aten_31_2250

    Created on 05/18/2022 13:18:16

    Supported Models:
        PE5108
        PE5208
        PE6108
        PE6208
        PE7108
        PE7208
        PE8108
        PE8208

    DRIVER STYLE
        Asynchronous update command responses

    COMMAND STRUCTURE
        COMMAND DELIMITER:  \r\n
        COMMAND EXAMPLE:    read status o01 simple\r\n
        RESPONSE EXAMPLE:   read status o01 simple\r\non\r\n\r\n>

    COMMAND NOTES

    REVISION HISTORY
    Version     Date            Notes
    1_1_0       5/18/2022       Changed driver type from hybrid to async.
                                Removed Environmental Sensor Status.
                                Removed Power Measurement Value.
                                Added Humidity and Temperature.
                                Fixed Switch Outlet command.
                                DR# 64098

    1_0_2       04/27/2022      Added command: Environmental Sensor Status. DR# 63970
                                - Number of supported sensors, reference Pg 3, pe6108.pdf

    1_0_1       12/27/2021      Fixed response handling format.  DR# 63422
    
    1_0_0       06/22/2016      Initial Version DR# 47930
    """

################################################################
# INITIALIZATION
################################################################

    def __init__(self, configs):
        """Driver Constructor
        Read/set information passed in via configuration data.

        """
        super().__init__(configs)

        self.Commands = {
            'Heartbeat':                {'Set': False,  'Update': True,     'Live': True,   'Emulated': False,                                                      'Status': {}},
            'Humidity':                 {'Set': False,  'Update': True,     'Live': True,   'Emulated': False,  'Parameters': ['Sensor'],                           'Status': {}},
            'OutletSwitchStatus':       {'Set': False,  'Update': True,     'Live': True,   'Emulated': False,  'Parameters': ['Outlet'],                           'Status': {}},
            'SwitchOutlet':             {'Set': True,   'Update': False,    'Live': False,  'Emulated': False,  'Parameters': ['Outlet'],                           'Status': {}},
            'Temperature':              {'Set': False,  'Update': True,     'Live': True,   'Emulated': False,  'Parameters': ['Sensor'],                           'Status': {}},
            'UserDefinedCommand':       {'Set': True,   'Update': False,    'Live': False,  'Emulated': False,                                                      'Status': {}},
            'UserDefinedString':        {'Set': True,   'Update': False,    'Live': False,  'Emulated': True,                                                       'Status': {}}
        }

        self.lastResponse = 0
        self.lastSend = 0
        self.RequiredTimer = None

        initError = []

        self.Authenticated = False
        self.lastSensorUpdate = defaultdict(float)

        try:
            self.Unidirectional = configs['Unidirectional']
            if self.Unidirectional not in ['True', 'False']:
                initError.append('Unidirectional set to an invalid value: {0}'.format(configs['Unidirectional']))
        except KeyError:
            initError.append('Missing Unidirectional Parameter.')

        try:
            self.CommandPacing = configs['CommandPacing']
            if not 0 <= self.CommandPacing <= 30:
                initError.append('CommandPacing must be greater than or equal to 0 and less than or equal to 30')
        except KeyError:
            initError.append('Missing CommandPacing Parameter.')
        except TypeError:
            initError.append('CommandPacing Parameter is the wrong type.')

        try:
            self.DefaultResponseTimeout = configs['ResponseTimeout']
            if self.DefaultResponseTimeout <= 0:
                initError.append('ResponseTimeout must be greater than 0.')
        except KeyError:
            initError.append('Missing ResponseTimeout Parameter.')
        except TypeError:
            initError.append('ResponseTimeout Parameter is the wrong type.')

        try:
            self.deviceUsername = configs['DriverCredentials']['Username']
        except KeyError:
            initError.append('Missing Username in DriverCredentials.')
        except TypeError:
            initError.append('Username Parameter is the wrong type.')

        try:
            self.devicePassword = configs['DriverCredentials']['Password']
        except KeyError:
            initError.append('Missing Password in DriverCredentials.')
        except TypeError:
            initError.append('Password Parameter is the wrong type.')

        if initError:
            self.Error(initError)
            self.Disable()
        elif self.Unidirectional == 'False':
            self.AddMatchString(re.compile(b'read sensor o0([12]) simple\s+(.+?)\s+(.+?)\s+'), self.__MatchHumidity, None)
            self.AddMatchString(re.compile(b'read status o0([1-8]) simple\s+(on|off|pending|pop)'), self.__MatchOutletSwitchStatus, None)
            self.AddMatchString(re.compile(b'Not Support|Invalid command or exceed max command length'), self.__MatchError, None)

            self.AddMatchString(re.compile(b'Login:'), self.__MatchUsername, None)
            self.AddMatchString(re.compile(b'Password:'), self.__MatchPassword, None)
            self.AddMatchString(re.compile(b'Logged in successfully'), self.__MatchTelnetSuccess, None)
            self.AddMatchString(re.compile(b'Incorrect user name or password!'), self.__MatchTelnetFail, None)

################################################################
###
################################################################

    def __MatchUsername(self, match, tag):
        self.DriverCmd('SetUsername', None, None)

    def _cmd_SetUsername(self, value, qualifier):
        self.Send(self.deviceUsername + '\r\n')
    
    def __MatchPassword(self, match, tag):
        self.DriverCmd('SetPassword', None, None)

    def _cmd_SetPassword(self, value, qualifier):
        self.Send(self.devicePassword + '\r\n')

    def __MatchTelnetSuccess(self, match, tag):
        self.Authenticated = True
    
    def __MatchTelnetFail(self, match, tag):
        self.Authenticated = False
        self.Error(['Failed to log in. Please verify login credentials.'])

################################################################
### BEGIN AUTO GENERATION OF COMMAND DEF
################################################################

    # Begin Heartbeat
    ####################################################################################################################
    #
    def _cmd_UpdateHeartbeat(self, value, qualifier):
        """Update Heartbeat
        value: None
        qualifier: None

        """
        if self.RequiredTimer:
            self.RequiredTimer.DeleteTimer()

        HeartbeatCmdString = 'read status o01 simple\r\n'
        if self.__UpdateHelper('Heartbeat', HeartbeatCmdString, value, qualifier):
            self.lastSend = time.monotonic()
            self.RequiredTimer = CallBackTimer.Timer(self.DefaultResponseTimeout, self.__ResponseTimeout, None, False, [])

    # Begin Humidity
    ####################################################################################################################
    #
    def _cmd_UpdateHumidity(self, value, qualifier):
        """Update Humidity
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        sensor = int(qualifier['Sensor'])

        if 1 <= sensor <= 2:
            ctime = time.monotonic()
            if ctime - self.lastSensorUpdate[sensor] > 3:
                self.lastSensorUpdate[sensor] = ctime

                HumidityCmdString = 'read sensor o0{} simple\r\n'.format(sensor)
                self.__UpdateHelper('Humidity', HumidityCmdString, value, qualifier)
            else:
                self.Discard('Device Is Busy')
        else:
            self.Discard('Invalid Command')

    def __MatchHumidity(self, match, tag):
        """Humidity MatchString Handler

        """
        qualifier = {
            'Sensor': match.group(1).decode()
        }

        humidity = match.group(3).decode().strip()
        if humidity != 'NA':
            self.WriteHumidity(float(humidity), qualifier, 'Live')
        else:
            self.WriteHumidity(-1.0, qualifier, 'Live')

        temperature = match.group(2).decode().strip()
        if temperature != 'NA':
            self.WriteTemperature(float(temperature), qualifier, 'Live')
        else:
            self.WriteTemperature(-1.0, qualifier, 'Live')

    def WriteHumidity(self, value, qualifier, context):
        """Write Humidity
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        self.WriteStatusHelper('Humidity', value, qualifier, context)

    def ReadHumidity(self, qualifier, context):
        """Read Humidity
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        return self.ReadStatusHelper('Humidity', qualifier, context)

    # Begin Outlet Switch Status
    ####################################################################################################################
    #
    def _cmd_UpdateOutletSwitchStatus(self, value, qualifier):
        """Update Outlet Switch Status
        value: Enum
        qualifier: {'Outlet': Enum}

        """
        outlet = int(qualifier['Outlet'])

        # Outlet #1 is updated by Heartbeat
        if 2 <= outlet <= 8:
            OutletSwitchStatusCmdString = 'read status o0{} simple\r\n'.format(outlet)
            self.__UpdateHelper('OutletSwitchStatus', OutletSwitchStatusCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command')

    def __MatchOutletSwitchStatus(self, match, tag):
        """Outlet Switch Status MatchString Handler

        """
        qualifier = {
            'Outlet': match.group(1).decode()
        }

        if qualifier['Outlet'] == '1':
            self.lastResponse = time.monotonic()
            self.WriteDeviceResponseStatus('Good', None, 'Live')

        value = match.group(2).decode().title()
        self.WriteOutletSwitchStatus(value, qualifier, 'Live')

    def WriteOutletSwitchStatus(self, value, qualifier, context):
        """Write Outlet Switch Status
        value: Enum
        qualifier: {'Outlet': Enum}

        """
        self.WriteStatusHelper('OutletSwitchStatus', value, qualifier, context)

    def ReadOutletSwitchStatus(self, qualifier, context):
        """Read Outlet Switch Status
        value: Enum
        qualifier: {'Outlet': Enum}

        """
        return self.ReadStatusHelper('OutletSwitchStatus', qualifier, context)

    # Begin Switch Outlet
    ####################################################################################################################
    #
    def _cmd_SetSwitchOutlet(self, value, qualifier):
        """Set Switch Outlet
        value: Enum
        qualifier: {'Outlet': Enum}

        """
        outlet = int(qualifier['Outlet'])

        ValueStateValues = {
            'On':          'on imme',
            'On (delay)':  'on delay',
            'Off':         'off imme',
            'Off (delay)': 'off delay',
            'Reboot':      'reboot'
        }

        if 1 <= outlet <= 8 and value in ValueStateValues:
            SwitchOutletCmdString = 'sw o0{} {}\r\n '.format(outlet, ValueStateValues[value])
            if self.__SafeToSet('SwitchOutlet'):
                self.__SetHelper('SwitchOutlet', SwitchOutletCmdString, value, qualifier, 10)
        else:
            self.Discard('Invalid Command')

    # Begin Temperature
    ####################################################################################################################
    #
    def _cmd_UpdateTemperature(self, value, qualifier):
        """Update Temperature
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        self._cmd_UpdateHumidity(value, qualifier)

    def WriteTemperature(self, value, qualifier, context):
        """Write Temperature
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        self.WriteStatusHelper('Temperature', value, qualifier, context)

    def ReadTemperature(self, qualifier, context):
        """Read Temperature
        value: Decimal
        qualifier: {'Sensor': Enum}

        """
        return self.ReadStatusHelper('Temperature', qualifier, context)

    # Begin User Defined Command
    ####################################################################################################################
    #
    def _cmd_SetUserDefinedCommand(self, value, qualifier):
        cmdstring = self.ReadUserDefinedString(qualifier, 'Emulated')
        if cmdstring:
            cmdstring = cmdstring.encode(encoding='iso-8859-1')
            self.__SetHelper('UserDefinedCommand', cmdstring, None, None)

    # Begin User Defined String
    ####################################################################################################################
    #
    def _cmd_SetUserDefinedString(self, value, qualifier):
        """Set User Defined String
        value: String
        qualifier: None

        """
        self.WriteUserDefinedString(value, qualifier, 'Emulated')

    def WriteUserDefinedString(self, value, qualifier, context):
        """Write User Defined String
        value: String
        qualifier: None

        """
        self.WriteStatusHelper('UserDefinedString', value, qualifier, context)

    def ReadUserDefinedString(self, qualifier, context):
        """Read User Defined String
        value: String
        qualifier: None

        """
        return self.ReadStatusHelper('UserDefinedString', qualifier, context)

################################################################
### END AUTO GENERATION OF COMMAND DEF
################################################################

    def __SafeToSet(self, command):
        return True

    def __SetHelper(self, command, commandstring, value, qualifier, queryDisallowTime=0):
        """Set Helper
        This function is used to determine how to send.

        """
        self.Send(commandstring)
        if queryDisallowTime > 0:
            self.StartQueryDelayTimer(queryDisallowTime)

    def __UpdateHelper(self, command, commandstring, value, qualifier):
        """Update Helper
        This function is used to determine how to send.

        """
        result = False

        if self.Authenticated:
            if self.QueryDelayTimerIsRunning():
                self.Discard('Device Is Busy')
            elif self.Unidirectional == 'True':
                self.Discard('Inappropriate Command')
            else:
                result = True
                self.Send(commandstring)
                self.WriteStatusHelper(command, value, qualifier, 'UpdateTime')
        else:
            self.Discard('Inappropriate Command')
        
        return result

    def __MatchError(self, match, tag):
        """Check Response For Errors
        Called by all SendAndWait calls to the device.
        Device will always have a response...confirmation, errors or answer to queries

        """
        value = match.group(0).decode()
        self.Error(['An error occurred: {}.'.format(value)])

    def __ResponseTimeout(self):
        """ResponseTime
        method will compare the last send time and the last response time. if the response time
        took longer than the defaultresponsetimeout then it would set the status response to bad

        """
        if self.lastSend != 0:
            if self.lastResponse < self.lastSend or (self.lastResponse - self.lastSend) > self.DefaultResponseTimeout:
                self.WriteDeviceResponseStatus('Bad', None, 'Live')

    def OnConnected(self):
        """
        On Connected
        This callback will be set by the firmware when a device has connected or
        reconnected to the device.  It's called after a successful response (sync)
        or matchstring (async) via the self.DriverResponseStatus property

        """
        pass

    def OnDisconnected(self):
        """
        On Disconnected
        This callback will be set by the firmware when a device has not responded
        or malformed responed for <n> seconds as indicated in the driver
        descriptor.  Behavior is to set all status to their uninitialized state.

        """
        self.lastSend = 0
        self.lastResponse = 0
        self.__ResetLiveStatus()

        self.Authenticated = False
        self.lastSensorUpdate = defaultdict(float)

################################################################
### HELPER METHODS SECTION
################################################################

    def WriteStatusHelper(self, command, value, qualifier, context):
        """
        Write Status Helper
        Wrapper method to manage setting/posting Live and Emulated status

        """
        Command = self.Commands[command]
        if Command['Live'] or Command['Emulated']:
            Status = Command['Status']
            with self.Mutex():
                if 'Parameters' in Command:
                    for Parameter in Command['Parameters']:
                        try:
                            Status = Status[qualifier[Parameter]]
                        except KeyError:
                            if Parameter in qualifier:
                                Status[qualifier[Parameter]] = {}
                                Status = Status[qualifier[Parameter]]
                            else:
                                self.Error(['Invalid parameter(s): {0}'.format(qualifier)])
                                return
                try:
                    if context in ['Live', 'Emulated']:
                        Status['TimeStamps'][context] = ExtronTime(time.monotonic())
                        if Status[context] != value:
                            Status[context] = value
                            self.PostNewStatusEx(command, value, qualifier, context)
                    elif context == 'UpdateTime':
                        try:
                            Status['TimeStamps']['Update'] = ExtronTime(time.monotonic())
                        except KeyError:
                            Status['TimeStamps'] = {'Update': ExtronTime(time.monotonic())}
                    elif context == 'Meta':
                        Status['Meta'] = value

                except:
                    Status['Emulated'] = value
                    if 'TimeStamps' not in Status:
                        Status['TimeStamps'] = {}
                    Status['TimeStamps']['Emulated'] = ExtronTime(time.monotonic())
                    self.PostNewStatusEx(command, value, qualifier, 'Emulated')
                    if context == 'Live':
                        Status['Live'] = value
                        Status['TimeStamps']['Live'] = ExtronTime(time.monotonic())
                        self.PostNewStatusEx(command, value, qualifier, 'Live')
                    else:
                        Status['Live'] = None
                        Status['TimeStamps']['Live'] = None
        else:
            self.Error(['Command, {0}, does not have status.'.format(command)])
            return

    def ReadStatusHelper(self, command, qualifier, context):
        """
        Read Status Helper
        Wrapper method to return current status Live or Emulated

        """
        Command = self.Commands[command]
        if Command['Live'] or Command['Emulated']:
            Status = Command['Status']
            with self.Mutex():
                if 'Parameters' in Command:
                    for Parameter in Command['Parameters']:
                        try:
                            Status = Status[qualifier[Parameter]]
                        except KeyError:
                            return None
                try:
                    return Status[context]
                except:
                    return None
        else:
            self.Error(['Command, {0}, does not have status.'.format(command)])
            return

    def __StatusItems(self, dictionary):
        """Iterator Function to 'yield' all of the Live/Emulated pairs

        """
        for k, v in dictionary.items():
            if k == 'Live' and not isinstance(dictionary['Live'], dict) and not isinstance(dictionary['Live'], ExtronTime):
                yield [], dictionary
            elif isinstance(v, dict):
                for subkey, result in self.__StatusItems(v):
                    yield [k]+subkey, result

    def _cmd_SetSyncEmulatedStatus(self, value, qualifier):
        """
        Synchronize All Emulated Status
        This command is issued by the automation script to cause a driver to sync
        all Emulated Feedback status to the authoritative Live feedback information.
        For each Emulated Feedback field that is out of date, change notification
        should be generated.
        value:  None
        qualifier:  None

        """
        with self.Mutex():
            if value in self.Commands:
                Command = self.Commands[value]
                if Command['Live'] and Command['Emulated']:
                    Status = Command['Status']
                    if 'Parameters' in Command:
                        for Parameter in Command['Parameters']:
                            try:
                                Status = Status[qualifier[Parameter]]
                            except KeyError:
                                if Parameter not in qualifier:
                                    self.Error(['Invalid parameter(s): {0}'.format(qualifier)])
                                    return
                    try:
                        if Status['Live'] is not None and Status['Live'] != Status['Emulated'] and Status['TimeStamps']['Live'] > Status['TimeStamps']['Emulated']:
                            Status['Emulated'] = Status['Live']
                            self.PostNewStatusEx(value, Status['Live'], qualifier, 'Emulated')
                    except:
                        pass
            else:
                self.Error(['Invalid Command: {0}'.format(value)])

    def StatusRefresh(self):
        """
        Status Refresh
        This command is called by the automation script when it needs a driver to
        to generate a Refresh of status for soft clients.

        """
        self.PostNewStatusEx('RefreshBegin', None, None, 'Live')
        with self.Mutex():
            for command in self.Commands:
                Command = self.Commands[command]
                for Parameters, Status in self.__StatusItems(Command['Status']):
                    qualifier = {}
                    for Parameter in range(len(Parameters)):
                        qualifier[Command['Parameters'][Parameter]] = Parameters[Parameter]
                    self.PostNewStatusEx(command, Status['Live'], qualifier, 'LiveRefresh')
                    self.PostNewStatusEx(command, Status['Emulated'], qualifier, 'EmulatedRefresh')
        super().StatusRefresh()
        self.PostNewStatusEx('RefreshComplete', None, None, 'Live')

    def __ResetLiveStatus(self):
        """
        Reset Status to Uninitialized
        This function is call when OnDisconnected is call to reset all the Live status.

        """
        with self.Mutex():
            for command in self.Commands:
                Command = self.Commands[command]
                if Command['Live']:
                    for _, Status in self.__StatusItems(Command['Status']):
                        Status['Live'] = None

    #Parent Class overloads
    def SendAndWait(self, data, timeout, **kwds):
        """Send and Wait
        Overload to handle bytes translation. If the data is a string then the data returned
        from the device will be a string. If the data sent is a byte string, then
        the data returned from the device will be a byte string.

        """
        if isinstance(data, str):
            data = data.encode(encoding = 'iso-8859-1')
            IsString = True
        else:
            IsString = False
        try:
            kwds['deliTag'] = kwds['deliTag'].encode(encoding = 'iso-8859-1')
        except:
            pass
        if IsString:
            check = super().SendAndWait(data, timeout, **kwds)
            if check:
                return check.decode()
            else:
                return ''
        else:
            return super().SendAndWait(data, timeout, **kwds)

    def Send(self, data, **kwds):
        """Send
        Overload to handle bytes translation.

        """
        if isinstance(data, str):
            data = data.encode(encoding = 'iso-8859-1')
        super().Send(data, **kwds)


class ExtronTime(float):
    pass
