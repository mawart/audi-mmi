import RPi.GPIO as GPIO
import serial
import struct
import time

breakpoint()  # force remote debugger to properly attach


MMI_PASS_THROUG_PIN = 7  # GPIO 7, PIN 26, HIGH = MMI signal pass through disabled - Raspberry Pi will act as intermediary, LOW = MMI signal pass through enabled

UART0 = '/dev/ttyAMA0'  # RXD1 = GPIO 15, PIN 10, TXD1 = GPIO 14, PIN 8
UART3 = '/dev/ttyAMA1'  # RXD3 = GPIO 5, PIN 29, TXD3 = GPIO 4, PIN 7
UART4 = '/dev/ttyAMA2'  # RXD4 = GPIO 9, PIN 21, TXD4 = GPIO 8, PIN 24
UART5 = '/dev/ttyAMA3'  # RXD5 = GPIO 13, PIN 33, TXD5 = GPIO 12, PIN 32

mmiHeadUnit = serial.Serial(
    port=UART5,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS,
    timeout = 0
)

mmiCtrlUnit = serial.Serial(
    port=UART4,
    baudrate=9600,
    stopbits=serial.STOPBITS_TWO,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS,
    timeout = 0
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

def read_and_write(read_serial, write_serial):
    # read all data from serial input buffer
    if (read_serial.in_waiting > 0):
        data = read_serial.read(read_serial.in_waiting) 
        write_raw(write_serial, data)


def asHex(data):
    return [hex(d) for d in data]

def sendHeadUnitAck():{
    write_raw(mmiHeadUnit, [0x7e, 0x0])
}

timestamp = time.time()
pass_through = True
exit = False
mmiDataList = []
while not exit:
    setMMIPassThroughMode(pass_through) 
    
    headUnitData = read_raw(mmiHeadUnit)
    mmiHeadUnit.read()
    if len(headUnitData) > 0:
        mmiDataList.append(('mmi head unit', headUnitData))
        # write_raw(mmiCtrlUnit, headUnitData)
        #print('mmi head unit: ' + ' '.join(asHex(headUnitData)))

    ctrlUnitData = read_raw(mmiCtrlUnit)
    if len(ctrlUnitData) > 0:
        mmiDataList.append(('mmi control unit', ctrlUnitData))
        # write_raw(mmiHeadUnit, ctrlUnitData)
        #print('mmi control: ' + ' '.join(asHex(ctrlUnitData)))

    #exit = True
    # headUnitData = read_raw(mmiHeadUnit)
    # if len(ctrlUnitData) > 0:
    #     # isBtn =  len(ctrlUnitData) > 2 and ctrlUnitData[0] == 0x10 and ctrlUnitData[1] ==0x02 and (ctrlUnitData[2] == 0x30 or ctrlUnitData[2] == 0x31)
    #     # if not isBtn:
    #     write_raw(mmiHeadUnit, ctrlUnitData)
    # if len(headUnitData) > 0:
    #     print(asHex(headUnitData))
    #     # isBtn =  len(ctrlUnitData) > 2 and ctrlUnitData[0] == 0x10 and ctrlUnitData[1] ==0x02 and (ctrlUnitData[2] == 0x30 or ctrlUnitData[2] == 0x31)
    #     # if not isBtn:
    #     write_raw(mmiCtrlUnit, headUnitData)
    
    if (time.time() - timestamp > 30):
    #    pass_through = not pass_through
    #     print('Pass trough ' + ('enabled' if pass_through else 'disabled'))
        timestamp = time.time()
        exit = True

for d in mmiDataList:
    print(d[0] + ': ' + ' '.join(asHex(d[1])))


# cleanup
GPIO.cleanup()
