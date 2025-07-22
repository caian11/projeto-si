# EV3g Mailbox in Python

This repo contains two Python3 classes for handling EV3g format mailbox messages.

## ev3mailbox

This class `from ev3mailbox import EV3Mailbox` performs the encoding and decoding of the binary form of EV3g Mailbox messages:

```python
from ev3mailbox import EV3Mailbox

rod    = EV3Mailbox("rod", "rainbow")
jane   = EV3Mailbox("jane", 3.14159)
freddy = EV3Mailbox("freddy", True)

bt_socket.send(rod)

# As per- the EV3g formats:
# Rod will be a string message
# Jane will be a number
# Freddy will be a boolean
```

This class will work out what format to send the message as based upon its Python data type. Accepted types are bool, int, float, and string. Int will be coerced to a float as there is no explicit int type in EV3g.

## ev3messages

This class `from ev3messages import EV3Messages` is the preferred way to handle EV3g messages. This class, through the use of threads, will handle the asynchronous reception of messages. To use, create an instance of the class, supplying it the BT MAC address of the EV3g side:

```python
from ev3messages import EV3Messages
import threading

def _jane_thread(handler):
    msg = ""
    while msg != None:
        msg = handler.get("Jane")
        print("Jane: Got message {}".format(msg), file=sys.stderr)

# Change to your MAC address
handler = EV3Message('00:16:53:4F:AF:E7')

jane = threading.Thread(target=_jane_thread,daemon=True,args=(handler,))

handler.send("Rod", "rainbow")

handler.stop()
```

The calls to `send(name, value)` are synchronous, i.e. the code will wait until the message has been received by the other side. Any errors will be raised by the send call, so should be wrapped in a `try: ... exception: ...` block. 

The calls to `get(name, timeout=None)` will block until either a message of that name is received from EV3g, or the timeout occurs. If the call times-out, the return value will be None. This call normally returns an EV3Mailbox object.