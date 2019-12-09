#!/usr/bin/env python3

# A Python3 class for encoding and decoding EV3g Mailbox messages
# Copyright (C) 2019 Jerry Nicholls <jerry@jander.me.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
import struct

class EV3Mailbox:
    """
    Class to handle the encoding and decoding of the EV3g Mailbox byte stream.
    """

    headerBytes = '\x01\x00\x81\x9e'.encode('latin-1')

    def __init__(self, name, value, d_type, payload):
        """
        Base object with all the data
        """

        self.name    = name
        self.value   = value
        self.d_type  = d_type
        self.payload = payload

    def __str__(self):
        """
        String representation of the mailbox
        """

        return 'Mailbox: {}={}'.format(self.name, self.value)

    @staticmethod
    def _decode(payload, d_type=None):
        """
        Decode a Mailbox message to its name and value.

        Attempt to determine the type from the length of the contents, unless an
        explicit type (d_type) was given.
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
        if header != EV3Mailbox.headerBytes:
            raise BufferError('Not a Mailbox message {} != {}'.format(
                header, EV3Mailbox.headerBytes
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

        if d_type == None:
            # Attempt to work out the type. Assume text to start.
            d_type  = str

            if len(valueBytes) == 1:
                d_type = bool

            # A 3 char string is indistinguishable from a float in terms of
            # length. A string will end in a \x00 but so can certain floats.
            # Assume it's a number if the last byte is not a 0 or there is
            # another zero in the bytes - e.g. Number 0 = \x00\x00\x00\x00.

            if (len(valueBytes) == 4 and
                (valueBytes[-1] != 0 or 0 in valueBytes[0:3])):
                d_type  = float

        # Double check the type as it may have been supplied.
        if d_type not in (bool, int, float, str):
            raise TypeError('Unknown type {}'.format(d_type))

        if d_type == bool:
            if len(valueBytes) != 1:
                raise TypeError('Wrong size for a boolean')

            value = True if (struct.unpack('B', valueBytes))[0] else False

        if d_type in (int, float):
            if len(valueBytes) != 4:
                raise TypeError('Wrong size for a number')

            value = (struct.unpack('f', valueBytes))[0]

        if d_type == str:
            if valueBytes[-1] != 0:
                raise BufferError('Text value not NULL terminated')
                
            value = valueBytes[:-1].decode('latin-1')

        return name, value, d_type

    @classmethod
    def encode(cls, name, value, d_type=None):
        """
        Create a mailbox based on a name, value and type (d_type).

        Encode the message based on those parameters.
        """

        # Attempt to define the d_type based on the instance type of the value
        # or coerce it based on the supplied type
        if d_type == None:
            d_type = type(value)

        if d_type not in (bool, int, float, str):
            raise TypeError('Unable to handle type {}'.format(d_type))
        else:
            s_type = type(value)
            try:
                value = d_type(value)
            except:
                raise TypeError('Unable to coerce type {} to {}'.format(s_type,d_type))

        nameBytes = (name + '\x00').encode('latin-1')
        nameLen   = len(nameBytes)

        if d_type == bool:
            valueBytes = struct.pack('B', 1 if value == True else 0)

        if d_type in (int, float):
            valueBytes = struct.pack('f',float(value))

        if d_type == str:
            valueBytes = (value + '\x00').encode('latin-1')

        valueLen = len(valueBytes)

        # 4ByteHeader + NameLenByte + NameBytes + ValueLen2Bytes + ValueBytes
        totalLen = nameLen + valueLen + 7

        payload = struct.pack(
            '<H4sB{}sH{}s'.format(nameLen,valueLen),
            totalLen, EV3Mailbox.headerBytes,
            nameLen, nameBytes,
            valueLen, valueBytes
        )

        return cls(name,value,d_type,payload)

    @classmethod
    def decode(cls, payload):
        """
        Create a new Mailbox object based upon its payload
        """

        name, value, d_type = EV3Mailbox._decode(payload)

        return cls(name, value, d_type, payload)

    def force_number(self):
        """
        Change this object's type and value to a float
        """
        name, value, d_type = EV3Mailbox._decode(self.payload, float)

        self.d_type   = d_type
        self.value = value

    def raw_bytes(self):
        """
        Simple hex decode of the internal byte stream
        """

        return ' '.join('{:02x}'.format(c) for c in self.payload)

if __name__ == '__main__':
    tests = [
        ['monty','python'],
        ['true',True],
        ['T',True],
        ['false',False],
        ['F',False],
        ['number',3.141],
        ['zero',0],
        ['ZERO','000'],
        ['ReallySmall',5.90052E-39],
    ]

    for test in tests:
        message = EV3Mailbox.encode(test[0], test[1])
        print('Encode --------------------')
        print(message)
        #print(message.raw_bytes())

        payload = message.payload
        decoded = EV3Mailbox.decode(payload)
        print('Decode --------------------')
        print(decoded)
        print()

        if test[0] == 'ReallySmall':
            print('Forcing to a number')
            decoded.force_number()
            print(decoded)
            print()
