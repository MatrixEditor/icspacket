/*
 * Copyright (c) 2025 MatrixEditor @ github
 * All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#include <py_application.h>

#include <asn_SET_OF.h>

/*global state storing extra Python objects*/
PyCompatTable_t *PyCompatTable = NULL;

int PyCompat_GetFlagsFromArgs(PyObject *kwargs, PyAsnFlags_t *flags) {
    static char *kwlist[] = {"minified", "aligned", "canonical", NULL};

    flags->aligned = 0;
    flags->canonical = 0;
    flags->minified = 0;
    if (kwargs == NULL) {
        return 0;
    }
    return PyArg_ParseTupleAndKeywords(NULL, kwargs, "|$ppp", kwlist,
                                       &flags->minified, &flags->aligned,
                                       &flags->canonical);
}

void PyCompat_Clear(void) {
    Py_CLEAR(PyCompatTable->PyBytesIO_Type);
    Py_CLEAR(PyCompatTable->PyBitArray_Type);
    Py_CLEAR(PyCompatTable->PyIntEnum_Type);
    Py_CLEAR(PyCompatTable->PyEnumMeta_Type);
    Py_CLEAR(PyCompatTable->PyIntFlag_Type);
    Py_CLEAR(PyCompatTable->str__getvalue);
    Py_CLEAR(PyCompatTable->str__write);
    Py_CLEAR(PyCompatTable->str__prepare);
    Py_CLEAR(PyCompatTable->str__oid_sep);
    Py_CLEAR(PyCompatTable->str__endian);
    Py_CLEAR(PyCompatTable->str__little);
    Py_CLEAR(PyCompatTable->str__to_bytes);
    Py_CLEAR(PyCompatTable->str__big);
    PyMem_RawFree(PyCompatTable);
    PyCompatTable = NULL;
}

int PyCompat_Init(void) {
#define _CACHED_STRING(state, attr, str, label) \
    if (((state)->attr = PyUnicode_InternFromString((str))) == NULL) goto label

#define _IMPORT_ATTR(ext_mod, attr, target)                              \
    if ((target = PyObject_GetAttrString((ext_mod), (attr)), !target)) { \
        goto error;                                                      \
    }

    PyObject *nTmpModule = NULL;
    PyCompatTable = PyMem_RawMalloc(sizeof(PyCompatTable_t));
    if (PyCompatTable == NULL) {
        return -1;
    }

    _CACHED_STRING(PyCompatTable, str__getvalue, "getvalue", error);
    _CACHED_STRING(PyCompatTable, str__write, "write", error);
    _CACHED_STRING(PyCompatTable, str__prepare, "__prepare__", error);
    _CACHED_STRING(PyCompatTable, str__oid_sep, ".", error);
    _CACHED_STRING(PyCompatTable, str__endian, "endian", error);
    _CACHED_STRING(PyCompatTable, str__little, "little", error);
    _CACHED_STRING(PyCompatTable, str__big, "big", error);
    _CACHED_STRING(PyCompatTable, str__to_bytes, "tobytes", error);

    nTmpModule = PyImport_ImportModule("io");
    if (!nTmpModule) {
        goto error;
    }
    _IMPORT_ATTR(nTmpModule, "BytesIO", PyCompatTable->PyBytesIO_Type);
    Py_CLEAR(nTmpModule);

    nTmpModule = PyImport_ImportModule("bitarray");
    if (nTmpModule != NULL) {
        _IMPORT_ATTR(nTmpModule, "bitarray", PyCompatTable->PyBitArray_Type);
        Py_CLEAR(nTmpModule);

        nTmpModule = PyImport_ImportModule("bitarray.util");
        if (!nTmpModule) {
            goto error;
        }
        _IMPORT_ATTR(nTmpModule, "ba2int", PyCompatTable->PyBitArray_AsLong);
        _IMPORT_ATTR(nTmpModule, "int2ba", PyCompatTable->PyBitArray_FromLong);
        Py_CLEAR(nTmpModule);
    } else {
        PyCompatTable->PyBitArray_AsLong = NULL;
        PyCompatTable->PyBitArray_FromLong = NULL;
        PyCompatTable->PyBitArray_Type = NULL;
        PyErr_Clear();
    }

    nTmpModule = PyImport_ImportModule("enum");
    if (!nTmpModule) {
        goto error;
    }
    _IMPORT_ATTR(nTmpModule, "IntEnum", PyCompatTable->PyIntEnum_Type);
    _IMPORT_ATTR(nTmpModule, "IntFlag", PyCompatTable->PyIntFlag_Type);
    /*
     * New in version 3.11: Before 3.11 enum used EnumMeta type, which is kept
     * as an alias.
     */
    _IMPORT_ATTR(nTmpModule, "EnumMeta", PyCompatTable->PyEnumMeta_Type);
    Py_CLEAR(nTmpModule);

    return PyCompatTable->PyBytesIO_Type ? 0 : -1;

error:
    return -1;

#undef _CACHED_STRING
#undef _IMPORT_ATTR
}