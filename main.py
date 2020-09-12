from mmi.mmiControl import MmiControl, MmiEvents, MmiButtonIds, MmiWheelIds, MmiLightIds
from mmi.mmiControl import EVENT_DESCRIPTIONS, BTN_DESCRIPTIONS, WHEEL_DESCRIPTIONS
import time
from util import shut_down
import RPi.GPIO as GPIO

ACC_12V_INPUT = 10 # GPIO 10, PIN 19, HIGH = 12V ON, LOW = 12V OFF
PI_ON_OUTPUT = 11 # GPIO 11, PIN 23, HIGH = Raspberry Pi ON, LOW = Raspberry Pi OFF

UART3 = '/dev/ttyAMA2' # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA3' # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA4' # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

GPIO.setup(ACC_12V_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PI_ON_OUTPUT, GPIO.OUT)

mmiControl = MmiControl(port=UART5, bufferSize=16,
                        buttonCount=17, wheelCount=2)

# 0x35: Triggered after the MMI was fully activated
# 0x38: Power button is pressed
# 0xff: Power is turned on (12v)


def mmiEvent(event, data):
    if (event == MmiEvents.ACC_12V_ON or event == MmiEvents.POWER_BTN_PRESSED):
        mmiControl.enableKeys()

    if (event == MmiEvents.MMI_ACTIVATED):
        # sets the intensity of the global backlight from 0 (off) to 255 (full brightness).
        mmiControl.setIllumination(0xFF)
        # sets the intensity of the button highlights from 0 (off) to 255 (full brightness).
        mmiControl.setHighlightLevel(0x99)

    if (event == MmiEvents.BTN_PRESSED or event == MmiEvents.BTN_RELEASED):
        print(BTN_DESCRIPTIONS[data], EVENT_DESCRIPTIONS[event])
    elif (event == MmiEvents.SMALL_WHEEL_ROTATED_LEFT or event == MmiEvents.SMALL_WHEEL_ROTATED_RIGHT or
          event == MmiEvents.BIG_WHEEL_ROTATED_LEFT or event == MmiEvents.BIG_WHEEL_ROTATED_RIGHT):
        print(EVENT_DESCRIPTIONS[event], 'by %d' % (data))
    else:
        print(EVENT_DESCRIPTIONS[event])

mmiNavButton = mmiControl.createButton(MmiButtonIds.NAV)
mmiSmallWheel = mmiControl.createWheel(MmiWheelIds.SMALL_WHEEL)
mmiMediaLight = mmiControl.createLight(MmiLightIds.MEDIA)

acc_12v_on_timestamp = time.time()
GPIO.output(PI_ON_OUTPUT, GPIO.HIGH) # signal Pi has booted and is up and running
while True:
    mmiControl.update(mmiEvent)

    if (GPIO.input(ACC_12V_INPUT)):
        # reset timestamp in acc is on
        acc_12v_on_timestamp = time.time()

    if (time.time() - acc_12v_on_timestamp > 5):
        # if acc has been off for 5 seconds initiate shutdown
        # this timeout prevents unintended shutdowns when power is turned off and on in short succession
        shut_down()

    if (mmiSmallWheel.wasTurned()):
        if (mmiSmallWheel.getAmount() < 0):
            # turned left
            pass
        else:
            # turned right
            pass

GPIO.cleanup()