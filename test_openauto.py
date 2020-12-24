from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import MMI_EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
import time
from util import shut_down
import RPi.GPIO as GPIO
import serial
import struct

breakpoint()  # force remote debugger to properly attach

ACC_12V_INPUT_PIN = 10  # GPIO 10, PIN 19, HIGH = 12V ON, LOW = 12V OFF
PI_ON_OUTPUT_PIN = 11  # GPIO 11, PIN 23, HIGH = Raspberry Pi ON, LOW = Raspberry Pi OFF

UART0 = '/dev/ttyAMA0'  # RXD1 = GPIO 15, PIN 10, TXD1 = GPIO 14, PIN 8
UART3 = '/dev/ttyAMA1'  # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA2'  # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA3'  # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use "GPIO" pin numbering
GPIO.setup(ACC_12V_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PI_ON_OUTPUT_PIN, GPIO.OUT)

mmiControl2 = MmiControl(port=UART4, bufferSize=16,
                         buttonCount=17, wheelCount=2)

mmiControl = MmiControl(port=UART5, bufferSize=16,
                        buttonCount=17, wheelCount=2)

mmiUnit_serial = serial.Serial(
    port=UART3,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS
)

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

def sendMmiButton(id, pressed):
    mmiControl2.write([MmiEvents.BTN_PRESSED if pressed else MmiEvents.BTN_RELEASED, id])    

def sendMmiWheel(id, cw, amount):
    if id == MmiWheelIds.BIG_WHEEL:
        mmiControl2.write([MmiEvents.BIG_WHEEL_ROTATED_RIGHT if cw else MmiEvents.BIG_WHEEL_ROTATED_LEFT, amount])    
    elif id == MmiWheelIds.SMALL_WHEEL:
        mmiControl2.write([MmiEvents.SMALL_WHEEL_ROTATED_RIGHT if cw else MmiEvents.SMALL_WHEEL_ROTATED_LEFT, amount])    
    else:
        pass

def asHex(data):
    return [hex(d) for d in data]

def print_debug(*argv):
    # print(argv)
    pass

sendMmiButton(MmiButtonIds.NAV, True)
nr_turns = 0

acc_12v_on_timestamp = time.time()
# signal Pi has booted and is up and running
GPIO.output(PI_ON_OUTPUT_PIN, GPIO.HIGH)
shutdown = False
while not shutdown:
    if (not GPIO.input(ACC_12V_INPUT_PIN)):
        # reset timestamp in acc is on (active low)
        acc_12v_on_timestamp = time.time()

    if (time.time() - acc_12v_on_timestamp > 5):
        # if acc has been off for 5 seconds initiate shutdown
        # this timeout prevents unintended shutdowns when power is turned off and on in short succession
        shutdown = True

    sendMmiWheel(MmiWheelIds.BIG_WHEEL, nr_turns < 7, 1)
    nr_turns += 1
    if nr_turns >= 14:
        sendMmiButton(MmiButtonIds.RADIO, True)
    if nr_turns >= 20:
        nr_turns = 0
        sendMmiButton(MmiButtonIds.NAV, True)

    time.sleep(0.5)

# initiate shutdown
shut_down()
