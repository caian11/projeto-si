#!/usr/bin/env python3
import struct

class Mailbox:
    BOOL, NUMBER, TEXT = range(3)

    headerBytes = '\x01\x00\x82\x9e'.encode('latin-1')

    def raw_bytes(data):
        return " ".join("{:02x}".format(c) for c in data)

    def encode(name, value, type):
        nameBytes = (name + '\x00').encode('latin-1')
        nameLen   = len(nameBytes)

        if type == Mailbox.BOOL:
            contentBytes = struct.pack('B', 1 if value == True else 0)

        if type == Mailbox.NUMBER:
            contentBytes = struct.pack('f',float(value))

        if type == Mailbox.TEXT:
            contentBytes = (value + '\x00').encode('latin-1')

        contentLen = len(contentBytes)

        # 4ByteHeader + NameLenByte + Name + ContentLen2Bytes + Content
        totalLen   = nameLen + contentLen + 7

        return(struct.pack(
            '<H4sB{}sH{}s'.format(nameLen,contentLen),
            totalLen, Mailbox.headerBytes,
            nameLen, nameBytes,
            contentLen, contentBytes
        ))

if __name__ == '__main__':
    print(Mailbox.encode("string","mortimer",Mailbox.TEXT))
    print(Mailbox.encode("true",True,Mailbox.BOOL))
    print(Mailbox.encode("false",True,Mailbox.BOOL))
    print(Mailbox.encode("number",3.141,Mailbox.NUMBER))
