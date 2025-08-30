
.. _dnp3_example_read:

Reading Objects
===============

The ``dnp3read.py`` script can be used to connect to a DNP3 outstation and request
data objects based on specified classes. The script offers several connection
and request options that allow you to customize your interaction with the
outstation.

Target Format
-------------


The format for specifyinf a remote address to connect to is a little bit
different this time::

    <link_addr>@<host>[:<port>]


The ``<link_addr>`` is the DNP3 link address, and the ``<host>`` is the IP address or hostname of the outstation. The default port is ``20000``.


Requesting Object Groups
------------------------

The ``-G`` option specifies the DNP3 object group number to request. This is an
integer representing the group of data objects you want to retrieve.  For
instance:

.. code-block::
    :caption: Reading all octet strings (group 110)

    $ dnp3read.py -t 1024@127.0.0.1 -G 110
    [I] Connecting to outstation (1024) at 127.0.0.1:20000...
    Data Objects:
    ├── Object(s): Octet string (Obj: 110, Var: 1) [Range: 8-10]
    │   ├── Octet string [0]:
    │   │   00000000:   00                                                .
    │   │
    │   ├── Octet string [1]:
    │   │   00000000:   00                                                .
    │   │
     ...
    │
    └── Object(s): Octet string (Obj: 110, Var: 5) [Range: 7-8]
        └── Octet string [7]:
            00000000:   48 65 6c 6c 6f                                    Hello


Requesting Objects from Data Classes
------------------------------------

To read all objects from specific data classes, just specify the ``-class*``
option:

.. code-block::
    :caption: Reading all class1 object groups

    dnp3read.py -t 1024@127.0.0.1 -class1
    [I] Connecting to outstation (1024) at 127.0.0.1:20000...
    Data Objects:
    ├── Object(s): Analog output event (Obj: 42, Var: 1) [Count: 1]
    │   └── 32-bit without time [0]: (prefix: 7)
    │       ├── comm_lost: False
    │       ├── local_forced: False
    │       ├── online: True
    │       ├── over_range: False
    │       ├── reference_err: False
    │       ├── remote_forced: False
    │       ├── reserved0: False
    │       ├── restart: False
    │       └── value: 1
    └── Object(s): Octet string event (Obj: 111, Var: 5) [Count: 1]
        └── Octet string event [0]: (prefix: 7)
            00000000:   48 65 6c 6c 6f                                    Hello



.. option:: -class0

    Requests **class 0** objects. The response will include objects from the following groups:

    * 1: Binary Input
    * 3: Double-bit Binary Input
    * 10: Binary Output Status
    * 20: Counter
    * 21: Frozen Counter
    * 30: Analog Input
    * 31: Frozen Analog Input
    * 40: Analog Output Status
    * 87: Data Set
    * 101: Binary-Coded Decimal Integer
    * 102: Unsigned Integer—8-bit
    * 110: Octet String
    * 121: Security Statistics

.. option::  -class1

    Requests **class 1** objects. The response may include objects from the following groups:

    * 2: Binary Input Event
    * 4: Double-bit Binary Input Event
    * 11: Binary Output Event
    * 13: Binary Output Command Event
    * 22: Counter Event
    * 23: Frozen Counter Event
    * 32: Analog Input Event
    * 33: Frozen Analog Input Event
    * 42: Analog Output Event
    * 43: Analog Output Command Event
    * 70: File Transfer
    * 88: Data Set Event
    * 111: Octet String Event
    * 113: Virtual Terminal Event
    * 120: Authentication
    * 122: Security Statistics Event

    .. note::
        ``-class2`` and ``-class3`` request the same object groups as ``-class1``

