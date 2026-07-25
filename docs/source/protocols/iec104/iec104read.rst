.. _iec104_example_read:

Reading Data via Interrogation
================================

The ``iec104read.py`` script connects to an IEC 60870-5-104 outstation and
requests data either via a general/counter interrogation (a bulk "send me
everything" request the outstation answers with a burst of ASDUs) or a
single read of one Information Object Address, dumping every ASDU received
as a tree of decoded information objects.

Target Format
-------------

.. code-block:: bash

    iec104read.py -t <host>[:<port>]

``-t/--target`` is required and specifies the outstation to connect to; the
default port is ``2404`` if omitted. ``-a/--common-address`` sets the
Common Address (CA) of the target station (default: ``1``), and
``--timeout`` bounds how long application-layer operations wait for a
response (default: no timeout).


Requesting a General Interrogation
--------------------------------------

.. code-block:: bash

    iec104read.py -t <host>
    iec104read.py -t <host> -qoi 21

With no ``-r``/``-ci`` option, ``iec104read.py`` issues a general
interrogation (``C_IC_NA_1``) and prints every ASDU the outstation sends in
response, ending with the ``ACTIVATION_TERMINATION`` confirmation that
marks the end of the interrogation sequence.

``-qoi`` selects the Qualifier Of Interrogation (default: ``20``, the whole station; ``21``-
``36`` select one of 16 interrogation groups instead, if the outstation
supports grouped points).

.. code-block:: text

    $ iec104read.py -t <host>
    [I] Connecting to outstation at <host>:2404...
    General interrogation command (C_IC_NA_1=100), COT=ACTIVATION_CON, CA=1
    └── IOA=0
        └── qualifier: 20
    Measured value, scaled value (M_ME_NB_1=11), COT=PERIODIC, CA=1
    └── IOA=110
        ├── value: 449
        └── quality: QDS(iv=False, nt=False, sb=False, bl=False, reserved=0, ov=False)
     ...
    Single point information (M_SP_NA_1=1), COT=INTERROGATED_BY_STATION, CA=1
    ├── IOA=300
    │   └── status: SIQ(iv=False, nt=False, sb=False, bl=False, reserved=0, spi=True)
     ...
    Bitstring of 32 bit (M_BO_NA_1=7), COT=INTERROGATED_BY_STATION, CA=1
    └── IOA=500
        ├── value: 43690
        └── quality: QDS(iv=False, nt=False, sb=False, bl=False, reserved=0, ov=False)
    General interrogation command (C_IC_NA_1=100), COT=ACTIVATION_TERMINATION, CA=1
    └── IOA=0
        └── qualifier: 20

Each information object is decoded through the same registry the protocol
layer uses to encode it (see
:mod:`~icspacket.proto.iec104.objects.coding`), so every field shown
(``value``, ``quality``, ``status``, ...) reflects that Type-ID's actual
element layout -- ``M_SP_NA_1`` above, for example, carries only a single
:class:`~icspacket.proto.iec104.objects.elements.SIQ` status/quality byte
per point, while ``M_ME_NB_1`` carries a 16-bit scaled value plus a
separate :class:`~icspacket.proto.iec104.objects.elements.QDS` quality
byte.

.. note::

    Outstations commonly interleave unsolicited ``COT=PERIODIC`` reports
    (e.g. the ``M_ME_NB_1`` measurement above, incrementing on every
    report) with the interrogation's own ``COT=INTERROGATED_BY_STATION``
    response objects -- both are shown as they arrive, in the order
    received.


Requesting a Counter Interrogation
--------------------------------------

.. code-block:: bash

    iec104read.py -t <host> -ci

``-ci/--counter-interrogation`` issues a counter interrogation
(``C_CI_NA_1``) instead of a general interrogation, requesting the current
value of every integrated totals point (``M_IT_NA_1``) the outstation
maintains.

.. note::

    Not every outstation implements Counter Interrogation -- it is
    optional per IEC 60870-5-104, and demo/reference stacks in particular
    frequently omit it.


Reading a Single Information Object
-----------------------------------------

.. code-block:: bash

    iec104read.py -t <host> -r 110

``-r/--read IOA`` sends a single Read command (``C_RD_NA_1``) for one
Information Object Address instead of performing an interrogation, and
prints the one ASDU returned.

.. note::

    As with Counter Interrogation above, single Read support is optional
    and commonly absent from demo/reference outstations.
