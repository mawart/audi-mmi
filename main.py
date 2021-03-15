from mmi.mmiHeadUnit import MmiHeadUnit
from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import MMI_EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
from mmi.mmiControl import writeToSerial
import time
from util import shut_down
import RPi.GPIO as GPIO
import serial
import struct

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

# MMI head unit uses UART 4
mmiHeadUnit = MmiHeadUnit(port=UART4, bufferSize=16)
# MMI button control unit uses UART 5
mmiBtnCtrl = MmiControl(port=UART5, bufferSize=16,
                        buttonCount=17, wheelCount=2)
# OpenAuto application uses UART0 to listen for MMI button events. We use UART 3 to send it the remapped events (MEDIA -> NAV)
# To this end TX of UART3 (GPIO 4, PIN 7) is physically connected to RX of UART0 (GPIO 15, PIN 10)
openAutoSerial = serial.Serial(
    port=UART3,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS
)
# create a button object to conveniently monitor the MMI Media button
mmiMediaButton = mmiBtnCtrl.createButton(MmiButtonIds.MEDIA)

# helper functions

def asHex(data):
    return [hex(d) for d in data]

def print_debug(*argv):
    # print(argv)
    pass

def setMMIPassThroughMode(enabled):
    # Enable (LOW) or disable (HIGH) pass through mode
    # This either directly connects MMI head unit with MMI button control unit or allows us to take control of the communication between them
    GPIO.output(MMI_PASS_THROUG_PIN, GPIO.LOW if enabled else GPIO.HIGH)

def setMediaMode(appState, enabled):
    appState.media_mode = enabled
   
    if (appState.debug):
        print(('Entering' if appState.media_mode else 'Leaving') + ' Media mode')

def setOpenAutoMode(appState, enabled):
    appState.open_auto_mode = enabled
    if (appState.open_auto_mode):  # we have entered OpenAuto mode
        # disable MMI pass through, we will handle communication between MMI control unit and MMI head unit from here on
        setMMIPassThroughMode(False)
        # send NAV button press to OpenAuto application so it will start to listen to the MMI buttons
        writeToSerial(openAutoSerial, [
            MmiEvents.BTN_PRESSED, MmiButtonIds.NAV])
    else:
        # we have left OpenAuto mode so re-enable MMI pass through
        setMMIPassThroughMode(True)
    
    if (appState.debug):
        print(('Entering' if appState.open_auto_mode else 'Leaving') + ' OpenAuto mode')



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

def isOpenAutoEvent(event, payload):
    openAutoBtnEvent = (
        event == MmiEvents.BTN_PRESSED or 
        event == MmiEvents.BTN_RELEASED
    ) and (
        payload == MmiButtonIds.TOP_LEFT or 
        payload == MmiButtonIds.TOP_RIGHT or 
        payload == MmiButtonIds.BOTTOM_LEFT or 
        payload == MmiButtonIds.BOTTOM_RIGHT or
        payload == MmiButtonIds.RETURN or 
        payload == MmiButtonIds.BIG_WHEEL_BTN
    )

    openAutoWheelEvent = (
        event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or 
        event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT
    )

    return openAutoBtnEvent or openAutoWheelEvent    

def isMainButtonEvent(event, payload):
    btnEvent = (
        event == MmiEvents.BTN_PRESSED or 
        event == MmiEvents.BTN_RELEASED
    ) and (
        payload == MmiButtonIds.RADIO or 
        payload == MmiButtonIds.MEDIA or 
        payload == MmiButtonIds.TEL or 
        payload == MmiButtonIds.NAME or
        payload == MmiButtonIds.NAV or 
        payload == MmiButtonIds.INFO or
        payload == MmiButtonIds.CAR or
        payload == MmiButtonIds.SETUP
    )

    return btnEvent    


def mmiBtnCtrlEvent(appState, event, payload, serial_data):   
    # Determine in which mode we should be
    if(event == MmiEvents.BTN_PRESSED):
        if(payload == MmiButtonIds.MEDIA):
            if (not appState.media_mode): 
                setMediaMode(appState, True)
            if (appState.open_auto_mode): 
                setOpenAutoMode(appState, False)
        elif(payload == MmiButtonIds.NEXT):
            if (appState.media_mode and not appState.open_auto_mode): 
                setOpenAutoMode(appState, True)
        elif(isMainButtonEvent(event, payload)):
            if (appState.media_mode): 
                setMediaMode(appState, False)
            if (appState.open_auto_mode): 
                setOpenAutoMode(appState, False)

    # we are in OpenAuto mode
    if (appState.open_auto_mode):
        if (isOpenAutoEvent(event, payload)):
            # forward all button and wheel events to OpenAuto application
            writeToSerial(openAutoSerial, [event, payload])
            # forward dummy btn event (NEXT btn press) to mmi head unit to get a response for the 
            # current event so the mmi button control unit receives its acknowledgement

            # mmiHeadUnit.write([MmiEvents.BTN_PRESSED if not appState.btn_pressed else MmiEvents.BTN_RELEASED, MmiButtonIds.NEXT])
            # appState.btn_pressed = not appState.btn_pressed
            mmiHeadUnit.write_raw([0x10, 0x2, 0x30, 0x10, 0x10, 0x10, 0x3, 0x75])
            # mmiHeadUnit.write([MmiEvents.BTN_RELEASED, MmiButtonIds.NEXT])
        else:
            # forward all data from mmi control unit to mmi head unit commands, but supress all OpenAuto related button and wheel events
            # to allow the controls to be used in OpenAuto and not have the MMI head unit interfere
            mmiHeadUnit.write_raw(serial_data)

    # log all events when in debug mode
    if (state.debug):
        logMmiBtnCtrlEvent(event, payload, serial_data)


def mmiHeadUnitEvent(appState, event, payload, serial_data):
    pass
# TODO: split pass through between RX and TX part of MMI control unit
#      we can let the MMI head unit send its data directly to the MMI control unit
#      we only need to control what the MMI control unit sends to the MMI head unit


class AppState:
    media_mode = False
    open_auto_mode = False
    mmi_standalone = False
    btn_pressed = False
    debug = True

# initalize application state
acc_12v_on_timestamp = time.time()
state = AppState()

# signal Pi has booted and is up and running
GPIO.output(PI_ON_OUTPUT_PIN, GPIO.HIGH)
# Enable pass through mode (directly connects MMI head unit with MMI button control unit)
setMMIPassThroughMode(True)
shutdown = False

# start main application loop
while not shutdown:
    # check data received from MMI control unit
    mmiBtnCtrl.update(lambda event, payload, serial_data: mmiBtnCtrlEvent(
        state, event, payload, serial_data))
    # check data received from MMI head unit
    mmiHeadUnit.update(lambda event, payload, serial_data: mmiHeadUnitEvent(
        state, event, payload, serial_data))

    if (not GPIO.input(ACC_12V_INPUT_PIN)):
        # reset timestamp if acc is on (active low)
        acc_12v_on_timestamp = time.time()

    if (time.time() - acc_12v_on_timestamp > 30):
        # if acc has been off for 30 seconds initiate shutdown
        # this timeout prevents unintended shutdowns when power is turned off and on in short succession
        shutdown = True

# initiate shutdown
shut_down()
GPIO.cleanup()
