.. _dnp3_example_dnp3dump:


Dumping Objects
===============

The ``dnp3dump.py`` tool provides a command-line interface for inspecting,
decoding, and printing information about DNP3 protocol data.

The tool accepts input data in several forms (application layer, link layer,
or raw object data) and can print structured information such as a dictionary
of parsed objects.

.. option:: -apdu <HEX|FILE>

   Provide a complete **APDU (Application Protocol Data Unit)** as either
   a hex string or the path to a file containing hex-encoded data.

   Example::

       dnp3dump.py -apdu "c68100001e01000000010000000028030000000100000000"
        [I] Parsed RESPONSE (129) APDU (FIR, FIN), SEQ: 6
        [I] No Internal Indications (IIN)
        Data Objects:
        ├── Object(s): Analog input (Obj: 30, Var: 1) [Range: 0-1]
        │   └── 32-bit with flag [0]:
        │       ├── comm_lost: False
        │       ├── local_forced: False
        │       ├── online: True
        │       ├── over_range: False
        │       ├── reference_err: False
        │       ├── remote_forced: False
        │       ├── reserved0: False
        │       ├── restart: False
        │       └── value: 0
        └── Object(s): Analog output status (Obj: 40, Var: 3) [Range: 0-1]
            └── single-precision, floating-point with flag [0]:
                ├── comm_lost: False
                ├── local_forced: False
                ├── online: True
                ├── over_range: False
                ├── reference_err: False
                ├── remote_forced: False
                ├── reserved0: False
                ├── restart: False
                └── value: 0.0


.. option:: -lpdu <HEX|FILE>

   Provide a complete **LPDU (Link Protocol Data Unit)** as either
   a hex string or the path to a file containing hex-encoded data.

   Example::

       dnp3dump.py -lpdu "056414c4010002004aa2d6c6013c01063c02063c03063c04067aa5"
        [I] Parsed UNCONFIRMED_USER_DATA (4) LPDU (MASTER, PRM) from: 0x0002, to: 0x0001
        [I] Parsed READ (1) APDU (FIR, FIN), SEQ: 6
        [I] No Internal Indications (IIN)
        Data Objects:
        ├── Object(s): Class objects (Obj: 60, Var: 1) (Empty)
        ├── Object(s): Class objects (Obj: 60, Var: 2) (Empty)
        ├── Object(s): Class objects (Obj: 60, Var: 3) (Empty)
        └── Object(s): Class objects (Obj: 60, Var: 4) (Empty)

.. option:: -objects <HEX|FILE>

   Provide raw **object data** (the payload portion of an APDU)
   as either a hex string or the path to a file containing hex-encoded data.

   Example::

       dnp3dump.py -objects "6f0b000000646e70206e61706963617a"
        Data Objects:
        └── Object(s): Octet string event (Obj: 111, Var: 11) [Range: 0-1]
            └── Octet string event [0]:
                00000000:   64 6e 70 20 6e 61 70 69 63 61 7a   dnp.napicaz

Output Options
--------------

.. option:: -dict

   Print the parsed DNP3 objects in a structured **dictionary form**.

   Example::

       dnp3dump.py -apdu "c10232010701ed21da026d01" -dict
        [I] Parsed WRITE (2) APDU (FIR, FIN), SEQ: 1
        [I] No Internal Indications (IIN)
        {50: {1: [DNP3Object(prefix=None, index=0, instance=DNP3ObjectG50V1(timestamp=1567710913005))]}}


