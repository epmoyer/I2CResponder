# https://www.raspberrypi.org/forums/viewtopic.php?f=146&t=302978
from machine import mem32, mem8, Pin


class I2CResponder:
    I2C0_BASE = 0x40044000
    I2C1_BASE = 0x40048000
    IO_BANK0_BASE = 0x40014000

    mem_rw = 0x0000
    mem_xor = 0x1000
    mem_set = 0x2000
    mem_clr = 0x3000

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

    def write_reg(self, reg, data, method=0):
        mem32[self.i2c_base | method | reg] = data

    def set_reg(self, reg, data):
        self.write_reg(reg, data, method=self.mem_set)

    def clr_reg(self, reg, data):
        self.write_reg(reg, data, method=self.mem_clr)

    def __init__(self, i2cID=0, sda=0, scl=1, responder_address=0x41):
        self.scl = scl
        self.sda = sda
        self.responder_address = responder_address
        self.i2c_ID = i2cID
        if self.i2c_ID == 0:
            self.i2c_base = self.I2C0_BASE
        else:
            self.i2c_base = self.I2C1_BASE

        # 1 Disable DW_apb_i2c
        self.clr_reg(self.IC_ENABLE, 1)
        # 2 set responder address
        # clr bit 0 to 9
        # set responder address
        self.clr_reg(self.IC_SAR, 0x1FF)
        self.set_reg(self.IC_SAR, self.responder_address & 0x1FF)
        # 3 write IC_CON  7 bit, enable in responder-only
        self.clr_reg(self.IC_CON, 0b01001001)
        # set SDA PIN
        mem32[self.IO_BANK0_BASE | self.mem_clr | (4 + 8 * self.sda)] = 0x1F
        mem32[self.IO_BANK0_BASE | self.mem_set | (4 + 8 * self.sda)] = 3
        # set SLA PIN
        mem32[self.IO_BANK0_BASE | self.mem_clr | (4 + 8 * self.scl)] = 0x1F
        mem32[self.IO_BANK0_BASE | self.mem_set | (4 + 8 * self.scl)] = 3
        # 4 enable i2c
        self.set_reg(self.IC_ENABLE, 1)

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

    def any(self):
        # get IC_STATUS
        status = mem32[self.i2c_base | self.IC_STATUS]
        # check RFNE receive FIFO not empty
        if status & 8:
            return True
        return False

    def get(self):
        while not self.any():
            pass
        return mem32[self.i2c_base | self.IC_DATA_CMD] & 0xFF

