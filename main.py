from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
import time
from util import shut_down
import RPi.GPIO as GPIO

breakpoint() # force remote debugger to properly attach

ACC_12V_INPUT_PIN = 10 # GPIO 10, PIN 19, HIGH = 12V ON, LOW = 12V OFF
PI_ON_OUTPUT_PIN = 11 # GPIO 11, PIN 23, HIGH = Raspberry Pi ON, LOW = Raspberry Pi OFF

UART3 = '/dev/ttyAMA1' # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA2' # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA3' # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # Use "GPIO" pin numbering
GPIO.setup(ACC_12V_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PI_ON_OUTPUT_PIN, GPIO.OUT)

mmiControl2 = MmiControl(port=UART4, bufferSize=16,
                        buttonCount=17, wheelCount=2)

mmiControl = MmiControl(port=UART5, bufferSize=16,
                        buttonCount=17, wheelCount=2)

def printAsHex(message, data):
    print(message, [hex(d) for d in data])

def mmiDataReceived(data):
    if (len(data) > 0):
        printAsHex('data received', data)
        mmiControl2.write_raw(data)

def mmiEvent(event, data):
    if (event == MmiEvents.ACC_12V_ON or event == MmiEvents.POWER_BTN_PRESSED):
        mmiControl.enableKeys()

    elif (event == MmiEvents.MMI_ACTIVATED):
        # sets the intensity of the global backlight from 0 (off) to 255 (full brightness).
        mmiControl.setIllumination(0xFF)
        # sets the intensity of the button highlights from 0 (off) to 255 (full brightness).
        mmiControl.setHighlightLevel(0x99)

    elif (event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED):
        print(BTN_DESCRIPTIONS[data], EVENT_DESCRIPTIONS[event])
    
    elif (event == MmiEvents.SMALL_WHEEL_ROTATED_LEFT or event == MmiEvents.SMALL_WHEEL_ROTATED_RIGHT or
          event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT):
        print(EVENT_DESCRIPTIONS[event], 'by %d' % (data))
    
    elif (event in EVENT_DESCRIPTIONS):
        print(EVENT_DESCRIPTIONS[event])
    
    else:
        printAsHex('unknown event', data)

mmiNavButton = mmiControl.createButton(MmiButtonIds.NAV)
mmiSmallWheel = mmiControl.createWheel(MmiWheelIds.SMALL_WHEEL)
mmiMediaLight = mmiControl.createLight(MmiLightIds.MEDIA)

acc_12v_on_timestamp = time.time()
GPIO.output(PI_ON_OUTPUT_PIN, GPIO.HIGH) # signal Pi has booted and is up and running
shutdown = False
while not shutdown:
    mmiControl.update(mmiEvent, mmiDataReceived)

    if (GPIO.input(ACC_12V_INPUT_PIN)):
        # reset timestamp in acc is on
        acc_12v_on_timestamp = time.time()

    if (time.time() - acc_12v_on_timestamp > 5):
        # if acc has been off for 5 seconds initiate shutdown
        # this timeout prevents unintended shutdowns when power is turned off and on in short succession
        shutdown = True

    if (mmiSmallWheel.wasTurned()):
        if (mmiSmallWheel.getAmount() < 0):
            # turned left
            pass
        else:
            # turned right
            pass
    
    time.sleep(0.1) # run every 100ms to prevent taking too much CPU

shut_down()