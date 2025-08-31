.. _dnp3resolve:

Resolve Link Addresses
======================

Overview
--------

The ``dnp3linkaddr`` tool is designed to **discover the link address of a DNP3 outstation**.
Since many DNP3 deployments require knowledge of the correct remote link address
before initiating communication, this tool provides automated resolution methods
instead of relying on brute force.

The tool currently uses two approaches:

1. **Self-Address Method**
   Send a ``REQUEST_LINK_STATUS`` message using the *Self* address (``0xFFFE``).
   If the outstation supports this optional feature, it will reply with its configured link address.

2. **Passive Listening Method**
   Listen for ``REQUEST_LINK_STATUS`` messages periodically sent by the
   outstation (as required by `DNP3 specification section 9.2.6.5`).
   This allows link address resolution without requiring the *Self* address feature.

.. note::

   Some outstations poll at different intervals — typically between **5 and 60 seconds**.
   You may need to wait for up to a full cycle before receiving a ``REQUEST_LINK_STATUS`` frame.
   Be patient, especially when relying solely on the passive listening method.


Usage
-----

**Resolve using the Self-Address method (default):**

.. code-block:: bash

   dnp3linkaddr 127.0.0.1

This will attempt to send a ``REQUEST_LINK_STATUS`` message using the *Self*
address. If the outstation supports it, the tool will display the resolved link
address.

**Resolve by waiting for a periodic status request:**

.. code-block:: bash

   dnp3linkaddr 127.0.0.1 -no-self -interval 45

This disables the *Self* method and waits up to 45 seconds for the outstation to
send a ``REQUEST_LINK_STATUS`` message.


Practical Notes
---------------

- The **Self-Address method** is not mandatory in DNP3 and may not be implemented by all outstations.
- The **passive listening method** is more reliable but depends on the polling cycle of the outstation.
- Always verify that the **local link address** (``--listen``) matches what the
  outstation expects from the master.

.. hint::

    - Ain't nobody got no time for that - but patience is key here: some
      devices only send ``REQUEST_LINK_STATUS`` messages once every 60 seconds.

