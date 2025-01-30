from extronlib.interface import SerialInterface, EthernetClientInterface
from re import compile, search
from extronlib.system import Wait, ProgramLog
from struct import pack
from functools import reduce
from operator import add

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
        self.Models = {}
        self.Commands = {
            'ConnectionStatus': {'Status': {}},
            'Handshake': { 'Status': {}},
            'Model': { 'Status': {}},
            'OSD': { 'Status': {}},
            'Preset': {'Parameters': ['Command'], 'Status': {}},
            'Scene': { 'Status': {}},
            'Switch': { 'Status': {}},
            'Take': { 'Status': {}},
        }



        self.driver_sequence_counter = SequenceCounter()

        if self.Unidirectional == 'False':
            self.AddMatchString(compile(b'\xAA\x55\x00[\x00-\xFF]\x00\xFE\x00{7}\x10\x00\x13\x05\x00{6}[\x00-\xFF]{2}'),
                                self.__MatchHandshake, None)
    @staticmethod
    def calc_checkout(message):

        chk = (reduce(add, message[2:]) + 0x5555) & 0xFFFF
        return pack('<H', chk)

    @staticmethod
    def __constraint_checker(*value_dicts):
        return all(map(lambda x: (x['Min'] <= x['Value'] <= x['Max']), value_dicts))

    def UpdateHandshake(self, value, qualifier):

        HandshakeCmdString = b''.join([b'\x55\xAA\x00',
                                       self.driver_sequence_counter.sequence_counter,
                                       b'\xFE\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x13\x05\x00'])
        HandshakeCmdString = b''.join([HandshakeCmdString, self.calc_checkout(HandshakeCmdString)])
        self.__UpdateHelper('Handshake', HandshakeCmdString, value, qualifier)

    def __MatchHandshake(self, match, tag):
        self.connectionFlag = True  
        self.OnConnected()        

    def SetModel(self, value, qualifier):

        ValueStateValues = {
            'Switch':  b'\x01',
            'Splicer': b'\x00',
        }

        if value in ValueStateValues:
            ModelCmdString = b''.join([b'\x55\xAA\x00',
                                       self.driver_sequence_counter.sequence_counter,
                                       b'\xFE\x00\x00\x00\x00\x00\x01\x00\x2C\x00\x00\x13\x01\x00',
                                       ValueStateValues[value]])
            ModelCmdString = b''.join([ModelCmdString, self.calc_checkout(ModelCmdString)])
            self.__SetHelper('Model', ModelCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetModel')

    def SetOSD(self, value, qualifier):

        ValueStateValues = {
            'Open':  b'\x01',
            'Close': b'\x00',
        }

        if value in ValueStateValues:
            OSDCmdString = b''.join([b'\x55\xAA\x00',
                                     self.driver_sequence_counter.sequence_counter,
                                     b'\xFE\x00\x00\x00\x00\x00\x01\x00\x1F\x00\x00\x13\x01\x00',
                                     ValueStateValues[value]])
            OSDCmdString = b''.join([OSDCmdString, self.calc_checkout(OSDCmdString)])
            self.__SetHelper('OSD', OSDCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetOSD')

    def SetPreset(self, value, qualifier):

        CommandStates = {
            'Load': b'\x00',
            'Save': b'\x02',
        }

        ValueConstraints = {
            'Min':   1,
            'Max':   16,
            'Value': int(value) if value.isdigit() else -1,
        }

        cmd = qualifier['Command']
        if self.__constraint_checker(ValueConstraints) and cmd in CommandStates:
            PresetCmdString = b''.join([b'\x55\xAA\x00',
                                        self.driver_sequence_counter.sequence_counter,
                                        b'\xFE\x00\x00\x00\x00\x00\x01\x00',
                                        CommandStates[cmd], b'\x01\x51\x13\x01\x00',
                                        pack('B', ValueConstraints['Value'] - 1)])
            PresetCmdString = b''.join([PresetCmdString, self.calc_checkout(PresetCmdString)])
            self.__SetHelper('Preset', PresetCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetPreset')

    def SetScene(self, value, qualifier):

        ValueConstraints = {
            'Min':   1,
            'Max':   16,
            'Value': int(value) if value.isdigit() else -1,
        }

        if self.__constraint_checker(ValueConstraints):
            SceneCmdString = b''.join([b'\x55\xAA\x00',
                                       self.driver_sequence_counter.sequence_counter,
                                       b'\xFE\x00\x00\x00\x00\x00\x01\x00\x20\x00\x00\x13\x01\x00',
                                       pack('B', ValueConstraints['Value'] - 1)])
            SceneCmdString = b''.join([SceneCmdString, self.calc_checkout(SceneCmdString)])
            self.__SetHelper('Scene', SceneCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetScene')

    def SetSwitch(self, value, qualifier):

        SwitchCmdString = b''.join([b'\x55\xAA\x00',
                                    self.driver_sequence_counter.sequence_counter,
                                    b'\xFE\x00\x00\x00\x00\x00\x01\x00\x2D\x00\x00\x13\x01\x00\x01'])
        SwitchCmdString = b''.join([SwitchCmdString, self.calc_checkout(SwitchCmdString)])
        self.__SetHelper('Switch', SwitchCmdString, value, qualifier)
    def SetTake(self, value, qualifier):

        TakeCmdString = b''.join([b'\x55\xAA\x00',
                                  self.driver_sequence_counter.sequence_counter,
                                  b'\xFE\x00\x00\x00\x00\x00\x01\x00\x2D\x00\x00\x13\x01\x00\x00'])
        TakeCmdString = b''.join([TakeCmdString, self.calc_checkout(TakeCmdString)])
        self.__SetHelper('Take', TakeCmdString, value, qualifier)

    def __SetHelper(self, command, commandstring, value, qualifier):
        self.Debug = True
        self.Send(commandstring)

    def __UpdateHelper(self, command, commandstring, value, qualifier):

        if self.Unidirectional == 'True':
            self.Discard('Inappropriate Command ' + command)
        else:            
            if self.initializationChk:
                self.OnConnected()
                self.initializationChk = False

            self.counter = self.counter + 1
            if self.counter > self.connectionCounter and self.connectionFlag:
                self.OnDisconnected()
            self.Send(commandstring)

    def OnConnected(self):   
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

    def __ReceiveData(self, interface, data):
        # Handle incoming data
        self.__receiveBuffer += data
        index = 0    # Start of possible good data
        
        #check incoming data if it matched any expected data from device module
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
            self.__matchStringDict[regex_string] = {'callback': callback, 'para':arg}


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



class SequenceCounter(object):

    _sequence_counter = None

    @property
    def sequence_counter(self):
        if ((not self._sequence_counter and not self._sequence_counter == 0) or
                self._sequence_counter < 0):
            self._sequence_counter = 0
        else:
            self._sequence_counter += 1
        return pack('B', self._sequence_counter & 0xFF)

    @sequence_counter.setter
    def sequence_counter(self, value):
        if value < 0:
            value = 0
        self._sequence_counter = value

    def decrement(self, value=1):
        self._sequence_counter -= value
