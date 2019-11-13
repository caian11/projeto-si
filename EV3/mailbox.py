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

    def raw_bytes(data):
        """
        Simple hex decode of the supplied byte stream
        """

        return " ".join("{:02x}".format(c) for c in data)

    def encode(name, value, type):
        """
        Given a name, value, and type, encode the Mailbox byte stream
        """

        if type not in Mailbox.Type.types():
            raise TypeError('Unknown type {}'.format(type))

        nameBytes = (name + '\x00').encode('latin-1')
        nameLen   = len(nameBytes)

        if type == Mailbox.Type.BOOL:
            contentBytes = struct.pack('B', 1 if value == True else 0)

        if type == Mailbox.Type.NUMBER:
            contentBytes = struct.pack('f',float(value))

        if type == Mailbox.Type.TEXT:
            contentBytes = (value + '\x00').encode('latin-1')

        contentLen = len(contentBytes)

        # 4ByteHeader + NameLenByte + NameBytes + ContentLen2Bytes + Content
        totalLen   = nameLen + contentLen + 7

        return(struct.pack(
            '<H4sB{}sH{}s'.format(nameLen+1,contentLen),
            totalLen, Mailbox.headerBytes,
            nameLen, nameBytes,
            contentLen, contentBytes
        ))

    def unpack(message):
        """
        Unpack a Mailbox message to its name and payload.
        The payload type cannot be known before its name is known and handled
        by this method's caller. A second function will be used to decode
        a payload for a given type.
        """

        mailboxSize = (struct.unpack_from('<H', message, 0))[0]

        # Shortest message is a boolean:
        # HHHH L N 0 LL B = 10 bytes
        if mailboxSize < 10:
            raise BufferError(
                'Payload is too small: {} < 10'.format(mailboxSize)
            )

        # Check that we have a Mailbox message header
        header = (struct.unpack_from('<4s', message, 2))[0]
        if header != Mailbox.headerBytes:
            raise BufferError('Not a Mailbox message {} != {}'.format(
                header, Mailbox.headerBytes
            ))

        # Get the name and its length
        nameLen    = (struct.unpack_from('<B', message, 6))[0] - 1
        name, null =  struct.unpack_from('<{}sB'.format(nameLen), message, 7)

        if null != 0:
            raise BufferError('Name not NULL terminated')

        # Get the content and its length
        contentLen = (struct.unpack_from('<H', message, 8 + nameLen))[0]

        if 8 + nameLen + contentLen != mailboxSize:
            raise BufferError(
              'Mailbox size error: Packet {} != Declared{}'.format(
                  mailboxSize, 8 + nameLen + contentLen
              )
            )

        content = (struct.unpack_from(
            '<{}s'.format(contentLen), message, 10 + nameLen
        ))[0]

        return(name.decode('latin-1'), content)

    def decode(content, type):
        """
        Given the content, decode it based on the supplied type.
        """

        if type not in Mailbox.Type.types():
            raise TypeError('Unknown type {}'.format(type))

        if len(content) == 0:
            raise BufferError('Content must be at least 1 byte')

        if type == Mailbox.Type.BOOL:
            if len(content) != 1:
                raise TypeError('Wrong size for a boolean')

            value = True if (struct.unpack('B', content))[0] else False

        if type == Mailbox.Type.NUMBER:
            if len(content) != 4:
                raise TypeError('Wrong size for a float')

            value = (struct.unpack('f', content))[0]

        if type == Mailbox.Type.TEXT:
            value = content[:-1].decode('latin-1')

        return value

if __name__ == '__main__':
    tests = [
        ["string","mortimer",Mailbox.Type.TEXT],
        ["true",True,Mailbox.Type.BOOL],
        ["T",True,Mailbox.Type.BOOL],
        ["false",False,Mailbox.Type.BOOL],
        ["F",False,Mailbox.Type.BOOL],
        ["number",3.141,Mailbox.Type.NUMBER],
    ]

    for test in tests:
        message = Mailbox.encode(test[0], test[1], test[2])
        print(message)
        print(Mailbox.raw_bytes(message))
        name, content = Mailbox.unpack(message)
        print(name, content)
        value = Mailbox.decode(content, test[2])
        print(value)
