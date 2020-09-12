from components.mmiButton import MmiButtonInput, MmiButton
from components.mmiWheel import MmiWheel
from components.mmiLight import MmiLight
import struct
import serial

# 0x35: Triggered after the MMI was fully activated
# 0x38: Power button is pressed
# 0xff: Power is turned on (12v)


class MmiEvents:
    MMI_ACTIVATED = 0x35
    POWER_BTN_PRESSED = 0x38
    ACC_12V_ON = 0xff
    BTN_PRESSED = 0x30
    BTN_RELEASED = 0x31
    SMALL_WHEEL_ROTATED_RIGHT = 0x40
    SMALL_WHEEL_ROTATED_LEFT = 0x41
    BIG_WHEEL_ROTATED_RIGHT = 0x50
    BIG_WHEEL_ROTATED_LEFT = 0x51


EVENT_DESCRIPTIONS = {
    MmiEvents.MMI_ACTIVATED: 'Triggered after the MMI was fully activated',
    MmiEvents.POWER_BTN_PRESSED: 'Power button is pressed',
    MmiEvents.ACC_12V_ON: 'Power is turned on (12v)',
    MmiEvents.BTN_PRESSED: 'Button pressed',
    MmiEvents.BTN_RELEASED: 'Button released',
    MmiEvents.SMALL_WHEEL_ROTATED_RIGHT: 'Small wheel rotated right',
    MmiEvents.SMALL_WHEEL_ROTATED_LEFT: 'Small wheel rotated left',
    MmiEvents.BIG_WHEEL_ROTATED_RIGHT: 'Big wheel rotated right',
    MmiEvents.BIG_WHEEL_ROTATED_LEFT: 'Big wheel rotated left'
}

# 0x01: pressing the big wheel
# 0x02: media button
# 0x03: name button
# 0x04: tel button
# 0x05: nav button
# 0x06: info button
# 0x07: car button
# 0x08: setup button
# 0x0A: top left button
# 0x0B: bottom left button
# 0x0C: previous button
# 0x0D: top right button
# 0x0E: bottom right button
# 0x0F: return button
# 0x10: next button
# 0x18: radio button
# 0x38: pressing the small wheel


class MmiButtonIds:
    BIG_WHEEL_BTN = 0x01
    MEDIA = 0x02
    NAME = 0x03
    TEL = 0x04
    NAV = 0x05
    INFO = 0x06
    CAR = 0x07
    SETUP = 0x08
    TOP_LEFT = 0x0A
    BOTTOM_LEFT = 0x0B
    PREV = 0x0C
    TOP_RIGHT = 0x0D
    BOTTOM_RIGHT = 0x0E
    RETURN = 0x0F
    NEXT = 0x10
    RADIO = 0x18
    SMALL_WHEEL_BTN = 0x38


BTN_DESCRIPTIONS = {
    MmiButtonIds.BIG_WHEEL_BTN: 'big wheel',
    MmiButtonIds.MEDIA: 'media button',
    MmiButtonIds.NAME: 'name button',
    MmiButtonIds.TEL: 'tel button',
    MmiButtonIds.NAV: 'nav button',
    MmiButtonIds.INFO: 'info button',
    MmiButtonIds.CAR: 'car button',
    MmiButtonIds.SETUP: 'setup button',
    MmiButtonIds.TOP_LEFT: 'top left button',
    MmiButtonIds.BOTTOM_LEFT: 'bottom left button',
    MmiButtonIds.PREV: 'previous button',
    MmiButtonIds.TOP_RIGHT: 'top right button',
    MmiButtonIds.BOTTOM_RIGHT: 'bottom right button',
    MmiButtonIds.RETURN: 'return button',
    MmiButtonIds.NEXT: 'next button',
    MmiButtonIds.RADIO: 'radio button',
    MmiButtonIds.SMALL_WHEEL_BTN: 'small wheel'
}

class MmiLightIds(MmiButtonIds):
    pass

WHEEL_DESCRIPTIONS = BTN_DESCRIPTIONS

# 0x40: small wheel
# 0x50: big wheel


class MmiWheelIds:
    SMALL_WHEEL = 0x40
    BIG_WHEEL = 0x50


WHEEL_DESCRIPTIONS = {
    MmiWheelIds.SMALL_WHEEL: 'small wheel',
    MmiWheelIds.BIG_WHEEL: 'big wheel'
}


class MmiControl:
    # public:
    def __init__(self, port, bufferSize, buttonCount, wheelCount):
        self._serial = serial.Serial(
            port=port,
            baudrate=9600,
            stopbits=serial.STOPBITS_TWO,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS
        )
        self._buffer = [0x00 for _ in range(bufferSize)]
        self._bufferSize = bufferSize

        self._buttonCount = buttonCount
        self._buttons = [None for _ in range(buttonCount)]

        self._wheelCount = wheelCount
        self._wheels = [None for _ in range(wheelCount)]

    def createButton(self, buttonId):
        if (self._assignedButtonCount >= self._buttonCount):
            return None

        button = MmiButton(MmiButtonInput(buttonId))
        self._buttons[self._assignedButtonCount] = button
        self._assignedButtonCount += 1
        return button

    def createWheel(self, wheelId):
        if (self._assignedWheelCount >= self._wheelCount):
            return None

        wheel = MmiWheel(wheelId)
        self._wheels[self._assignedWheelCount] = wheel
        self._assignedWheelCount += 1
        return wheel

    def createLight(self, lightId):
        light = MmiLight(lightId, self)
        return light

    def setIllumination(self, brightness):
        message = [0x60, brightness]
        self.write(message)

    def setHighlightLevel(self, brightness):
        message = [0x64, brightness, 0x01]
        self.write(message)

    def setLight(self, id, state):
        if (id == 0x10):
            message = [0x68, (0x01 if state else 0x00), id, id]
            self.write(message)
        else:
            message = [0x68, (0x01 if state else 0x00), id]
            self.write(message)

    def enableKeys(self):
        message = [0x70, 0x12]
        self.write(message)

    def shutdown(self):
        message = [0x70, 0x11]
        self.write(message)

    def update(self, mmiCallback):
        while (self._serial.in_waiting > 0 and self._readIndex < self._bufferSize):
            data = self._serial.read()
            data = struct.unpack('B', data)[0]

            self._buffer[self._readIndex] = data
            self._readIndex += 1

            # Detect packet start
            if (self._startIndex == -1):
                if (data == 0x10):
                    self._startIndex = -2
                elif (data == 0x06):
                    self._readIndex = 0
                continue

            elif (self._startIndex == -2):
                if (data == 0x02):
                    self._startIndex = self._readIndex
                else:
                    self._startIndex = -1
                continue

            # Detect packet end
            if (self._endIndex == -1 and data == 0x10):
                self._endIndex = -2
                continue

            elif (self._endIndex == -2):
                if (data == 0x03):
                    self._endIndex = self._readIndex - 2
                elif (data != 0x10):
                    self._endIndex = -1
                continue

            # We have a packet ...
            if (self._endIndex > 0):
                remoteChecksum = data
                localChecksum = 0
                for i in range(self._startIndex - 2, self._endIndex + 2):
                    localChecksum += self._buffer[i]

                if (localChecksum == remoteChecksum):
                    self.ack()
                    payloadSize = self._endIndex - self._startIndex

                    payload = [0x00 for _ in range(payloadSize)]
                    for i in range(payloadSize):
                        payload[i] = self._buffer[self._startIndex+i]

                    self.serialEvent(payload, mmiCallback)

                self._startIndex = -1
                self._endIndex = -1
                self._readIndex = 0

            elif (self._readIndex >= self._bufferSize):
                self._startIndex = -1
                self._endIndex = -1
                self._readIndex = 0

        # Update button states
        for i in range(self._assignedButtonCount):
            self._buttons[i].update()

        # Update wheel states
        for i in range(self._assignedWheelCount):
            self._wheels[i].update()

# private:
    _buttonCount = 0
    _assignedButtonCount = 0
    _buttons = []

    _wheelCount = 0
    _assignedWheelCount = 0
    _wheels = []

    _serial = None
    _buffer = []
    _bufferSize = 0

    _startIndex = -1
    _endIndex = -1
    _readIndex = 0

    def write(self, data):
        length = len(data)
        message = [0x00 for _ in range(length + 5)]
        message[0] = 0x10
        message[1] = 0x02
        checksum = 0x25
        for i in range(length):
            checksum += data[i]
            message[2+i] = data[i]

        message[2+length] = 0x10
        message[3+length] = 0x03
        message[4+length] = checksum
        self._serial.write(message)
        self._serial.flush()

    def ack(self):
        self._serial.write(0x06)
        self._serial.flush()

    def serialEvent(self, data, mmiCallback):
        length = len(data)
        # power on or volume button pushed initially
        if (data[0] == 0x79 and length > 1):
            if (data[1] == 0x38 or data[1] == 0xff):
                mmiCallback(data[1])

        # unknown ...
        elif (data[0] == 0x35):
            # ... but it comes as return to the activation sequence 70 12
            # data package only has this byte ... however the user might want to use it as trigger:
            mmiCallback(data[0])

        # a button has been pressed
        elif ((data[0] == 0x30 or data[0] == 0x31) and length > 1):
            mmiCallback(data[0], data[1])
            for i in range(self._assignedButtonCount):
                self._buttons[i].updateTrigger(data[1], data[0] == 0x30)

        # the small wheel has been turned
        elif ((data[0] == 0x40 or data[0] == 0x41) and length > 1):
            ammount = data[1] * (1 if data[0] == 0x40 else -1)
            mmiCallback(data[0], data[1])
            for i in range(self._assignedWheelCount):
                self._wheels[i].turn(0x40, ammount)

        # the big wheel has been turned
        elif ((data[0] == 0x50 or data[0] == 0x51) and length > 1):
            ammount = data[1] * (1 if data[0] == 0x50 else -1)
            mmiCallback(data[0], data[1])
            for i in range(self._assignedWheelCount):
                self._wheels[i].turn(0x50, ammount)
