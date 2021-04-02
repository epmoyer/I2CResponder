"""I2CResponder Test Application.

NOTE: This module uses I2C Controller/Responder nomenclature per
      https://www.eetimes.com/its-time-for-ieee-to-retire-master-slave/

This test application runs on a single Raspberry Pico to exercise the API of the
I2CResponder() class.

To execute this application you will need to wire I2C0 and I2C1 together as follows:


   +---- 3.3V -------------------------------------------------------------------+
   |                                                                             |
   |                      +======================= Pico ====================+    |
   |   1K Ohm             I                                                 I    |
   +--/\/\/\/----O--------I Pin 1 (GP0, I2C0 SDA)                    PIN 40 I    |
   |             |        I                                                 I    |
   |             |    +---I Pin 2 (GP1, I2C0 SCL)                    PIN 39 I    |
   |             |    |   I                                                 I    |
   |             |    |   I Pin 2                                    PIN 38 I    |
   |             |    |   I                                                 I    |
   |             |--------I Pin 4 (GP2, I2C1 SDA)                    PIN 37 I    |
   |   1K Ohm         |   I                                                 I    |
   +--/\/\/\/---------O---I Pin 5 (GP3, I2C1 SCL)         (3V3(OUT)) PIN 36 I----+
                          I                                                 I
                          I                                                 I
"""

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

    # -----------------
    # Initialize Responder and Controller
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL, responder_address=RESPONDER_ADDRESS
    )
    i2c_controller = I2C(
        CONTROLLER_I2C_DEVICE_ID,
        scl=Pin(GPIO_CONTROLLER_SCL),
        sda=Pin(GPIO_CONTROLLER_SDA),
        freq=I2C_FREQUENCY,
    )
    print('Testing I2CResponder v' + i2c_responder.VERSION)

    # -----------------
    # Demonstrate that the Responder is responding at its assigned I2C address.
    # -----------------
    print('Scanning I2C Bus for Responders...')
    responder_addresses = i2c_controller.scan()
    print('I2C Addresses of Responders found: ' + format_hex(responder_addresses))
    print()

    # -----------------
    # Demonstrate I2C WRITE
    # -----------------
    buffer_out = bytearray([0x01, 0x02])
    print('Controller: Issuing I2C WRITE with data: ' + format_hex(buffer_out))
    i2c_controller.writeto(RESPONDER_ADDRESS, buffer_out)
    time.sleep(0.25)

    print('   Responder: Getting I2C WRITE data...')
    buffer_in = i2c_responder.get_write_data(max_size=len(buffer_out))
    print('   Responder: Received I2C WRITE data: ' + format_hex(buffer_in))
    print()

    # -----------------
    # Demonstrate I2C READ
    # -----------------
    # NOTE: We want the Controller to initiate an I2C READ, but the Responder implementation
    #   is polled.  As soon as we execute i2c_controller.readfrom() we will block
    #   until the I2C bus supplies the requested data.  But we need to have executional
    #   control so that we can poll i2c_responder.read_is_pending() and then supply the
    #   requested data.  To circumvent the deadlock, we will briefly launch a thread on the
    #   second Pico core, and THAT thread will execute the .readfrom().  That thread will block
    #   while this thread polls, then supplies the requested data.
    # -----------------
    thread_lock = _thread.allocate_lock()
    _thread.start_new_thread(thread_i2c_controller_read, (i2c_controller, thread_lock,))

    buffer_out = bytearray([0x09, 0x08])
    for value in buffer_out:
        # We will loop here (polling) until the Controller (running on its own thread) issues an
        # I2C READ.
        while not i2c_responder.read_is_pending():
            pass
        i2c_responder.put_read_data(value)
        with thread_lock:
            print('   Responder: Transmitted I2C READ data: ' + format_hex(value))
    time.sleep(1)
    print('Controller: Received I2C READ data: ' + format_hex(READBUFFER))

def thread_i2c_controller_read(i2c_controller, thread_lock):
    """Issue an I2C READ on the Controller."""
    with thread_lock:
        print('Controller: Initiating I2C READ...')
    # NOTE: This operation will BLOCK until the Responder supplies the requested
    #       data, which is why we are running it on a second thread (on the second
    #       Pico core).
    data = i2c_controller.readfrom(RESPONDER_ADDRESS, 2)

    for i, value in enumerate(data):
        READBUFFER[i] = value


def format_hex(_object):
    """Format a value or list of values as 2 digit hex."""
    try:
        values_hex = [to_hex(value) for value in _object]
        return '[{}]'.format(', '.join(values_hex))
    except TypeError:
        # The object is a single value
        return to_hex(_object)


def to_hex(value):
    return '0x{:02X}'.format(value)


if __name__ == "__main__":
    main()
