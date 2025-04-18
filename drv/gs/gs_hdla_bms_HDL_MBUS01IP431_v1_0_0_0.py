from extronlib.interface import SerialInterface, EthernetClientInterface
from extronlib.system import Wait, ProgramLog
from re import compile, search
from struct import pack


class DeviceClass:
    def __init__(self, Hostname):

        self.Debug = False
        self.Models = {}

        self.Commands = {
            'CurtainSwitch': {'Parameters': ['Target Subnet ID', 'Target Device ID', 'Number'], 'Status': {}},
            'Scene': {'Parameters': ['Target Subnet ID', 'Target Device ID', 'Area'], 'Status': {}},
            'Sequence': {'Parameters': ['Target Subnet ID', 'Target Device ID', 'Area'], 'Status': {}},
            'SingleChannel': {'Parameters': ['Target Subnet ID', 'Target Device ID', 'Channel Number', 'Running Time'], 'Status': {}},
            'UniversalSwitch': {'Parameters': ['Target Subnet ID', 'Target Device ID', 'Number'], 'Status': {}},
        }

        self._OriginalDeviceID = 0
        self._OriginalDeviceType = 65534
        self._OriginalSubnetID = 0
        
        self.OriginalIDs = pack('>2BH', int(self._OriginalSubnetID), int(self._OriginalDeviceID), int(self._OriginalDeviceType))

        controller_ip_address = Hostname
        if controller_ip_address:
            controller_ip_address = str(controller_ip_address).split('.')
            controller_ip_address = [int(a) for a in controller_ip_address]
        else:
            self.Error(['Missing or wrongly formulated Controller IP Address.'])

        self.CRC_TAB = (
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
        )

        if controller_ip_address:
            self.Header = b''.join([bytes(controller_ip_address), b'HDLMIRACLE\xAA\xAA'])

    @property
    def OriginalDeviceID(self):
        return self._OriginalDeviceID

    @OriginalDeviceID.setter
    def OriginalDeviceID(self, value):
        if 0 <= int(value) <= 254:
            self._OriginalDeviceID = int(value)
            if self._OriginalSubnetID and self._OriginalDeviceType:
                self.__SetOriginalID()
        else:
            self.Error(['Original Device ID should be a value between 0 to 254.'])

    @property
    def OriginalSubnetID(self):
        return self._OriginalSubnetID

    @OriginalSubnetID.setter
    def OriginalSubnetID(self, value):
        if 0 <= int(value) <= 254:
            self._OriginalSubnetID = int(value)
            if self._OriginalDeviceID and self._OriginalDeviceType:
                self.__SetOriginalID()
        else:
            self.Error(['Original Subnet ID should be a value between 0 to 254.'])

    @property
    def OriginalDeviceType(self):
        return self._OriginalDeviceType

    @OriginalDeviceType.setter
    def OriginalDeviceType(self, value):
        if 0 <= int(value) <= 65535:
            self._OriginalDeviceType = int(value)
            if self._OriginalSubnetID and self._OriginalDeviceID:
                self.__SetOriginalID()
        else:
            self.Error(['Original Device Type should be a value between 0 to 65535.'])

    def __SetOriginalID(self):
        if self._OriginalDeviceID:
            if self._OriginalSubnetID:
                if self.OriginalDeviceType:
                    self.OriginalIDs = pack('>2BH', int(self._OriginalSubnetID), int(self._OriginalDeviceID), int(self._OriginalDeviceType))
                else:
                    self.Error(['Please set Original Device Type variable.'])
            else:
                self.Error(['Please set Original Subnet ID variable.'])
        else:
            self.Error(['Please set Original Device Type variable.'])

    def __add_crc(self, buffer):
        crc = 0
        for buf_byte in buffer:
            data_byte = crc >> 8
            crc = (crc << 8) & 0xFFFF
            crc ^= self.CRC_TAB[data_byte ^ buf_byte]
        return b''.join([buffer, crc.to_bytes(2, 'big')])

    @staticmethod
    def __constraint_checker(*value_dicts):
        return all(map(lambda x: (x['Min'] <= x['Value'] <= x['Max']), value_dicts))

    def SetCurtainSwitch(self, value, qualifier):

        TargetSubnetIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Subnet ID']) if qualifier['Target Subnet ID'].isdigit() else -1,
        }

        TargetDeviceIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Device ID']) if qualifier['Target Device ID'].isdigit() else -1,
        }

        NumberConstraints = {
            'Min': 1,
            'Max': 16,
            'Value': int(qualifier['Number']) if qualifier['Number'].isdigit() else -1,
        }

        ValueStateValues = {
            'Stop': 0,
            'Open': 1,
            'Close': 2,
        }

        if value in ValueStateValues and self.__constraint_checker(TargetSubnetIDConstraints, TargetDeviceIDConstraints, NumberConstraints):
            target_ids = pack('>2B', TargetSubnetIDConstraints['Value'], TargetDeviceIDConstraints['Value'])
            cmd_str = b''.join([b'\x0D', self.OriginalIDs, b'\xE3\xE0', target_ids, NumberConstraints['Value'].to_bytes(1, 'big'), ValueStateValues[value].to_bytes(1, 'big')])
            CurtainSwitchCmdString = b''.join([self.Header, self.__add_crc(cmd_str)])
            self.__SetHelper('CurtainSwitch', CurtainSwitchCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetCurtainSwitch')

    def SetScene(self, value, qualifier):

        TargetSubnetIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Subnet ID']) if qualifier['Target Subnet ID'].isdigit() else -1,
        }

        TargetDeviceIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Device ID']) if qualifier['Target Device ID'].isdigit() else -1,
        }

        AreaConstraints = {
            'Min': 1,
            'Max': 255,
            'Value': int(qualifier['Area']) if qualifier['Area'].isdigit() else -1,
        }

        ValueConstraints = {
            'Min': 0,
            'Max': 255,
            'Value': int(value) if value.isdigit() else -1,
        }

        if self.__constraint_checker(TargetSubnetIDConstraints, TargetDeviceIDConstraints,
                                     AreaConstraints, ValueConstraints):
            target_ids = pack('>2B', TargetSubnetIDConstraints['Value'], TargetDeviceIDConstraints['Value'])
            cmd_str = b''.join([b'\x0D', self.OriginalIDs, b'\x00\x02', target_ids, AreaConstraints['Value'].to_bytes(1, 'big'), ValueConstraints['Value'].to_bytes(1, 'big')])
            SceneCmdString = b''.join([self.Header, self.__add_crc(cmd_str)])
            self.__SetHelper('Scene', SceneCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetScene')

    def SetSequence(self, value, qualifier):

        TargetSubnetIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Subnet ID']) if qualifier['Target Subnet ID'].isdigit() else -1,
        }

        TargetDeviceIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Device ID']) if qualifier['Target Device ID'].isdigit() else -1,
        }

        AreaConstraints = {
            'Min': 1,
            'Max': 255,
            'Value': int(qualifier['Area']) if qualifier['Area'].isdigit() else -1,
        }

        ValueConstraints = {
            'Min': 0,
            'Max': 255,
            'Value': int(value) if value.isdigit() else -1,
        }

        if self.__constraint_checker(TargetSubnetIDConstraints, TargetDeviceIDConstraints,
                                     AreaConstraints, ValueConstraints):
            target_ids = pack('>2B', TargetSubnetIDConstraints['Value'], TargetDeviceIDConstraints['Value'])
            cmd_str = b''.join([b'\x0D', self.OriginalIDs, b'\x00\x1A', target_ids,
                                AreaConstraints['Value'].to_bytes(1, 'big'),
                                ValueConstraints['Value'].to_bytes(1, 'big')])
            SequenceCmdString = b''.join([self.Header, self.__add_crc(cmd_str)])
            self.__SetHelper('Sequence', SequenceCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetSequence')

    def SetSingleChannel(self, value, qualifier):

        TargetSubnetIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Subnet ID']) if qualifier['Target Subnet ID'].isdigit() else -1,
        }

        TargetDeviceIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Device ID']) if qualifier['Target Device ID'].isdigit() else -1,
        }

        ChannelNumberConstraints = {
            'Min': 1,
            'Max': 255,
            'Value': int(qualifier['Channel Number']) if qualifier['Channel Number'].isdigit() else -1,
        }

        RunningTimeConstraints = {
            'Min': 0,
            'Max': 3600,
            'Value': int(qualifier['Running Time']) if qualifier['Running Time'] else -1,
        }

        ValueConstraints = {
            'Min': 0,
            'Max': 100,
            'Value': value,
        }

        if self.__constraint_checker(TargetSubnetIDConstraints, TargetDeviceIDConstraints, ChannelNumberConstraints,
                                     RunningTimeConstraints, ValueConstraints):
            target_ids = pack('>2B', TargetSubnetIDConstraints['Value'], TargetDeviceIDConstraints['Value'])
            rt_high = int(RunningTimeConstraints['Value'] / 256)
            rt_low = int(RunningTimeConstraints['Value'] % 256)
            cmd_str = b''.join([b'\x0F', self.OriginalIDs, b'\x00\x31', target_ids,
                                ChannelNumberConstraints['Value'].to_bytes(1, 'big'),
                                ValueConstraints['Value'].to_bytes(1, 'big'),
                                rt_high.to_bytes(1, 'big'), rt_low.to_bytes(1, 'big')])
            SingleChannelCmdString = b''.join([self.Header, self.__add_crc(cmd_str)])
            self.__SetHelper('SingleChannel', SingleChannelCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetSingleChannel')

    def SetUniversalSwitch(self, value, qualifier):

        TargetSubnetIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Subnet ID']) if qualifier['Target Subnet ID'].isdigit() else -1,
        }

        TargetDeviceIDConstraints = {
            'Min': 0,
            'Max': 254,
            'Value': int(qualifier['Target Device ID']) if qualifier['Target Device ID'].isdigit() else -1,
        }

        NumberConstraints = {
            'Min': 1,
            'Max': 255,
            'Value': int(qualifier['Number']) if qualifier['Number'].isdigit() else -1,
        }

        ValueStateValues = {
            'On': 255,
            'Off': 0,
        }

        if value in ValueStateValues and self.__constraint_checker(
                TargetSubnetIDConstraints, TargetDeviceIDConstraints, NumberConstraints):
            target_ids = pack('>2B', TargetSubnetIDConstraints['Value'], TargetDeviceIDConstraints['Value'])
            cmd_str = b''.join([b'\x0D', self.OriginalIDs, b'\xE0\x1C', target_ids,
                                NumberConstraints['Value'].to_bytes(1, 'big'),
                                ValueStateValues[value].to_bytes(1, 'big')])
            UniversalSwitchCmdString = b''.join([self.Header, self.__add_crc(cmd_str)])
            self.__SetHelper('UniversalSwitch', UniversalSwitchCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetUniversalSwitch')

    def __SetHelper(self, command, commandstring, value, qualifier):
        self.Debug = True
        self.Send(commandstring)

    ######################################################
    # RECOMMENDED not to modify the code below this point
    ######################################################

    # Send Control Commands
    def Set(self, command, value, qualifier=None):
        method = getattr(self, 'Set%s' % command)
        if method is not None and callable(method):
            method(value, qualifier)
        else:
            print(command, 'does not support Set.')


class EthernetClass(EthernetClientInterface, DeviceClass):

    def __init__(self, Hostname, IPPort, Protocol='UDP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Ethernet'
        DeviceClass.__init__(self, Hostname)
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
