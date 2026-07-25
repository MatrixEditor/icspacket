.. _api_iec104_objects:

Information Object Library
============================

The per-Type-ID information-object catalog: reusable field-level elements
(:mod:`~icspacket.proto.iec104.objects.elements`, e.g. SIQ/DIQ/QDS/VTI),
the structs built from them for each ASDU Type-ID
(:mod:`~icspacket.proto.iec104.objects.information`, e.g. ``M_SP_NA_1``,
``M_ME_NB_1``, ``C_SC_NA_1``), and the registry that maps a
:class:`~icspacket.proto.iec104.const.TypeID` to its struct
(:mod:`~icspacket.proto.iec104.objects.coding`).

.. automodule:: icspacket.proto.iec104.objects.elements
    :members:

.. automodule:: icspacket.proto.iec104.objects.information
    :members:

.. automodule:: icspacket.proto.iec104.objects.coding
    :members:
