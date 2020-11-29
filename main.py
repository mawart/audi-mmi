from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
import time
from util import shut_down
import RPi.GPIO as GPIO
import serial
import struct

# breakpoint()  # force remote debugger to properly attach

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

def update():
    serial_data = []
    while (mmiUnit_serial.in_waiting > 0):
        data = mmiUnit_serial.read()
        data = struct.unpack('B', data)[0]
        serial_data.append(data)
    
    length = len(serial_data)
    if(length > 0):    
        if(serial_data[0] == 0x67 and length > 1 and serial_data[1] == 0x5e):
            remainder = [serial_data[i] for i in range(4, length)]
            print('mmi unit mode switch', mmiUnitEvent[serial_data[2]], mmiUnitLights[serial_data[3]] if serial_data[3] in mmiUnitLights else hex(serial_data[3]), asHex(remainder))
        else:
            print_debug('mmi unit data received', asHex(serial_data))

        mmiControl.write_raw(serial_data)

def asHex(data):
    return [hex(d) for d in data]


def print_debug(*argv):
    # print(argv)
    pass

def mmiSerialDataReceived(serial_data, state):
    serial_data_hex = asHex(serial_data)
    print_debug('data received', serial_data_hex)
    # forward the received control data to the mmi unit
    # mmiControl2.write_raw(serial_data)
    if (len(serial_data) >= 4):
        event = serial_data[2]
        payload = serial_data[3]
        if ((event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED) and payload == MmiButtonIds.NAV):
            print('Nav button event -> forwarded as Media button to mmi unit')
            mmiControl2.write([event, MmiButtonIds.MEDIA])
            if event == MmiEvents.BTN_PRESSED:
                state.open_auto_mode = not state.open_auto_mode
            
            if state.open_auto_mode:
                print('Open Auto mode activated')
            else:
                print('Open Auto mode de-activated')            
            return

        if(state.open_auto_mode and 
             ((event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED) or 
              (event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT) or
              (event == MmiEvents.SMALL_WHEEL_ROTATED_LEFT or event == MmiEvents.SMALL_WHEEL_ROTATED_RIGHT))
            ):
            print('Open Auto mode active, not forwarding events to mmi unit')
            return

    print_debug('data forwarded to mmi unit')
    # forward the received control data to the mmi unit
    mmiControl2.write_raw(serial_data)


def mmiEvent(event, payload, serial_data):
    serial_data_hex = asHex(serial_data)
    # if ((event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED) and payload == MmiButtonIds.NAV):
    #     print('Nav button event -> remapping to Media button')
    #     mmiControl2.write([event, MmiButtonIds.MEDIA])
    # else:
    #     print('data forwarded to mmi unit')
    #     # forward the received control data to the mmi unit
    #     mmiControl2.write_raw(serial_data)

    if (event == MmiEvents.ACC_12V_ON or event == MmiEvents.POWER_BTN_PRESSED):
        mmiControl.enableKeys()

    elif (event == MmiEvents.MMI_ACTIVATED):
        # sets the intensity of the global backlight from 0 (off) to 255 (full brightness).
        mmiControl.setIllumination(0xFF)
        # sets the intensity of the button highlights from 0 (off) to 255 (full brightness).
        mmiControl.setHighlightLevel(0x99)

    if (event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED):
        print_debug(BTN_DESCRIPTIONS[payload],
                    EVENT_DESCRIPTIONS[event], serial_data_hex)

    elif (event == MmiEvents.SMALL_WHEEL_ROTATED_LEFT or event == MmiEvents.SMALL_WHEEL_ROTATED_RIGHT or
          event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT):
        print_debug(EVENT_DESCRIPTIONS[event],
                    'by %d' % (payload), serial_data_hex)

    elif (event in EVENT_DESCRIPTIONS):
        print_debug(EVENT_DESCRIPTIONS[event], serial_data_hex)

    else:
        print('unknown event', serial_data_hex)

# mmiNavButton = mmiControl.createButton(MmiButtonIds.NAV)
# mmiSmallWheel = mmiControl.createWheel(MmiWheelIds.SMALL_WHEEL)
# mmiMediaLight = mmiControl.createLight(MmiLightIds.MEDIA)

class AppState:
    open_auto_mode = False

acc_12v_on_timestamp = time.time()
state = AppState()

# signal Pi has booted and is up and running
GPIO.output(PI_ON_OUTPUT_PIN, GPIO.HIGH)
shutdown = False
while not shutdown:
    #mmiControl.update(mmiEvent, lambda serial_data: mmiSerialDataReceived(serial_data, state))
    #update()

    if (not GPIO.input(ACC_12V_INPUT_PIN)):
        # reset timestamp in acc is on (active low)
        acc_12v_on_timestamp = time.time()

    if (time.time() - acc_12v_on_timestamp > 5):
        # if acc has been off for 5 seconds initiate shutdown
        # this timeout prevents unintended shutdowns when power is turned off and on in short succession
        shutdown = True

    # if (mmiSmallWheel.wasTurned()):
    #     if (mmiSmallWheel.getAmount() < 0):
    #         # turned left
    #         pass
    #     else:
    #         # turned right
    #         pass

    # time.sleep(0.1)  # run every 100ms to reduce CPU load

# initiate shutdown
shut_down()
GPIO.cleanup()