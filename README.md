# I2CResponder
**Note:** This project uses I2C "Controller/Responder" nomenclature per [this article.](https://www.eetimes.com/its-time-for-ieee-to-retire-master-slave/)

I2C Responder support is not yet present in Pico micropython (as of MicroPython v1.14).
This project implements (in Python) a polled Raspberry Pico I2C Responder by accessing the Pico hardware registers directly.

## Credits
The implementation is largely built upon the work of `danjperron` appearing in [this forum post](https://www.raspberrypi.org/forums/viewtopic.php?f=146&t=302978&sid=164b1038e60b43a22d1af6b6ba69f6ae).

## Test application
The project includes a test application which runs on a single Raspberry Pico to exercise the API of the I2CResponder() class by looping two I2C ports to each other.

To execute this application you will need to wire I2C0 and I2C1 together as follows:
```

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
```

## Output
```
>>> 
Testing I2CResponder v1.0.0
Scanning I2C Bus for Responders...
I2C Addresses of Responders found: [0x41]

Controller: Issuing I2C WRITE with data: [0x01, 0x02]
   Responder: Getting I2C WRITE data...
   Responder: Received I2C WRITE data: [0x01, 0x02]

Controller: Initiating I2C READ...
   Responder: Transmitted I2C READ data: 0x09
   Responder: Transmitted I2C READ data: 0x08
Conroller: Received I2C READ data: [0x09, 0x08]
 
>>>
```

### Core API

```python
    def read_is_pending(self):
        """Return True if the Controller has issued an I2C READ command.

        If this function returns True then the Controller has issued an
        I2C READ, which means that its I2C engine is currently blocking
        waiting for us to respond with the requested I2C READ data.
        """

    def put_read_data(self, data):
        """Issue requested I2C READ data to the requesting Controller.

        This function should be called to return the requested I2C READ
        data when read_is_pending() returns True.

        Args:
            data (int): A byte value to send.
        """
    
    def write_data_is_available(self):
        """Check whether incoming (I2C WRITE) data is available.

        Returns:
            True if data is available, False otherwise.
        """

    def get_write_data(self, max_size=1):
        """Get incoming (I2C WRITE) data.

        Will return bytes from the Rx FIFO, if present, up to the requested size.

        Args:
            max_size (int): The maximum number of bytes to fetch.
        Returns:
            A list containing 0 to max_size bytes.
        """
```