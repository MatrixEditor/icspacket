.. _cip_example_cipclient:

Operating via CIP / EtherNet-IP
===============================

The ``cipclient`` utility supports nearly every EtherNet/IP/CIP service
supported by :mod:`icspacket.proto.cip`: UDP discovery, unconnected and
connected (Class 3) explicit messaging, Assembly Object I/O, Multiple
Service Packet, and Class 0/1 cyclic I/O connections opened through the
Connection Manager.

Usage
-----

.. code-block:: bash

    cipclient.py [OPTIONS] <service> [args...] <host>

``<host>`` (IP address or hostname) is always the **last** positional
argument, following the service's own arguments. ``-p/--port`` selects the
target TCP port (default ``44818``), and ``--timeout`` bounds
transport-level operations in seconds (default ``10``).


Discovering Targets
---------------------

.. code-block:: bash

    cipclient.py list-identity <host>
    cipclient.py list-services <host>
    cipclient.py list-interfaces <host>

``list-identity`` (alias ``li``), ``list-services`` (alias ``ls``), and
``list-interfaces`` (alias ``lif``) each send one of the three EtherNet/IP
encapsulation-layer discovery commands (``ListIdentity``, ``ListServices``,
``ListInterfaces``) and print every item the target returns as a table.
``list-identity`` is the most broadly useful of the three -- most targets
respond to it, and it doubles as an unauthenticated way to fingerprint a
device (vendor, product name/code, serial number) before addressing it
further:

.. code-block:: text

    $ cipclient.py list-identity <host>
                                                ListIdentity
    +---------+-------+--------+------+---------+----------+------------+----------------------+-------+
    | Address | Port  | Vendor | Type | Product | Revision | Serial     | Name                 | State |
    +=========+=======+========+======+=========+==========+============+======================+=======+
    | 0.0.0.0 | 44818 | 1      | 14   | 54      | 20.11    | 0x006c061a | 1756-L61/B LOGIX5561 | 255   |
    +---------+-------+--------+------+---------+----------+------------+----------------------+-------+

.. note::

    Many targets (including ``cip``/cpppo) report no
    ``ListServices``/``ListInterfaces`` items at all, or only a generic
    "Communications" service entry -- this is normal; not every stack
    populates these optional discovery responses.


Inspecting the Identity Object
---------------------------------

.. code-block:: bash

    cipclient.py identity <host>
    cipclient.py identity -i 1 <host>

``identity`` (alias ``id``) reads and decodes the standard Identity Object
attributes (Vendor ID, Device Type, Product Code, Revision, Status, Serial
Number, Product Name, State) for the given instance (``-i/--instance``,
default ``1``) via :class:`~icspacket.proto.cip.objects.identity.IdentityObject`.
This is the connected/typed equivalent of reading the same attributes
individually with ``get`` below.

.. code-block:: text

    $ cipclient.py -q --timeout 10 -p 44818 identity 127.0.0.1
                Identity Object
    +---------------+----------------------+
    | Attribute     | Value                |
    +===============+======================+
    | Vendor ID     | 1                    |
    | Device Type   | 14                   |
    | Product Code  | 54                   |
    | Revision      | 20.11                |
    | Status        | 0x3160               |
    | Serial Number | 0x006c061a           |
    | Product Name  | 1756-L61/B LOGIX5561 |
    | State         | 255                  |
    +---------------+----------------------+


Reading and Writing Single Attributes
-----------------------------------------

.. code-block:: bash

    cipclient.py get 0x01 1 1 <host>
    cipclient.py get 0x04 1 3 --connected <host>
    cipclient.py set 0x04 1 3 deadbeef <host>

``get`` (aliases ``read``, ``get-attribute-single``) and ``set`` (aliases
``write``, ``set-attribute-single``) send a Get/Set_Attribute_Single request
addressed by ``class_code``, ``instance``, and ``attribute`` (all accept
decimal or ``0x``-prefixed hex). ``set``'s ``value`` is a hexadecimal byte
string (e.g. ``deadbeef``); use the target object's own attribute layout to
determine field order and width. Both accept ``--connected`` to open a
throwaway Class 3 connection to ``(class_code, instance)`` first and send
the request over it instead of unconnected, then close the connection
afterwards.

``get`` additionally decodes the raw response through the same declarative
attribute schema used by ``get-all``/``identity``, when the class is a
registered object and the attribute has a known schema (shown in the
``Decoded`` column; otherwise ``-``):

.. code-block:: text

    $ cipclient.py get 0x01 1 1 <host>
                         Get_Attribute_Single
    +-------+----------+-----------+-----------+--------+---------+
    | Class | Instance | Attribute | Connected | Value  | Decoded |
    +=======+==========+===========+===========+========+=========+
    | 0x1   | 1        | 1         | False     | 0x0100 | 1       |
    +-------+----------+-----------+-----------+--------+---------+


Reading All Attributes of an Object
---------------------------------------

.. code-block:: bash

    cipclient.py get-all 0x01 1 <host>

``get-all`` (aliases ``gall``, ``get-attributes-all``) sends a
Get_Attributes_All request for ``class_code``/``instance``. For objects
with a registered wrapper that models a standard Get_Attributes_All layout
(e.g. Identity, TCP/IP Interface, Ethernet Link), every field is decoded and
labeled; for any other object, as many leading declared attributes as can
be safely decoded are shown, falling back to the raw response bytes:

.. code-block:: text

    $ cipclient.py get-all 0x01 1 <host>
     Get_Attributes_All (class 0x1, instance
                       1)
    +----------------+----------------------+
    | Attribute      | Value                |
    +================+======================+
    | vendor_id      | 1                    |
    | device_type    | 14                   |
    | product_code   | 54                   |
    | revision_major | 20                   |
    | revision_minor | 11                   |
    | status         | 12640                |
    | serial_number  | 7079450              |
    | product_name   | 1756-L61/B LOGIX5561 |
    | state          | 255                  |
    +----------------+----------------------+


Reading and Writing Assembly Data
-------------------------------------

.. code-block:: bash

    cipclient.py assembly-get 100 <host>
    cipclient.py assembly-set 150 aabbccdd <host>

``assembly-get``/``assembly-set`` (aliases ``asm-get``/``asm-set``) read or
write an Assembly Object instance's Data attribute (attribute 3) directly,
without needing a Class 0/1 connection:

.. code-block:: text

    $ cipclient.py assembly-set 150 0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20 <host>
                                      Assembly Data
    +----------+--------------------------------------------------------------------+
    | Instance | Written                                                            |
    +==========+====================================================================+
    | 150      | 0x0102030405060708090a0b0c0d0e0f10111213141516171...               |
    +----------+--------------------------------------------------------------------+


Routing a Request Through Unconnected_Send
-----------------------------------------------

.. code-block:: bash

    cipclient.py unconnected-send 0xe 0x01 1 1 <host>
    cipclient.py unconnected-send 0xe 0x01 1 1 --route-path 01000c00 <host>

``unconnected-send`` (alias ``uc-send``) embeds a Message Router request
(``service``, ``class_code``, ``instance``, optional ``attribute``/``data``)
inside a Connection Manager Unconnected_Send and routes it via
``--route-path``. This is normally used
to reach a device behind a CIP router (e.g. across a backplane or a
ControlLogix chassis) without opening a dedicated connection to it first.


Sending Several Services at Once
-------------------------------------

.. code-block:: bash

    cipclient.py multi 0xe:0x1:1:1 0xe:0x1:1:7 <host>
    cipclient.py multi 0xe:0x4:1:3 --connected <host>

``multi`` (aliases ``multi-service``, ``msp``) bundles multiple embedded
service requests into a single Multiple_Service_Packet, one
``SERVICE:CLASS:INSTANCE[:ATTRIBUTE[:DATA]]`` argument per embedded
request, and prints each embedded reply's status and data:

.. code-block:: text

    $ cipclient.py multi 0xe:0x1:1:1 0xe:0x1:1:7 <host>
                            Multiple_Service_Packet
    +---+---------+--------+----------------------------------------------+
    | # | Service | Status | Response                                     |
    +===+=========+========+==============================================+
    | 0 | 0xe     | 0      | 0x0100                                       |
    | 1 | 0xe     | 0      | 0x14313735362d4c36312f42204c4f47495835353631 |
    +---+---------+--------+----------------------------------------------+

Pass ``--connected`` to send the whole packet over a throwaway Class 3
connection to the Message Router instead of unconnected.


Opening and Closing Class 3 Connections
---------------------------------------------

.. code-block:: bash

    cipclient.py forward-open --path-class 0x04 --path-instance 151 \
        --o2t-conn-point 150 --t2o-conn-point 100 \
        --conn-serial 0x5242 --orig-vendor-id 0x1234 --orig-serial-number 0xdeadbeef \
        --o2t-rpi 100000 --o2t-size 36 --o2t-type 2 \
        --t2o-rpi 100000 --t2o-size 32 --t2o-type 2 <host>
    cipclient.py forward-close --path-class 0x04 --path-instance 151 \
        --conn-serial 0x5242 --orig-vendor-id 0x1234 --orig-serial-number 0xdeadbeef <host>

``forward-open`` (alias ``fo``) and ``forward-close`` (alias ``fc``) send a
raw Forward_Open/Forward_Close request through the Connection Manager and
print every field of the response. Unlike ``get --connected``/``set
--connected`` (which open and close a *throwaway* connection internally),
these expose the full request so a connection can be held open explicitly
and torn down independently, later, with a separate ``forward-close``
invocation.

Every option maps directly onto a Forward_Open request field:

.. option:: --large

    Use Large_Forward_Open (32-bit connection parameters) instead of the
    standard 16-bit Forward_Open.

Connection Identification (``--conn-serial``, ``--orig-vendor-id``,
``--orig-serial-number``, plus ``--o2t-conn-id``/``--t2o-conn-id`` on
``forward-open``) uniquely identifies the connection to the target -- a
subsequent ``forward-close`` **must** repeat the same
serial/vendor-id/originator-serial values used to open it, or the target
rejects the close and keeps the connection open (seen as a
``CONNECTION_FAILURE`` ownership conflict on the *next* open attempt).

The Connection Path (``--path-class``, ``--path-instance``, plus
``--o2t-conn-point``/``--t2o-conn-point`` when connecting to an Assembly
Object) identifies the object instance the connection is opened to --
``--o2t-conn-point``/``--t2o-conn-point`` append a Connection Point segment
for each direction's assembly instance, as used by ``io-connect`` below.

.. code-block:: text

    $ cipclient.py forward-open --path-class 0x04 --path-instance 151 \
        --o2t-conn-point 150 --t2o-conn-point 100 \
        --conn-serial 0x5242 --orig-vendor-id 0x1234 --orig-serial-number 0xdeadbeef \
        --o2t-rpi 100000 --o2t-size 36 --o2t-priority 2 --o2t-type 2 \
        --t2o-rpi 100000 --t2o-size 32 --t2o-priority 2 --t2o-type 2 <host>
                                                        Forward_Open
    +--------------------+--------------------+--------+--------+-------------------+----------+----------+------------+
    | O->T Connection ID | T->O Connection ID | Serial | Vendor | Originator Serial | O->T API | T->O API | Reply Data |
    +====================+====================+========+========+===================+==========+==========+============+
    | 0x4d170013         | 0x00000000         | 0x5242 | 4660   | 0xdeadbeef        | 100000   | 100000   | (empty)    |
    +--------------------+--------------------+--------+--------+-------------------+----------+----------+------------+


Opening a Class 0/1 Cyclic I/O Connection
-----------------------------------------------

.. code-block:: bash

    cipclient.py io-connect 00000000000000000000000000000000 \
        --path-class 0x04 --path-instance 151 \
        --o2t-conn-point 150 --t2o-conn-point 100 \
        --conn-serial 1 --orig-vendor-id 1 --orig-serial-number 1 \
        --o2t-size 36 --t2o-size 32 --o2t-type 2 --t2o-type 2 \
        --cycles 5 <host>

``io-connect`` (alias ``io``) opens a Forward_Open connection exactly like
``forward-open`` above (accepting every option described there, including
``--large``), then additionally opens the UDP Class 0/1 I/O connection it
describes and exchanges cyclic data over it for a fixed number of
send/receive cycles, closing both the I/O connection and the underlying
Forward_Open connection automatically when done.

``data`` (the O->T assembly payload to send each cycle, as hexadecimal
bytes) is the only new positional argument; its length must match
``--o2t-size``. The I/O Exchange group adds:

.. option:: --cycles N

    Number of send/receive cycles to perform (default: ``1``).

.. option:: --interval SEC

    Seconds to sleep between cycles (default: ``1.0``). Keep this short
    together with a small ``--cycles`` count if the connection shares a TCP
    explicit-messaging session that could otherwise idle out before
    ``forward-close`` runs.

.. option:: --io-port PORT

    UDP port to exchange Class 0/1 data on, if different from the standard
    port. Needed when the target's I/O port is remapped, e.g. behind
    NAT/port-forwarding (the lab's ``cip-io`` container maps it to
    ``2223``).

.. option:: --no-header-format

    Omit the 4-byte Run/Idle header from O->T datagrams, for listen-only/
    input-only connections.

.. option:: --no-sequence-format

    Omit the 16-bit connected sequence count prefix from O->T datagrams.
    Some targets rely solely on the CPF-level sequence number and expect
    this header to be absent (e.g. OpENer's sample assemblies, as used by
    the lab's ``cip-io`` container).

.. code-block:: text

    $ cipclient.py io-connect 0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20 \
        --path-class 0x04 --path-instance 151 \
        --o2t-conn-point 150 --t2o-conn-point 100 \
        --conn-serial 0x5346 --orig-vendor-id 0x1234 --orig-serial-number 0xc0ffee03 \
        --o2t-rpi 100000 --o2t-size 36 --o2t-priority 2 --o2t-type 2 \
        --t2o-rpi 100000 --t2o-size 32 --t2o-priority 2 --t2o-type 2 \
        --no-sequence-format --io-port 2223 --cycles 2 --interval 0.2 <host>
                                           Class 0/1 I/O Exchange
    +-------+--------------------------------------------+---------------------------------------------+
    | Cycle | Sent (O->T)                                | Received (T->O)                             |
    +=======+============================================+=============================================+
    | 0     | 0x0102030405060708090a0b0c0d0e0f101112131… | 0x0102030405060708090a0b0c0d0e0f1011121314… |
    | 1     | 0x0102030405060708090a0b0c0d0e0f101112131… | 0x0102030405060708090a0b0c0d0e0f1011121314… |
    +-------+--------------------------------------------+---------------------------------------------+
