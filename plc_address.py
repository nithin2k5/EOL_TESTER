"""Modbus bit numbers for the PLC's bit device addresses.

The PLC names bits LS XGB style: a device letter, a word number in decimal,
then the bit within that word as one hex digit. M0067 is word 6, bit 7, and
M1000 is word 100, bit 0. Each word holds 16 bits, so the Modbus coil (or
discrete input) number is word * 16 + bit:

    M0067 -> 103     M009A -> 154     M1000 -> 1600     P0004 -> 4

Reading the whole address as one hex number gives the same answer only
while the word is below 10; M1000 read that way is 4096, which the PLC
does not have.
"""


def bit_address(address):
    """Modbus bit number for an address such as M009A or P0004.

    Raises ValueError for an address that is empty or not in that form.
    """
    digits = address.strip()[1:]
    if not digits:
        raise ValueError(f"No word or bit in PLC address {address!r}")
    return int(digits[:-1] or '0') * 16 + int(digits[-1], 16)
