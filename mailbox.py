#!/usr/bin/env python3
import struct
from enum import Enum

class Mailbox:
    """
    Class to handle the encoding and decoding of the EV3g Mailbox byte stream.
    """

    class Type(Enum):
        """
        Simple enums to define the message types.
        """

        BOOL   = 1
        NUMBER = 2
        TEXT   = 3

    headerBytes = '\x01\x00\x81\x9e'.encode('latin-1')

    def __init__(self, name, value, fmt, payload):
        """
        Base object with all the data
        """

        self.name    = name
        self.value   = value
        self.fmt     = fmt
        self.payload = payload

    def __str__(self):
        """
        String representation of the mailbox
        """

        return 'Name: {} Value: {} Format: {} Payload:\n{}'.format(
            self.name, self.value, self.fmt, self.payload
        )

    @staticmethod
    def _decode(payload, fmt=None):
        """
        Decode a Mailbox message to its name and value.

        Attempt to determine the type from the length of the contents, unless an
        explicit type (fmt) was given.
        """

        # Shortest message is a boolean:
        # HHHH L N 0 LL B = 10 bytes
        mailboxSize = (struct.unpack_from('<H', payload, 0))[0]
        if mailboxSize < 10:
            raise BufferError(
                'Payload is too small: {} < 10'.format(mailboxSize)
            )

        # Check that we have a Mailbox message header
        header = (struct.unpack_from('<4s', payload, 2))[0]
        if header != Mailbox.headerBytes:
            raise BufferError('Not a Mailbox message {} != {}'.format(
                header, Mailbox.headerBytes
            ))

        # Get the name and its length
        nameLen    = (struct.unpack_from('<B', payload, 6))[0] - 1
        name, null =  struct.unpack_from('<{}sB'.format(nameLen), payload, 7)

        if null != 0:
            raise BufferError('Name not NULL terminated')

        name = name.decode('latin-1')

        # Get the value and its length
        valueLen = (struct.unpack_from('<H', payload, 8 + nameLen))[0]

        if 8 + nameLen + valueLen != mailboxSize:
            raise BufferError(
              'Mailbox size error: Actual={} != Expected={}'.format(
                  mailboxSize, 8 + nameLen + valueLen
              )
            )

        valueBytes = (struct.unpack_from(
            '<{}s'.format(valueLen), payload, 10 + nameLen
        ))[0]

        if fmt == None:
            # Attempt to work out the type. Assume text to start.
            fmt  = Mailbox.Type.TEXT

            if len(valueBytes) == 1:
                fmt = Mailbox.Type.BOOL

            # A 3 char string is indistinguishable from a float in terms of
            # length. A string will end in a \x00 but so can certain floats.
            # Assume it's a number if the last byte is not a 0 or there is
            # another zero in the bytes - e.g. Number 0 = \x00\x00\x00\x00.

            if (len(valueBytes) == 4 and
                (valueBytes[-1] != 0 or 0 in valueBytes[0:3])):
                fmt  = Mailbox.Type.NUMBER

        # Double check the type as it may have been supplied.
        if fmt not in Mailbox.Type:
            raise TypeError('Unknown type {}'.format(fmt))

        if fmt == Mailbox.Type.BOOL:
            if len(valueBytes) != 1:
                raise TypeError('Wrong size for a boolean')

            value = True if (struct.unpack('B', valueBytes))[0] else False

        if fmt == Mailbox.Type.NUMBER:
            if len(valueBytes) != 4:
                raise TypeError('Wrong size for a float')

            value = (struct.unpack('f', valueBytes))[0]

        if fmt == Mailbox.Type.TEXT:
            if valueBytes[-1] != 0:
                raise BufferError('Text value not NULL terminated')
            value = valueBytes[:-1].decode('latin-1')

        return name, value, fmt

    @classmethod
    def encode(cls, name, value, fmt):
        """
        Create a mailbox based on a name, value and type (fmt).

        Encode the message based on those parameters.
        """

        if fmt not in Mailbox.Type:
            raise TypeError('Unknown type {}'.format(fmt))

        nameBytes = (name + '\x00').encode('latin-1')
        nameLen   = len(nameBytes)

        if fmt == Mailbox.Type.BOOL:
            valueBytes = struct.pack('B', 1 if value == True else 0)

        if fmt == Mailbox.Type.NUMBER:
            valueBytes = struct.pack('f',float(value))

        if fmt == Mailbox.Type.TEXT:
            valueBytes = (value + '\x00').encode('latin-1')

        valueLen = len(valueBytes)

        # 4ByteHeader + NameLenByte + NameBytes + ValueLen2Bytes + ValueBytes
        totalLen = nameLen + valueLen + 7

        payload = struct.pack(
            '<H4sB{}sH{}s'.format(nameLen,valueLen),
            totalLen, Mailbox.headerBytes,
            nameLen, nameBytes,
            valueLen, valueBytes
        )

        return cls(name,value,fmt,payload)

    @classmethod
    def decode(cls, payload):
        """
        Create a new Mailbox object based upon its payload
        """

        name, value, fmt = Mailbox._decode(payload)

        return cls(name, value, fmt, payload)

    def force_number(self):
        """
        Change this object's type and value to a float
        """
        name, value, fmt = Mailbox._decode(self.payload, Mailbox.Type.NUMBER)

        self.fmt   = fmt
        self.value = value

    def raw_bytes(self):
        """
        Simple hex decode of the internal byte stream
        """

        return ' '.join('{:02x}'.format(c) for c in self.payload)

if __name__ == '__main__':
    tests = [
        ['monty','python',Mailbox.Type.TEXT],
        ['true',True,Mailbox.Type.BOOL],
        ['T',True,Mailbox.Type.BOOL],
        ['false',False,Mailbox.Type.BOOL],
        ['F',False,Mailbox.Type.BOOL],
        ['number',3.141,Mailbox.Type.NUMBER],
        ['zero',0,Mailbox.Type.NUMBER],
        ['ZERO','000',Mailbox.Type.TEXT],
        ['ReallySmall',5.90052E-39,Mailbox.Type.NUMBER],
    ]

    for test in tests:
        message = Mailbox.encode(test[0], test[1], test[2])
        print('Encode --------------------')
        print(message)
        #print(message.raw_bytes())

        payload = message.payload
        decoded = Mailbox.decode(payload)
        print('Decode --------------------')
        print(decoded)
        print()

        if test[0] == 'ReallySmall':
            print('Forcing to a number')
            decoded.force_number()
            print(decoded)
            print()
