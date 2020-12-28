from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import MMI_EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
from mmi.mmiControl import writeToSerial
import time
from util import shut_down
import RPi.GPIO as GPIO
import serial
import struct

from input import KBHit

# breakpoint()  # force remote debugger to properly attach

ACC_12V_INPUT_PIN = 10  # GPIO 10, PIN 19, HIGH = 12V ON, LOW = 12V OFF
PI_ON_OUTPUT_PIN = 11  # GPIO 11, PIN 23, HIGH = Raspberry Pi ON, LOW = Raspberry Pi OFF
MMI_PASS_THROUG_PIN = 7  # GPIO 7, PIN 26, HIGH = MMI signal pass through disabled - Raspberry Pi will act as intermediary, LOW = MMI signal pass through enabled

# Rapsberry Pi UART device list
UART0 = '/dev/ttyAMA0'  # RXD0/RXD1 = GPIO 15, PIN 10, TXD0/TXD1 = GPIO 14, PIN 8
UART3 = '/dev/ttyAMA1'  # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA2'  # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA3'  # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

# setup Raspberry Pi GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use "GPIO" pin numbering
GPIO.setup(ACC_12V_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PI_ON_OUTPUT_PIN, GPIO.OUT)
GPIO.setup(MMI_PASS_THROUG_PIN, GPIO.OUT)

# MMI button control unit uses UART 5
mmiBtnCtrl = MmiControl(port=UART5, bufferSize=16,
                        buttonCount=17, wheelCount=2)
# create a button object to conveniently monitor the MMI Media button
mmiMediaButton = mmiBtnCtrl.createButton(MmiButtonIds.MEDIA)

# helper functions
def asHex(data):
    return [hex(d) for d in data]

def setMMIPassThroughMode(enabled):
    # Enable (LOW) or disable (HIGH) pass through mode
    # This either directly connects MMI head unit with MMI button control unit or allows us to take control of the communication between them
    GPIO.output(MMI_PASS_THROUG_PIN, GPIO.LOW if enabled else GPIO.HIGH)

def logMmiBtnCtrlEvent(event, payload, serial_data):
    serial_data_hex = asHex(serial_data)

    if (event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED):
        print(BTN_DESCRIPTIONS[payload],
                MMI_EVENT_DESCRIPTIONS[event], serial_data_hex)

    elif (event == MmiEvents.SMALL_WHEEL_ROTATED_LEFT or event == MmiEvents.SMALL_WHEEL_ROTATED_RIGHT or
            event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT):
        print(MMI_EVENT_DESCRIPTIONS[event],
                'by %d' % (payload), serial_data_hex)

    elif (event in MMI_EVENT_DESCRIPTIONS):
        print(MMI_EVENT_DESCRIPTIONS[event], serial_data_hex)

    else:
        print('unknown event', serial_data_hex)    

def mmiBtnCtrlEvent(appState, event, payload, serial_data):
    # if the Media button was held for 2 seconds toggle the OpenAuto mode
    if (mmiMediaButton.wasHeldFor(2000)):
        appState.open_auto_mode = not appState.open_auto_mode
        print('OpenAuto mode ' + ('enabled' if appState.open_auto_mode else 'disabled'))
        return

    # if we are contolling the mmi control unit we need to actively enable the keys after power up.
    if (state.mmi_standalone):
        if (event == MmiEvents.ACC_12V_ON or event == MmiEvents.POWER_BTN_PRESSED):
            mmiBtnCtrl.enableKeys()

        elif (event == MmiEvents.MMI_ACTIVATED):
            # sets the intensity of the global backlight from 0 (off) to 255 (full brightness).
            mmiBtnCtrl.setIllumination(0xFF)
            # sets the intensity of the button highlights from 0 (off) to 255 (full brightness).
            mmiBtnCtrl.setHighlightLevel(0x99)

    # log all events when in debug mode
    if (state.debug):
        logMmiBtnCtrlEvent(event, payload, serial_data)

def sendCommand():
    dict = {
        'BIG_WHEEL': MmiButtonIds.BIG_WHEEL_BTN,
        'MEDIA': MmiButtonIds.MEDIA,
        'NAME': MmiButtonIds.NAME,
        'TEL': MmiButtonIds.TEL,
        'NAV': MmiButtonIds.NAV,
        'INFO': MmiButtonIds.INFO,
        'CAR': MmiButtonIds.CAR,
        'SETUP': MmiButtonIds.SETUP,
        'TOP_LEFT': MmiButtonIds.TOP_LEFT,
        'BOTTOM_LEFT': MmiButtonIds.BOTTOM_LEFT,
        'PREV': MmiButtonIds.PREV,
        'TOP_RIGHT': MmiButtonIds.TOP_RIGHT,
        'BOTTOM_RIGHT': MmiButtonIds.BOTTOM_RIGHT,
        'RETURN': MmiButtonIds.RETURN,
        'NEXT': MmiButtonIds.NEXT,
        'RADIO': MmiButtonIds.RADIO,
        'SMALL_WHEEL': MmiButtonIds.SMALL_WHEEL_BTN 
    }
    light = input("Select light id (MEDIA, NAV, etc.) your option : ")
    lightId = dict.get(light, -1)
    if(lightId == -1):
        print('Invalid light id.')
        return

    action = int(input("(0=OFF, 1=ON) your option : "))
    if(action != 0 and action != 1):
        print('Invalid action.')
        return

    print(light + ' turned ' + ('on' if action == 1 else 'off'))
    mmiBtnCtrl.setLight(lightId, True if action == 1 else False)

class AppState:
    open_auto_mode = False
    mmi_standalone = True
    debug = True

# initalize application state
state = AppState()

# Disable pass through mode (isolates MMI button control unit from MMI head unit)
setMMIPassThroughMode(False)
exit = False

kb = KBHit()
# start main application loop
while not exit:

    if kb.kbhit():
        c = kb.getch()
        if ord(c) == 27: # ESC
            exit = True
        elif ord(c) == 32: # SPACE
            sendCommand()
        print(c)

    # check data received from MMI control unit
    mmiBtnCtrl.update(lambda event, payload, serial_data: mmiBtnCtrlEvent(
        state, event, payload, serial_data))

# cleanup
kb.set_normal_term()
GPIO.cleanup()