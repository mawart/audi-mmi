import struct
import serial

mmiUnitEvent = {
    0xfe: 'off',
    0xfa: 'on'
}
mmiUnitLights = {
    0xe6: 'INFO',
    0xf3: 'INFO',
    0xea: 'NAV',
    0xf5: 'NAV',
    0xde: 'SETUP',
    0xef: 'SETUP',
    0xee: 'TEL',
    0xf7: 'TEL',
    0xf2: 'NAME',
    0xf9: 'NAME',
    0xf6: 'MEDIA',
    0xfb: 'MEDIA',
    0xe2: 'CAR',
    0xf1: 'CAR',
    0x9e: 'RADIO',
    0xcf: 'RADIO'
}

class MmiHeadUnit:
    # public:
    def __init__(self, port, bufferSize):
        self._serial = serial.Serial(
            port=port,
            baudrate=9600,
            stopbits=serial.STOPBITS_TWO,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS
        )
        self._buffer = [0x00 for _ in range(bufferSize)]
        self._bufferSize = bufferSize

    def update(self, mmiCallback):
        # reset buffer and arrays
        self._buffer = [0x00 for _ in range(self._bufferSize)]
        payload = []
        serial_data = []
        # read all data from serial input buffer
        while (self._serial.in_waiting > 0 and self._readIndex < self._bufferSize):
            data = self._serial.read()  # read one byte
            data = struct.unpack('B', data)[0]  # convert to number
            serial_data.append(data)

        # if serial data has been received, but no packet was detected signal the serial event with a dummy payload
        if (len(serial_data) > 0 and len(payload) == 0):
            self.serialEvent([0x00], serial_data, mmiCallback)

# private:
    _serial = None
    _buffer = []
    _bufferSize = 0

    _startIndex = -1
    _endIndex = -1
    _readIndex = 0

    def write_raw(self, data):
        self._serial.write(data)
        self._serial.flush()

    def write(self, data):
        length = len(data)
        # initialize message buffer
        message = [0x00 for _ in range(length + 5)]
        # set first two start bytes
        message[0] = 0x10
        message[1] = 0x02
        # initialize checksum value (sum of start and end bytes)
        checksum = 0x25
        # fill message buffer with data and calculate checksum value
        for i in range(length):
            checksum += data[i]
            message[2+i] = data[i]
        # set last two end bytes
        message[2+length] = 0x10
        message[3+length] = 0x03
        # add checksum value
        message[4+length] = checksum & 0xFF  # truncate to one byte
        # write message
        self._serial.write(message)
        self._serial.flush()

    def ack(self):
        self._serial.write(0x06)
        self._serial.flush()

    def serialEvent(self, payload, serial_data, mmiCallback):
        length = len(payload)
        if (length > 1):
            mmiCallback(payload[1], payload[0] == 0xFA, serial_data)
        else:
            # unmapped event
           mmiCallback(None, None, serial_data)


# def update():
#     serial_data = []
#     while (mmiUnit_serial.in_waiting > 0):
#         data = mmiUnit_serial.read()
#         data = struct.unpack('B', data)[0]
#         serial_data.append(data)
    
#     length = len(serial_data)
#     if(length > 0):    
#         if(serial_data[0] == 0x67 and length > 1 and serial_data[1] == 0x5e):
#             remainder = [serial_data[i] for i in range(4, length)]
#             print('mmi unit mode switch', mmiUnitEvent[serial_data[2]], mmiUnitLights[serial_data[3]] if serial_data[3] in mmiUnitLights else hex(serial_data[3]), asHex(remainder))
#         else:
#             print_debug('mmi unit data received', asHex(serial_data))

#         mmiControl.write_raw(serial_data)