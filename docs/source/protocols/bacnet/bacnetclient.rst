.. _bacnet_example_bacnetclient:

Discovering, Reading and Writing Properties
===========================================

The ``bacnetclient`` utility provides a simple way to discover BACnet/IP
devices and objects, read and write object properties, and
subscribe to Change-of-Value (COV) notifications against a BACnet/IP
network.

Usage
-----

.. code-block:: bash

    bacnetclient.py [OPTIONS] [command [args...]]

By default, ``bacnetclient`` binds to all local interfaces using
BACpypes3's own address resolution. Use ``-a/--address`` to bind a specific
local address (CIDR form, e.g. ``192.168.1.50/24``); this is required when
more than one local interface could otherwise be selected, or when the
default BACnet/IP port (``47808``) is already in use locally.

``--name``/``--instance``/``--vendor-id`` configure the **local** device object
identity (defaults: ``icspacket``/``999``/``999``); ``--foreign``/
``--foreign-ttl`` register the local device as a foreign device with a
remote BBMD, and ``--bbmd`` instead configures the local device to act as a
BBMD itself with the given Broadcast Distribution Table entries.

.. code-block:: bash

    bacnetclient.py
    bacnet> whois <address>
    bacnet> read <address> analog-value,1 present-value
    bacnet> exit


Discovering Devices and Objects
---------------------------------

.. code-block:: bash

    bacnetclient.py whois
    bacnetclient.py whois <address>
    bacnetclient.py whois --low 1000 --high 2000
    bacnetclient.py whohas <address> -o analog-value,1
    bacnetclient.py whohas <address> -n "ANALOG VALUE 1"

``whois`` (alias ``wi``) sends a Who-Is request and reports every device
that answers with an I-Am, either broadcast on the local network (default)
or unicast to a single ``<address>``. ``-l/--low`` and ``-u/--high`` narrow
the query to a device instance range.

.. code-block:: text

    bacnet> whois <address>
    +-------------+------------+----------+-----------------+-----------+
    | Device      | Address    | Max APDU | Segmentation    | Vendor ID |
    +=============+============+==========+=================+===========+
    | device,4000 | <address>  |     1476 | no-segmentation |       260 |
    +-------------+------------+----------+-----------------+-----------+

``whohas`` (alias ``wh``) discovers which device(s) hold a given object,
searching by either ``-o/--object-id`` or ``-n/--name`` (mutually
exclusive).

Reading and Writing Properties
---------------------------------

.. code-block:: bash

    bacnetclient.py read <address> analog-value,1 present-value
    bacnetclient.py write <address> analog-value,1 present-value 72.5 -p 8
    bacnetclient.py write <address> binary-value,1 present-value active -p 8
    bacnetclient.py identify <address>

``read``/``write`` (aliases ``r``/``w``) operate on a single object
property, addressed by object identifier (e.g. ``analog-value,1``) and
property identifier (e.g. ``present-value``). ``-i/--index`` selects an
array element for array-valued properties, and ``-p/--priority`` sets a
commandable priority (1-16) for ``write``.

.. code-block:: text

    bacnet> write <address> analog-value,1 present-value 72.5 -p 8
    [I] Writing 72.5 to analog-value,1.present-value on <address>...
    [I] Write operation succeeded
    bacnet> read <address> analog-value,1 present-value
    [I] Reading analog-value,1.present-value from <address>...
    analog-value,1.present-value = 72.5

``identify`` (alias ``id``) reads a device's identification properties
(``vendor-name``, ``model-name``, ``firmware-revision``, ...), resolving
the device identifier automatically via ``whois`` unless ``-d/--device-id``
is given.


Reading and Writing Multiple Properties at Once
----------------------------------------------------

.. code-block:: bash

    bacnetclient.py rpm <address> -o analog-value,1:present-value,units -o device,4000:vendor-name
    bacnetclient.py wpm <address> -w analog-value,1:present-value:72.5::8 -w binary-value,1:present-value:active::8

``rpm`` issues a single ReadPropertyMultiple request. Repeat
``-o/--object`` for each object to read, in
``OBJECT:PROP[,PROP...]`` form (comma-separated property list).


Browsing a Device's Objects
------------------------------

.. code-block:: bash

    bacnetclient.py objects <address>
    bacnetclient.py objects <address> --values

.. code-block:: text

    bacnet> objects <address> --values
    +-----------------+----------------+-------+
    | Object          | Name           | Value |
    +=================+================+=======+
    | device,4000     | icspacket-...  |       |
    | analog-value,1  | ANALOG VALUE 1 | 72.5  |
    | binary-value,1  | BINARY VALUE 1 | ...   |
    +-----------------+----------------+-------+
    (truncated - a real device typically reports many more objects)


Change-of-Value Subscriptions
---------------------------------

.. code-block:: bash

    bacnetclient.py subscribe <address> analog-value,1
    bacnetclient.py subscribe <address> analog-value,1 --confirmed --duration 30
    bacnetclient.py subscribe <address> analog-value,1 --count 5

``subscribe`` (alias ``sub``) subscribes to Change-of-Value notifications
for a single object and prints each notification as it arrives, until
``--duration`` seconds elapse, ``--count`` notifications have been
received, or Ctrl+C is pressed (whichever comes first; the default is to
run indefinitely).

Pass ``-c/--confirmed`` to request confirmed
notifications instead of the default unconfirmed ones, and
``-l/--lifetime`` to request a specific subscription lifetime in seconds
instead of BACpypes3's default (which most implementations, including
bacnet-stack, treat as an indefinite subscription).

Most servers send an immediate notification reflecting the object's
*current* value as soon as the subscription is accepted, before any
further change actually occurs:

.. code-block:: text

    bacnet> subscribe <address> analog-value,1 --duration 30
    [I] Subscribing to analog-value,1 on <address> (confirmed=False)...
    present-value = 99.9000015258789
    status-flags = <StatusFlags: >
    present-value = 123.44999694824219
    status-flags = <StatusFlags: >

(the second pair of lines above was produced by writing a new value to
``analog-value,1`` from a separate client while the subscription above was
still active).


BBMD Broadcast Distribution and Foreign Device Tables
----------------------------------------------------------

.. code-block:: bash

    bacnetclient.py bdt <address>
    bacnetclient.py fdt <address>

``bdt``/``fdt`` read a remote BBMD's Broadcast Distribution Table /
Foreign Device Table:

.. code-block:: text

    bacnet> bdt <address>
    +------------+
    | Entry      |
    +============+
    | <address>  |
    +------------+
    bacnet> fdt <address>
    [W] FDT is empty


