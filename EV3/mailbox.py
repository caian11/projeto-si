#!/usr/bin/env python3
import struct
from enum import Enum

class MailboxType(Enum):
    BOOL   = 0
    NUMBER = 1
    TEXT    = 2

class Mailbox:
    headerBytes = '\x01\x00\x82\x9e'.encode('latin-1')

    def raw_bytes(data):
        return " ".join("{:02x}".format(c) for c in data)

    def encode(name, value, type):
        name    = name + '\x00'
        nameLen = len(name)
        packFmt = '<H4BB{}B'.format(nameLen)

        if type == MailboxType.BOOL:
            content = 1 if value == True else 0
            packFmt = packFmt + '<HB'

        if type == MailboxType.NUMBER:
            content = float(value)
            packFmt = packFmt + '<Hf'

        if type == MailboxType.TEXT:
            value   = value + '\x00'
            content = value.encode('latin-1')
            packFmt = packFmt + '<H{}B'.format(len(content))

        print(packFmt)
            

if __name__ == '__main__':
    Mailbox.encode("bob","mortimer",MailboxType.TEXT)
