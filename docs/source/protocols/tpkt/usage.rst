.. _proto_tpkt:

Using a TPKT Wrapper
====================

.. code-block:: python

    import socket
    from icspacket.proto.tpkt import tpktsock

    sock = tpktsock(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(...)

    # send and receive are the same
    sock.sendall(b"...")
    data = sock.recv(42)

