.. _opcua_example_opcuaclient:

Basic Client
============

The ``opcuaclient`` utility provides a way to discover server endpoints,
browse the address space, and read/write/subscribe to node values on
a remote OPC-UA server.


Usage
-----

.. code-block:: bash

    opcuaclient.py [OPTIONS] <service> ... <host> [-p <port>]

Where ``<host>`` specifies the target server (IP address or hostname, or a
full ``opc.tcp://`` endpoint URL), and ``port`` (default ``4840``) is the
TCP port. See ``opcuaclient.py --help`` for the full set of authentication
and secure-channel options (username/password, certificate-based user
tokens, ``--security-policy``/``--security-mode``).


Discovering Endpoints
----------------------

.. code-block:: bash

    opcuaclient.py endpoints <host>

The ``endpoints`` (aliases ``e``, ``discover``) command performs an
unauthenticated ``GetEndpoints`` call and lists every endpoint the server
advertises, together with its security policy, security mode and supported
user token types.


Browsing the Address Space
----------------------------

.. code-block:: bash

    opcuaclient.py browse <host>
    opcuaclient.py browse "ns=2;i=1" <host>
    opcuaclient.py browse --recursive --values <host>
    opcuaclient.py browse -r --maxdepth 3 <host>

The ``browse`` (alias ``b``) command lists the children of a node (default:
the ``Objects`` folder) as a tree, showing each child's display name, node
class (``Object``, ``Variable``, ``Method``, ...) and NodeId.

.. figure:: _images/opcuaclient-browse.png
    :align: center

    ``opcuaclient.py browse <host>`` -- a single-level listing of the
    ``Objects`` folder on the lab server.

.. option:: -r, --recursive

    Descend into every child node instead of listing only a single level,
    building a full tree of the address space rooted at the given node.

.. option:: --maxdepth DEPTH

    Limit how many levels deep ``--recursive`` descends (default: ``10``).
    Has no effect without ``--recursive``.

.. option:: -V, --values

    Additionally read and display the current value of every ``Variable``
    node encountered.


Reading and Writing Values
-----------------------------

.. code-block:: bash

    opcuaclient.py read "ns=2;i=2" <host>
    opcuaclient.py write "ns=2;i=3" "'FAULT'" <host>

``read``/``write`` operate on a single node's value, addressed by its
NodeId. Use ``endpoints``/``browse`` to discover the actual identifiers
exposed by a given server rather than assuming a particular numbering
scheme -- NodeId syntax (numeric ``ns=2;i=2`` vs. string ``ns=2;s=Name``)
is server-defined.


Subscribing to Data Changes
------------------------------

.. code-block:: bash

    opcuaclient.py subscribe "ns=2;i=2" "ns=2;i=4" --duration 30 <host>

``subscribe`` (alias ``sub``) creates a subscription for one or more nodes
and prints each data-change notification as it arrives, for a configurable
``--duration`` and/or ``--count``.

.. note::

    ``subscribe`` options (``--interval``/``--duration``/``--count``) are
    consumed by argparse's subparser and must appear *before* ``<host>``,
    not after it.
