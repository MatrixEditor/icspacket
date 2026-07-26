.. _modbus_example_modbusclient:

Modbus Interaction (rwq)
========================

The ``modbusclient`` utility provides a simple way to read and write Modbus
data tables (coils, discrete inputs, holding/input registers) and to
discover which unit identifiers and addresses are actually implemented by
a target Modbus/TCP (or Modbus/UDP) server.

Usage
-----

.. code-block:: bash

    modbusclient.py [OPTIONS] <host> [command [args...]]

Where ``<host>`` specifies the target device (IP address or hostname), and
``port`` (default ``502``) is the Modbus TCP/UDP port. Use ``--udp`` to
switch to Modbus/UDP and ``-u/--unit`` to set the default unit/slave
identifier used by ``read``/``write``/``identify``.

.. code-block:: bash

    modbusclient.py <host>
    modbus> write holding 0 1234
    modbus> read holding 0 -c 1
    modbus> exit

.. tip::

    This is also scriptable by piping commands on stdin together with
    ``-i/--interactive``:

    .. code-block:: bash

        printf 'write holding 0 1234\nread holding 0 -c 1\nexit\n' \
            | modbusclient.py <host> -i


Reading and Writing Tables
---------------------------

.. code-block:: bash

    modbusclient.py <host> read holding 0 -c 4
    modbusclient.py <host> write holding 0 1234
    modbusclient.py <host> write coils 0 true false true
    modbusclient.py <host> identify

``read``/``write`` operate on one of the four standard Modbus tables:
``coils``, ``discrete`` (discrete inputs, read-only), ``holding`` and
``input`` (input registers, read-only). ``identify`` retrieves the FC43
device identification objects (vendor, product, revision, ...), if
supported by the target.


Discovering Unit Identifiers
-----------------------------

.. code-block:: bash

    modbusclient.py <host> units
    modbusclient.py <host> units --identify

The ``units`` (alias ``u``) command probes a range of unit/slave identifiers
(default ``1``-``247``, adjustable via ``-s/--start`` and ``-e/--end``) and
reports every id that produces a response. Pass ``-i/--identify`` to additionally attempt an FC43 device
identification read for each responsive unit id.

.. note::

    Many Modbus/TCP gateways and multi-device servers respond to **every**
    probed unit id (accepting requests for registered devices and returning
    an error for unregistered ones), rather than answering only for a single
    "own" id. A device that ignores the unit-id field entirely will behave
    the same way. Treat a large number of responsive ids as inconclusive
    rather than proof of multiple physical devices.


Discovering Coils and Registers
---------------------------------

.. code-block:: bash

    modbusclient.py <host> discover
    modbusclient.py <host> discover holding --end 65536
    modbusclient.py <host> discover coils --block-size 64

The ``discover`` (aliases ``d``, ``scan``) command probes a table (or, by
default, all four tables) over an address range (default ``0``-``999``,
adjustable via ``-s/--start``/ ``-e/--end``) and reports the contiguous
address ranges that respond successfully.

Use ``-b/--block-size`` to cap the number of addresses probed per request,
e.g. to accommodate a server or gateway with stricter limits than the
protocol maximum (125 registers / 2000 coils per request).
