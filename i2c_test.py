import utime
from machine import mem32, Pin, I2C
from i2c_responder import I2CResponder
import time

I2C_FREQUENCY = 100000
# I2C_FREQUENCY = 10000

CONTROLLER_I2C_DEVICE_ID = 1
GPIO_CONTROLLER_SDA = 2
GPIO_CONTROLLER_SCL = 3

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 0
GPIO_RESPONDER_SCL = 1


def main():

    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=0, scl_gpio=1, responder_address=RESPONDER_ADDRESS
    )
    i2c_controller = I2C(
        CONTROLLER_I2C_DEVICE_ID,
        # scl=Pin(GPIO_CONTROLLER_SCL, pull=Pin.PULL_UP),
        scl=Pin(GPIO_CONTROLLER_SCL),
        # sda=Pin(GPIO_CONTROLLER_SDA, pull=Pin.PULL_UP),
        sda=Pin(GPIO_CONTROLLER_SDA),
        freq=I2C_FREQUENCY,
    )
    print('I2C0 IC_CON: ' + format_hex(mem32[i2c_responder.I2C0_BASE | i2c_responder.IC_CON]))
    print('I2C1 IC_CON: ' + format_hex(mem32[i2c_responder.I2C1_BASE | i2c_responder.IC_CON]))

    print('Scanning bus for responders...')
    responder_addresses = i2c_controller.scan()
    print('Responders found: ' + format_hex(responder_addresses))

    buffer_out = bytearray([0x01, 0x02])
    # while True:
    print('Controller Write: ' + format_hex(buffer_out))
    i2c_controller.writeto(RESPONDER_ADDRESS, buffer_out)
    time.sleep(0.25)

    print('Responder Read...')
    buffer_in = i2c_responder.get_rx_data(max_size=len(buffer_out))
    print('Responder Received: ' + format_hex(buffer_in))
    print()
    # time.sleep(1)


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
