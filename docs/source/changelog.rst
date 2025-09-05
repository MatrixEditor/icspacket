.. _changelog:

=========
Changelog
=========

.. _v0.2.3:

v0.2.3 :bdg-info:`beta-develop`
----------------------------------

**Added**

- New :class:`~icspacket.proto.iec61850.goose.GOOSE_Client` and :class:`~icspacket.proto.iec61850.sv.SV_Client`
- New :class:`~icspacket.proto.mms.data.Timestamp` to convert MMS UtcTime values into :class:`datetime`
  objects.
- Example to receive published GOOSE messages: ``gooseobserv.py``