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

        def types():
            return(Mailbox.Type.BOOL, Mailbox.Type.NUMBER, Mailbox.Type.TEXT)

    headerBytes = '\x01\x00\x81\x9e'.encode('latin-1')

    def __init__(self, name, value, type, payload):
        """
        Base object with all the data
        """

        self.name    = name
        self.value   = value
        self.type    = type
        self.payload = payload

    def __str__(self):
        """
        String representation of the mailbox
        """

        return 'Name: {} Value: {} Type: {} Payload:\n{}'.format(
            self.name, self.value, self.type, self.payload
        )

    @staticmethod
    def _decode_as(payload, type):
        """
        Decode a payload based on the supplied type.
        """

        if type not in Mailbox.Type.types():
            raise TypeError('Unknown type {}'.format(type))

        if type == Mailbox.Type.BOOL:
            if len(payload) != 1:
                raise TypeError('Wrong size for a boolean')

            value = True if (struct.unpack('B', payload))[0] else False

        if type == Mailbox.Type.NUMBER:
            if len(payload) != 4:
                raise TypeError('Wrong size for a float')

            value = (struct.unpack('f', payload))[0]

        if type == Mailbox.Type.TEXT:
            value = payload[:-1].decode('latin-1')

        return value

    @classmethod
    def encode(cls, name, value, type):
        """
        Create a mailbox based on a name, value and type.

        Encode the message based on those paremeters.
        """

        if type not in Mailbox.Type.types():
            raise TypeError('Unknown type {}'.format(type))

        nameBytes = (name + '\x00').encode('latin-1')
        nameLen   = len(nameBytes)

        if type == Mailbox.Type.BOOL:
            valueBytes = struct.pack('B', 1 if value == True else 0)

        if type == Mailbox.Type.NUMBER:
            valueBytes = struct.pack('f',float(value))

        if type == Mailbox.Type.TEXT:
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

        return cls(name,value,type,payload)

    @classmethod
    def decode(cls,payload, type=None):
        """
        Decode a Mailbox message to its name and value.

        
        If no explicit type is given, attempt to determine that from the
        length of the contents. An explit type is allowed to ensure that
        a number is treated as a number. Really small numbers could be
        determined to be a string.
        """

        mailboxSize = (struct.unpack_from('<H', payload, 0))[0]

        # Shortest message is a boolean:
        # HHHH L N 0 LL B = 10 bytes
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

        print("Name {} NameLen {} ValueLen {}".format(name,nameLen,valueLen))

        if 8 + nameLen + valueLen != mailboxSize:
            raise BufferError(
              'Mailbox size error: Packet={} != Expected={}'.format(
                  mailboxSize, 8 + nameLen + valueLen
              )
            )

        valueBytes = (struct.unpack_from(
            '<{}s'.format(valueLen), payload, 10 + nameLen
        ))[0]

        # If no explicit type was given, attempt to work it out
        if type == None:
            type  = Mailbox.Type.TEXT

            if len(valueBytes) == 1:
                type = Mailbox.Type.BOOL

            # A 3 char string is indistinguishable from a float in terms of
            # length. A string will end in a \x00 but so can certain floats.
            # Assume it's a number if the last byte is not a 0 or there is
            # another zero in the bytes - e.g. Number 0 = \x00\x00\x00\x00.

            if (len(valueBytes) == 4 and
                (valueBytes[-1] != 0 or 0 in valueBytes[0:3])):
                type  = Mailbox.Type.NUMBER

        value = Mailbox._decode_as(valueBytes, type)

        return cls(name, value, type, payload)

    def decode_as(self, type):
        """
        Decode the object's payload based on the supplied type.
        """

        return Mailbox._decode_as(self.payload, type)

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
