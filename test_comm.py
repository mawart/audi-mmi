import RPi.GPIO as GPIO
import serial
import struct
import time
from input import KBHit

breakpoint()  # force remote debugger to properly attach


MMI_PASS_THROUG_PIN = 7  # GPIO 7, PIN 26, HIGH = MMI signal pass through disabled - Raspberry Pi will act as intermediary, LOW = MMI signal pass through enabled

UART0 = '/dev/ttyAMA0'  # RXD1 = GPIO 15, PIN 10, TXD1 = GPIO 14, PIN 8
UART3 = '/dev/ttyAMA1'  # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA2'  # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA3'  # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

mmiHeadUnit = serial.Serial(
    port=UART4,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS
)

mmiCtrlUnit = serial.Serial(
    port=UART5,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS
)

# setup Raspberry Pi GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use "GPIO" pin numbering
GPIO.setup(MMI_PASS_THROUG_PIN, GPIO.OUT)

def setMMIPassThroughMode(enabled):
    # Enable (LOW) or disable (HIGH) pass through mode
    # This either directly connects MMI head unit with MMI button control unit or allows us to take control of the communication between them
    GPIO.output(MMI_PASS_THROUG_PIN, GPIO.LOW if enabled else GPIO.HIGH)

def write_raw(mySerial, data):
    mySerial.write(data)
    mySerial.flush()

def read_raw(mySerial):
    serial_data = []
    # read all data from serial input buffer
    while (mySerial.in_waiting > 0):
        data = mySerial.read()  # read one byte
        data = struct.unpack('B', data)[0]  # convert to number
        serial_data.append(data)
    return serial_data

def asHex(data):
    return [hex(d) for d in data]


kb = KBHit()

timestamp = time.time()
pass_through = True
exit = False
while not exit:
    setMMIPassThroughMode(pass_through)
    
    if not pass_through:
        data = read_raw(mmiHeadUnit)
        write_raw(mmiCtrlUnit, data)
        print('MMI head unit: ' + asHex(data))

        data = read_raw(mmiCtrlUnit)
        write_raw(mmiHeadUnit, data)
        print('MMI control unit: ' + asHex(data))
    
    if (time.time() - timestamp > 5):
        pass_through = not pass_through

# cleanup
GPIO.cleanup()
