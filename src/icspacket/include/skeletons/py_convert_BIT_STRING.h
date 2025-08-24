/*
 * Copyright (c) 2025 MatrixEditor @ github
 * All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#ifndef _PyConvert_BIT_STRING_H_
#define _PyConvert_BIT_STRING_H_

#include <asn_internal.h>

#include <py_convert.h>
#include <BIT_STRING.h>

#define PyCompatBITSTRING_index(bit, arrayType) \
    ((bit) / (8 * sizeof(arrayType)))

#define PyCompatBITSTRING_shift(bit, arrayType) \
    ((8 * sizeof(arrayType)) - 1 - ((bit) % (8 * sizeof(arrayType))))

#define PyCompatBITSTRING_maxLength(maxBit, arrayType) \
    (((maxBit) + (8 * sizeof(arrayType)) - 1) / (8 * sizeof(arrayType)))

static inline int PyCompatBITSTRING_New(BIT_STRING_t *dst, size_t size) {
    if (dst == NULL) {
        PyErr_BadInternalCall();
        return -1;
    }

    if (dst->buf != NULL) {
        FREEMEM(dst->buf);
        dst->buf = NULL;
    }

    dst->size = size;
    /* NOTE:
     *   We have to use malloc() instead of PyMem_RawMalloc here as this will
     *   be free'd using ASN1c.
     */
    dst->buf = (uint8_t *)MALLOC(size);
    if (dst->buf == NULL) {
        PyErr_NoMemory();
        return -1;
    }

    memset(dst->buf, 0, size);
    return 0;
}

static inline int PyCompatBITSTRING_SetFlag(BIT_STRING_t *dst, const size_t bit,
                                            PyObject *obj, size_t maxSize) {
    const size_t index = PyCompatBITSTRING_index(bit, uint8_t);
    const size_t shift = PyCompatBITSTRING_shift(bit, uint8_t);
    size_t extra_off = 0;
    if (dst == NULL) {
        PyErr_BadInternalCall();
        return -1;
    }

    if (dst->buf == NULL) {
        if (PyCompatBITSTRING_New(dst, maxSize == 0 ? 1 : maxSize) < 0) {
            return -1;
        }
    }

    if (maxSize > 0 && dst->size > maxSize) {
        /* fix for very small bit strings*/
        extra_off = dst->size - maxSize;
    }

    if (index + extra_off >= dst->size) {
        PyErr_Format(PyExc_IndexError,
                     "Given required index %zu is out of range for size %zu",
                     index + extra_off, dst->size);
        return -1;
    }

    if (obj == NULL || !PyObject_IsTrue(obj)) {
        dst->buf[index + extra_off] &= ~(1 << shift);
    } else {
        dst->buf[index + extra_off] |= 1 << shift;
    }
    return 0;
}

static inline PyObject *PyCompatBITSTRING_GetFlag(BIT_STRING_t *src,
                                                  const size_t bit,
                                                  size_t maxSize) {
    const size_t index = PyCompatBITSTRING_index(bit, uint8_t);
    const size_t shift = PyCompatBITSTRING_shift(bit, uint8_t);

    size_t extra_off = 0;

    if (src == NULL || src->buf == NULL) {
        PyErr_BadInternalCall();
        return NULL;
    }

    if (maxSize > 0 && src->size > maxSize) {
        /* fix for very small bit strings*/
        extra_off = src->size - maxSize;
    }

    if (index + extra_off >= src->size) {
        PyErr_Format(PyExc_IndexError,
                     "Given required index %zu is out of range for size %zu",
                     index, src->size);
        return NULL;
    }
    return (src->buf[index + extra_off] & (1 << shift)) ? Py_True : Py_False;
}

static inline int PyCompatBITSTRING_Resize(BIT_STRING_t *dst, size_t new_size) {
    if (dst == NULL) {
        PyErr_BadInternalCall();
        return -1;
    }

    uint8_t *old_buf = dst->buf;
    size_t old_size = dst->size;
    if (new_size == old_size) {
        return 0;  // early exit
    }

    if (new_size > old_size) {
        // just use realloc()
        dst->bits_unused = 0;
        dst->size = new_size;
        dst->buf = (uint8_t *)REALLOC(dst->buf, new_size);
        if (dst->buf == NULL) {
            PyErr_NoMemory();
            return -1;
        }
        memset(dst->buf + old_size, 0, new_size - old_size);
        return 0;
    }

    // smaller, shrink the bit string
    dst->size = new_size;
    dst->bits_unused = 0;
    dst->buf = (uint8_t *)MALLOC(new_size);
    if (dst->buf == NULL) {
        PyErr_NoMemory();
        return 0;
    }

    if (old_buf != NULL) {
        memcpy(dst->buf, old_buf, new_size);
        FREEMEM(old_buf);
    }
    return 0;
}

#define PyCompatBITSTRING_FromObject(src, dst) \
    PyCompatBytes_ToStringAndSize((src), &(dst)->buf, &(dst)->size)

static PyObject *PyCompatBITSTRING_AsObject(BIT_STRING_t *src) {
    PyObject *nBitArray = NULL;
    PyObject *nBytes = PyCompatBytes_FromStringAndSize(src->buf, src->size);
    if (nBytes == NULL || PyCompatTable->PyBitArray_Type == NULL) {
        return nBytes;
    }

    /* bitarray explicitly installed */
    nBitArray = PyObject_CallOneArg(PyCompatTable->PyBitArray_Type, nBytes);
    Py_DECREF(nBytes);
    return nBitArray;
}

#endif