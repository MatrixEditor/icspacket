/*
 * Copyright (c) 2025 MatrixEditor @ github
 * All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#ifndef _PyConvert_RELATIVE_OID_H_
#define _PyConvert_RELATIVE_OID_H_

#include <py_convert_OBJECT_IDENTIFIER.h>
#include <RELATIVE-OID.h>

static PyObject *PyCompatRelativeOID_AsUTF8String(const RELATIVE_OID_t *oid) {
    PyObject *nResult = NULL;
    asn_oid_arc_t fixed_arcs[10];
    asn_oid_arc_t *arcs = fixed_arcs;
    size_t arc_slots = sizeof(fixed_arcs) / sizeof(fixed_arcs[0]);
    ssize_t arc_count = 0;

    if (!oid->buf || !oid->size) {
        PyErr_SetString(PyExc_ValueError,
                        "Invalid arguments: empty RELATIVE-OID");
        return NULL;
    }

    arc_count = RELATIVE_OID_get_arcs(oid, arcs, arc_slots);
    if (arc_count > arc_slots) {
        arc_slots = arc_count;
        arcs =
            (asn_oid_arc_t *)PyMem_RawMalloc(sizeof(asn_oid_arc_t) * arc_slots);
        if (!arcs) goto end;
        arc_count = RELATIVE_OID_get_arcs(oid, arcs, arc_slots);
        if (arc_count < 0) goto error;
        assert(arc_count == arc_slots);
    } else if (arc_count < 0)
        goto error;

    nResult = PyCompatOID_ArcsAsUTF8String(arcs, arc_count);
end:
    if (arcs != fixed_arcs && arcs) PyMem_RawFree(arcs);
    return nResult;

error:
    switch (errno) {
        case EINVAL: {
            PyErr_SetString(PyExc_ValueError, "Invalid arguments: parse error");
            break;
        }
        case ERANGE: {
            PyErr_SetString(
                PyExc_ValueError,
                "One or more arcs have value out of array cell type range.");
            break;
        }
        case ENOMEM: {
            PyErr_NoMemory();
            break;
        }
        default: {
            PyErr_BadInternalCall();
            break;
        }
    };
    goto end;
}

static int PyCompatRelativeOID_FromUnicode(PyObject *unicode,
                                           RELATIVE_OID_t *oid) {
    asn_oid_arc_t fixed_arcs[10];
    asn_oid_arc_t *arcs = fixed_arcs;
    ssize_t arc_slots = sizeof(fixed_arcs) / sizeof(fixed_arcs[0]);
    ssize_t arc_count = 0;
    int result = -1;
    const char *oid_text = NULL;
    Py_ssize_t oid_text_len = 0;

    PyCompatUnicode_Check(unicode, -1);
    oid_text = PyUnicode_AsUTF8AndSize(unicode, &oid_text_len);
    if (oid_text_len < 0) goto end;

    arc_count = OBJECT_IDENTIFIER_parse_arcs(oid_text, oid_text_len, arcs,
                                             arc_slots, NULL);
    if (arc_count > arc_slots) {
        arc_slots = arc_count;
        arcs =
            (asn_oid_arc_t *)PyMem_RawMalloc(sizeof(asn_oid_arc_t) * arc_slots);
        if (!arcs) goto end;
        arc_count = OBJECT_IDENTIFIER_parse_arcs(oid_text, oid_text_len, arcs,
                                                 arc_slots, NULL);
        if (arc_count < 0) goto error;
        assert(arc_count == arc_slots);
    } else if (arc_count < 0) {
        goto error;
    }

    oid->buf = NULL;
    oid->size = 0;
    result = RELATIVE_OID_set_arcs(oid, arcs, arc_count);
    if (result < 0) goto error;
end:
    if (arcs != fixed_arcs && arcs) PyMem_RawFree(arcs);
    return result;

error:
    switch (errno) {
        case EINVAL: {
            PyErr_SetString(PyExc_ValueError, "Invalid arguments: parse error");
            break;
        }
        case ERANGE: {
            PyErr_SetString(PyExc_ValueError,
                            "Invalid arguments: first two arcs do not conform "
                            "to ASN.1 restrictions");
            break;
        }
        case ENOMEM: {
            PyErr_NoMemory();
            break;
        }
        default: {
            PyErr_BadInternalCall();
            break;
        }
    };
    goto end;
}

#endif