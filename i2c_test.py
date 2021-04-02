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
        RESPONDER_I2C_DEVICE_ID, sda=0, scl=1, responder_address=RESPONDER_ADDRESS
    )
    i2c_controller = I2C(
        CONTROLLER_I2C_DEVICE_ID,
        # scl=Pin(GPIO_CONTROLLER_SCL, pull=Pin.PULL_UP),
        scl=Pin(GPIO_CONTROLLER_SCL),
        # sda=Pin(GPIO_CONTROLLER_SDA, pull=Pin.PULL_UP),
        sda=Pin(GPIO_CONTROLLER_SDA),
        freq=I2C_FREQUENCY,
    )

    print('Scanning bus for responders...')
    responder_addresses = i2c_controller.scan()
    # responder_addresses_hex = [
    #     '0x{:02X}'.format(responder_address) for responder_address in responder_addresses
    # ]
    # print('Responders found: [{}]'.format(', '.join(responder_addresses_hex)))
    print('Responders found: ' + format_hex(responder_addresses))

    outbuffer = bytearray([0x01])
    # outbuffer = b'9'
    while True:
        print('Writing: ' + format_hex(outbuffer))
        i2c_controller.writeto(RESPONDER_ADDRESS, outbuffer)
        print("Write complete.")
        time.sleep(0.25)

        print('Reading...')
        if i2c_responder.any():
            print('Received: ' + format_hex(i2c_responder.get()))

        # try:
        #     read_size = 1
        #     i2c_controller.readfrom(RESPONDER_ADDRESS, read_size)
        #     print('ACK')
        # except OSError:
        #     print('No ACK')
        #     pass
        time.sleep(1)

    # counter = 1
    # try:
    #     while True:
    #         if i2c_responder.any():
    #             print(i2c_responder.get())
    #         if i2c_responder.anyRead():
    #             counter = counter + 1
    #             i2c_responder.put(counter & 0xFF)

    # except KeyboardInterrupt:
    #     pass


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
