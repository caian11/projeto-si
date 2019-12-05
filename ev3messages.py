#!/usr/bin/env python3

# A Python3 class for encoding and decoding EV3g Mailbox messages
# Copyright (C) 2019 Jerry Nicholls
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
    
import threading
import time
import sys
import bluetooth
from ev3mailbox import EV3Mailbox

class EV3Messages():
    """
    Class to handle sending and recieving of EV3 Mailbox messages
    """

    class Message():
        """
        Class to contain attributes for each message
        """

        def __init__(self,name):
            self.name  = name
            self.event = threading.Event()
            self.lock  = threading.Lock()
            self.fifo  = []

            self.event.clear()

        def add(self, msg):
            """
            Add a new mailbox message to FIFO and trigger any listeners
            """
            with self.lock:
                self.fifo.append(msg)
                self.event.set()

        def get(self, timeout=None):     
            """
            Wait for a mailbox and return it
            """       
            received = self.event.wait(timeout)

            msg = None
            if received == True:
                with self.lock:
                    msg = self.fifo.pop(0) if len(self.fifo) != 0 else None
                    if len(self.fifo) == 0:
                        self.event.clear()

            return(msg)

    def connect(self):
        """
        Ensure we're connected to the remote EV3
        """
        with self.bt_lock:
            if self.bt_socket == None:
                bt_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

                print("{}: Connection attempt to {}".format(time.asctime(), self.bt_address), file=sys.stderr)
                try:
                    bt_socket.connect((self.bt_address, 1))
                    bt_socket.settimeout(5)
                    self.bt_socket = bt_socket
                    print("{}: BT Connected".format(time.asctime()), file=sys.stderr)
                except:
                    print("{}: BT failed to connect".format(time.asctime()), file=sys.stderr)
                    raise #OSError("Failed to connect to EV3g") from None

    def disconnect(self):
        """
        Disconnect the socket
        """
        with self.bt_lock:
            if self.bt_socket != None:
                self.bt_socket.close()
            self.bt_socket = None

    def get(self, name=None, timeout=None):
        """
        Wait for a message of the given name
        """
        msg = None

        if name != None:
            with self.msgs_lock:
                if name not in self.messages:
                    self.messages[name] = EV3Messages.Message(name)
                message = self.messages[name]

            msg = message.get(timeout)

        return msg

    def send(self,name,value,fmt=None):
        try:
            self.connect()
        except:
            raise

        ev3mailbox = EV3Mailbox.encode(name, value, fmt)

        try:
            self.bt_socket.send(ev3mailbox.payload)
        except:
            print("{}: Failed to send".format(time.asctime()), file=sys.stderr)
            self.disconnect()
            raise OSError("Failed to send to EV3g") from None

    def stop(self):
        """
        Stop the recieving thread
        """
        self.active = False

    def _recv_thread(self):
        """
        Receive messages from the EV3
        """

        print("Starting recv thread", file=sys.stderr)

        while self.active == True:
            try:
                self.connect()
            except:
                raise

            try:
                print("{}: Receiving".format(time.asctime()), file=sys.stderr)
                payload = self.bt_socket.recv(1024)
                mailbox = EV3Mailbox.decode(payload)
                name    = mailbox.name
                if name != None:
                    with self.msgs_lock:
                        if name not in self.messages:
                            self.messages[name] = EV3Messages.Message(name)
                        message = self.messages[name] 

                    message.add(mailbox)
                print("{}: Received: {}".format(time.asctime(), mailbox), file=sys.stderr)
            except bluetooth.btcommon.BluetoothError as e:
                if e.args[0] != "timed out":
                    print("{}: BT Error - Failed to recv - {}".format(time.asctime(), e), file=sys.stderr)
                    self.disconnect()
            except Exception as e:
                print("{}: General Error - Failed to recv - {}".format(time.asctime(), e), file=sys.stderr)
                self.disconnect()

        # Make all messages None so that threads waiting on them know to quit
        for message in self.messages:
            self.messages[message].add(None)

        print("Stopping recv thread", file=sys.stderr)

    def __init__(self, btaddress):
        """
        Constructor
        """
        self.active      = True
        self.bt_address  = btaddress
        self.bt_lock     = threading.Lock()
        self.bt_socket   = None
        self.messages    = {}
        self.msgs_lock   = threading.Lock()
        self.recv_thread = threading.Thread(target=self._recv_thread)  

        self.recv_thread.start()

    def __del__(self):
        """
        Anything needing doing on shutdown
        """

        self.stop()

if __name__ == "__main__":

    active = True

    def _recv_thread(handler, name):
        msg = ""
        while msg != None:
            msg = handler.get(name)
            print("{}: Got message {}".format(name, msg), file=sys.stderr)

        print("Stopping recv thread {}".format(name), file=sys.stderr)

    def _send_thread(handler):
        i = 0
        while active == True:
            if i%10 == 0:
                my_boolean = True if i%20==0 else False
                print("Sending boolean: {}".format(my_boolean),file=sys.stderr)
                handler.send("boolean", my_boolean)
            if i%15 == 0:
                print("Sending number: {}".format(i/2),file=sys.stderr)
                handler.send("number", i/2)
            if i%9 == 0:
                print("Sending string: i={}".format(i),file=sys.stderr)
                handler.send("string", "i={}".format(i))
            time.sleep(1)
            i+=1

        print("Stopping send thread", file=sys.stderr)

    def _quit_thread(handler, name):
        msg = handler.get(name)
        print("{}: Got message {}".format(name, msg), file=sys.stderr)
        handler.stop()

        print("Stopping quit thread", file=sys.stderr)

    print("Starting main")
    msg_handler = EV3Messages('00:16:53:4F:AF:E7')

    number  = threading.Thread(target=_recv_thread,daemon=True,args=(msg_handler,"number",))
    string  = threading.Thread(target=_recv_thread,daemon=True,args=(msg_handler,"string",))
    boolean = threading.Thread(target=_recv_thread,daemon=True,args=(msg_handler,"boolean",))

    number.start()
    string.start()
    boolean.start()

    sender  = threading.Thread(target=_send_thread,daemon=True,args=(msg_handler,))
    sender.start()

    quitter = threading.Thread(target=_quit_thread,daemon=True,args=(msg_handler,"quit",))
    quitter.start()
    quitter.join()

    active = False

    print("Ending main")