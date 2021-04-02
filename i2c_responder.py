from machine import mem32, mem8, Pin


class I2CResponder:
    # Register base addresses
    I2C0_BASE = 0x40044000
    I2C1_BASE = 0x40048000
    IO_BANK0_BASE = 0x40014000

    # Register access method control flags
    REG_ACCESS_METHOD_RW = 0x0000
    REG_ACCESS_METHOD_XOR = 0x1000
    REG_ACCESS_METHOD_SET = 0x2000
    REG_ACCESS_METHOD_CLR = 0x3000

    # Register address offsets
    IC_CON = 0
    IC_TAR = 4
    IC_SAR = 8
    IC_DATA_CMD = 0x10
    IC_RAW_INTR_STAT = 0x34
    IC_RX_TL = 0x38
    IC_TX_TL = 0x3C
    IC_CLR_INTR = 0x40
    IC_CLR_RD_REQ = 0x50
    IC_CLR_TX_ABRT = 0x54
    IC_ENABLE = 0x6C
    IC_STATUS = 0x70

    # GPIO Register block size (i.e.) per GPIO
    GPIO_REGISTER_BLOCK_SIZE = 8

    # GPIO Register offsets within a GPIO Block
    GPIOxCTRL = 0x04

    # Register bit definitions
    IC_STATUS__RFNE = 0x08  # Receive FIFO Not Empty
    IC_ENABLE__ENABLE = 0x01
    IC_SAR__IC_SAR = 0x1FF  # Responder address
    IC_CON__CONTROLLER_MODE = 0x01
    IC_CON__IC_10BITADDR_RESPONDER = 0x08
    IC_CON__IC_RESPONDER_DISABLE = 0x40
    GPIOxCTRL__FUNCSEL = 0x1F
    GPIOxCTRL__FUNCSEL__I2C = 3

    def write_reg(self, register_offset, data, method=0):
        mem32[self.i2c_base | method | register_offset] = data

    def set_reg(self, register_offset, data):
        self.write_reg(register_offset, data, method=self.REG_ACCESS_METHOD_SET)

    def clr_reg(self, register_offset, data):
        self.write_reg(register_offset, data, method=self.REG_ACCESS_METHOD_CLR)

    def __init__(self, i2c_device_id=0, sda_gpio=0, scl_gpio=1, responder_address=0x41):
        self.scl_gpio = scl_gpio
        self.sda_gpio = sda_gpio
        self.responder_address = responder_address
        self.i2c_device_id = i2c_device_id
        self.i2c_base = self.I2C0_BASE if i2c_device_id == 0 else self.I2C1_BASE
        # Disable I2C engine while initializing it
        self.clr_reg(self.IC_ENABLE, self.IC_ENABLE__ENABLE)
        # Clear Responder address bits
        self.clr_reg(self.IC_SAR, self.IC_SAR__IC_SAR)
        # Set Responder address
        self.set_reg(self.IC_SAR, self.responder_address & self.IC_SAR__IC_SAR)
        # Clear 10 Bit addressing bit (i.e. enable 7 bit addressing)
        # Clear CONTROLLER bit (i.e. we are a Responder)
        # Clear RESPONDER_DISABLE bit (i.e. we are a Responder)
        self.clr_reg(
            self.IC_CON,
            (
                self.IC_CON__CONTROLLER_MODE
                | self.IC_CON__IC_10BITADDR_RESPONDER
                | self.IC_CON__IC_RESPONDER_DISABLE
            ),
        )
        # Configure SDA PIN to select "I2C" function
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_CLR
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.sda_gpio)
        ] = self.GPIOxCTRL__FUNCSEL
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_SET
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.sda_gpio)
        ] = self.GPIOxCTRL__FUNCSEL__I2C
        # Configure SCL PIN to select "I2C" function
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_CLR
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.scl_gpio)
        ] = self.GPIOxCTRL__FUNCSEL
        mem32[
            self.IO_BANK0_BASE
            | self.REG_ACCESS_METHOD_SET
            | (self.GPIOxCTRL + self.GPIO_REGISTER_BLOCK_SIZE * self.scl_gpio)
        ] = self.GPIOxCTRL__FUNCSEL__I2C
        # Enable i2c engine
        self.set_reg(self.IC_ENABLE, self.IC_ENABLE__ENABLE)

    def anyRead(self):
        status = mem32[self.i2c_base | self.IC_RAW_INTR_STAT] & 0x20
        if status:
            return True
        return False

    def put(self, data):
        # reset flag
        self.clr_reg(self.IC_CLR_TX_ABRT, 1)
        status = mem32[self.i2c_base | self.IC_CLR_RD_REQ]
        mem32[self.i2c_base | self.IC_DATA_CMD] = data & 0xFF

    def rx_data_is_available(self):
        """Check whether incoming (I2C write) data is available.

        Returns:
            True if data is available, False otherwise.
        """
        # get IC_STATUS
        status = mem32[self.i2c_base | self.IC_STATUS]
        # Check RFNE (Receive FIFO not empty)
        if status & self.IC_STATUS__RFNE:
            # There is data in the Zx FIFO
            return True
        # The Rx FIFO is empty
        return False

    def get_rx_data(self, max_size=1):
        """Get incoming (I2C write) data.

        Will return bytes from the Rx FIFO, if present, up to the requested size.

        Args:
            max_size [int]: The maximum number of bytes to fetch.
        Returns:
            A list containing 0 to max_size bytes.
        """
        data = []
        while len(data) < max_size and self.rx_data_is_available():
            data.append(mem32[self.i2c_base | self.IC_DATA_CMD] & 0xFF)
        return data
