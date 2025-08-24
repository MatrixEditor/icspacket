/*
 * Copyright (c) 2025 MatrixEditor @ github
 * All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#ifndef _PyConvert_OBJECT_IDENTIFIER_H_
#define _PyConvert_OBJECT_IDENTIFIER_H_

#include <asn_internal.h>

#include <py_convert.h>
#include <OBJECT_IDENTIFIER.h>

static PyObject *PyCompatOID_ArcsAsUTF8String(const asn_oid_arc_t *arcs,
                                              size_t arc_count) {
    PyObject *nResult = NULL, *nValues = NULL, *nTmpValue = NULL;

    if ((nResult = PyList_New(0)) == NULL) {
        goto end;
    }

    for (size_t i = 0; i < arc_count; i++) {
        if ((nTmpValue = PyLong_FromSize_t(arcs[i])) == NULL) {
            goto end;
        }
        Py_SETREF(nTmpValue, PyObject_Str(nTmpValue));
        if (!nTmpValue) {
            goto end;
        }
        if (PyList_Append(nResult, nTmpValue) < 0) {
            goto end;
        }
        Py_CLEAR(nTmpValue);
    }

    nResult = PyUnicode_Join(PyCompatTable->str__oid_sep, nResult);

end:
    Py_XDECREF(nValues);
    Py_XDECREF(nTmpValue);
    return nResult;
}

static PyObject *PyCompatOID_AsUTF8String(const OBJECT_IDENTIFIER_t *oid) {
    PyObject *nResult = NULL;
    asn_oid_arc_t fixed_arcs[10];
    asn_oid_arc_t *arcs = fixed_arcs;
    size_t arc_slots = sizeof(fixed_arcs) / sizeof(fixed_arcs[0]);
    ssize_t arc_count = 0;

    if (!oid->buf || !oid->size) {
        PyErr_SetString(PyExc_ValueError, "Invalid arguments: empty OID");
        return NULL;
    }

    arc_count = OBJECT_IDENTIFIER_get_arcs(oid, arcs, arc_slots);
    if (arc_count > arc_slots) {
        arc_slots = arc_count;
        arcs =
            (asn_oid_arc_t *)PyMem_RawMalloc(sizeof(asn_oid_arc_t) * arc_slots);
        if (!arcs) goto end;
        arc_count = OBJECT_IDENTIFIER_get_arcs(oid, arcs, arc_slots);
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

static int PyCompatOID_FromUnicode(PyObject *unicode,
                                   OBJECT_IDENTIFIER_t *oid) {
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
    result = OBJECT_IDENTIFIER_set_arcs(oid, arcs, arc_count);
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