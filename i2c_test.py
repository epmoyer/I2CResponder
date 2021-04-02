# Standard Library
from machine import Pin, I2C
import time
import _thread

# Local
from i2c_responder import I2CResponder

I2C_FREQUENCY = 100000

CONTROLLER_I2C_DEVICE_ID = 1
GPIO_CONTROLLER_SDA = 2
GPIO_CONTROLLER_SCL = 3

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 0
GPIO_RESPONDER_SCL = 1

READBUFFER = [0, 0]

PADS_BANK0_BASE = 0x4001c000
PADS_BANK0__PUE = 0x08

def main():

    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )
    i2c_controller = I2C(
        CONTROLLER_I2C_DEVICE_ID,
        scl=Pin(GPIO_CONTROLLER_SCL),
        sda=Pin(GPIO_CONTROLLER_SDA),
        freq=I2C_FREQUENCY,
    )

    print('Scanning I2C Bus for responders...')
    responder_addresses = i2c_controller.scan()
    print('Responders found: ' + format_hex(responder_addresses))
    print()

    buffer_out = bytearray([0x01, 0x02])
    # while True:
    print('Controller: Issuing I2C WRITE with data: ' + format_hex(buffer_out))
    i2c_controller.writeto(RESPONDER_ADDRESS, buffer_out)
    time.sleep(0.25)

    print('   Responder: Getting I2C WRITE data...')
    buffer_in = i2c_responder.get_write_data(max_size=len(buffer_out))
    print('   Responder: Received I2C WRITE data: ' + format_hex(buffer_in))
    print()
    # time.sleep(1)

    thread_lock = _thread.allocate_lock()
    _thread.start_new_thread(thread_i2c_controller_read, (i2c_controller, thread_lock,))
    buffer_out = bytearray([0x09, 0x08])
    for value in buffer_out:
        while not i2c_responder.read_is_pending():
            pass
        i2c_responder.put_read_data(value)
        with thread_lock:
            print('   Responder: Transmitted I2C READ data: ' + format_hex(value))
    time.sleep(1)
    # print(READBUFFER)
    print('Conroller: Received I2C READ data: ' + format_hex(READBUFFER))

def thread_i2c_controller_read(i2c_controller, thread_lock):
    with thread_lock:
        print('Controller: Initiating I2C READ...')
    data = i2c_controller.readfrom(RESPONDER_ADDRESS, 2)
    for i, value in enumerate(data):
        READBUFFER[i] = value


def format_hex(_object):
    try:
        values_hex = [to_hex(value) for value in _object]
        return '[{}]'.format(', '.join(values_hex))
    except TypeError:
        return to_hex(_object)


def to_hex(value):
    return '0x{:02X}'.format(value)


if __name__ == "__main__":
    main()
