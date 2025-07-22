#!/usr/bin/env python3

import sys
import threading
import time

sys.path.append('..')
from ev3messages import EV3Messages

active = True

def _recv_thread(handler, name):
    msg = ""
    while msg != None:
        msg = handler.get(name)
        print("{}: Got message {}".format(name, msg), file=sys.stderr)

    print("Stopping thread {}".format(name), file=sys.stderr)

def _send_thread(handler):
    i = 0
    while active == True:
        try:
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
        except Exception as e:
            print("{}: Failed to send - {}. Sleeping, then trying again".format(time.asctime(),e), file=sys.stderr)
            time.sleep(1)

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
