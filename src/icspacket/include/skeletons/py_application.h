/*
 * Copyright (c) 2025 MatrixEditor @ github
 * All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#ifndef _PyApplication_H_
#define _PyApplication_H_

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <asn_application.h>

typedef struct {
    PyObject* str__write;
    PyObject* str__getvalue;
    PyObject* str__prepare;
    PyObject* str__oid_sep;
    PyObject* str__endian;
    PyObject* str__little;
    PyObject* str__big;
    PyObject* str__to_bytes;

    PyObject* PyBytesIO_Type;
    PyObject* PyBitArray_Type;
    PyObject* PyIntEnum_Type;
    PyObject* PyEnumMeta_Type;
    PyObject* PyIntFlag_Type;

    PyObject* PyBitArray_AsLong;
    PyObject* PyBitArray_FromLong;
} PyCompatTable_t;

extern PyCompatTable_t* PyCompatTable;

typedef struct {
    int minified;
    int aligned;
    int canonical;
} PyAsnFlags_t;

/* used for conversion (generic template type)*/
typedef struct _pycompat_asnobject_s {
    PyObject_HEAD void* ob_value;
    int s_valid;
    PyObject* ob_parent;
} PyCompatAsnObject_t;

int PyCompat_Init(void);
void PyCompat_Clear(void);

int PyCompat_GetFlagsFromArgs(PyObject* kwargs, PyAsnFlags_t* flags);

static inline PyObject* PyCompat_CheckConstraints(
    const asn_TYPE_descriptor_t* pTypeDescriptor, const void* pValue) {
    char errbuf[1024];
    size_t errbuf_size = sizeof(errbuf);
    size_t used = errbuf_size;

    int res = asn_check_constraints(pTypeDescriptor, pValue, errbuf, &used);
    if (res) {
        if (used > errbuf_size) used = errbuf_size;
        return PyUnicode_FromStringAndSize(errbuf, used);
    }
    Py_RETURN_NONE;
}

static int PyCompat_WriteToStream(const void* pValue, size_t size, void* pIO) {
    PyObject *nBytesIO = (PyObject*)pIO, *nBytes = NULL, *nTmp = NULL;
    int result = 0;
    Py_ssize_t numWritten = 0;

    if (!PyCompatTable->str__write || !PyCompatTable->str__getvalue) {
        PyErr_SetString(PyExc_SystemError,
                        "BytesIO attributes not initialized");
        return -1;
    }

    if (!pValue && size > 0) {
        PyErr_BadArgument();
        return -1;
    }

    if ((nBytes = PyBytes_FromStringAndSize((const char*)pValue, size)) ==
        NULL) {
        return -1;
    }
    nTmp =
        PyObject_CallMethodOneArg(nBytesIO, PyCompatTable->str__write, nBytes);
    if (nTmp != NULL) {
        numWritten = PyLong_AsSsize_t(nTmp);
        Py_XDECREF(nTmp);
        if (numWritten != size) {
            result = -1;
            PyErr_SetString(PyExc_IOError, "Encode: short write to BytesIO");
        }
    } else {
        result = -1;
    }

    Py_XDECREF(nBytes);
    return result;
}

static PyObject* PyCompat_Encode(enum asn_transfer_syntax ats,
                                 const asn_TYPE_descriptor_t* pTypeDescriptor,
                                 const void* pValue) {
    PyObject *nStream = NULL, *nResult = NULL;
    asn_enc_rval_t rval;
    if (!PyCompatTable || !PyCompatTable->PyBytesIO_Type ||
        !PyCallable_Check(PyCompatTable->PyBytesIO_Type)) {
        PyErr_SetString(PyExc_SystemError, "PyBytesIO type not initialized");
        return NULL;
    }

    if ((nStream = PyObject_CallNoArgs(PyCompatTable->PyBytesIO_Type)) ==
        NULL) {
        goto end;
    }
    rval = asn_encode(NULL, ats, pTypeDescriptor, pValue,
                      PyCompat_WriteToStream, nStream);
    if (rval.encoded < 0) {
        switch (errno) {
            case EINVAL: {
                PyErr_SetString(PyExc_TypeError,
                                "Invalid parameters to the function");
                break;
            }
            case ENOENT: {
                PyErr_SetString(
                    PyExc_NotImplementedError,
                    "Transfer syntax is not defined (for this type)");
                break;
            }
            case EBADF: {
                PyErr_SetString(
                    PyExc_TypeError,
                    "Structure has invalid form or content constraint failed");
            }
            /* fall through - exception already set*/
            case EIO:
            default:
                break;
        }
        goto end;
    }

    nResult = PyObject_CallMethodNoArgs(nStream, PyCompatTable->str__getvalue);
end:
    Py_XDECREF(nStream);
    return nResult;
}

/*
 * Struct definition for basic types.
 *
 * Each class will store a reference to the actual value (native
 * representation), an internal state and a reference to the parent
 * object (if any). The flag is used to determine whether the object
 * is in a valid state (e.g. contains valid data). The parent object
 * MAY be NULL and should point to the parent object IF this instance
 * currently stores a reference to a child object.
 *      - ob_value - native representation of the value
 *      - s_valid - internal state
 *      - ob_parent - parent (optional)
 */
#define PyCompat_DEF_STRUCT(name)         \
    typedef struct _##name##_Py {         \
        PyObject_HEAD name##_t* ob_value; \
        int s_valid;                      \
        PyObject* ob_parent;              \
    } PyAsn##name##Object;

#define PyCompat_DEF_ENUM(name)               \
    typedef PyObject PyAsnEnum##name##Object; \
    extern PyObject* PyAsnEnum##name##_Type;

#define PyCompat_DEF_ANON_STRUCT(name, structName) \
    typedef struct _##name##_Py {                  \
        PyObject_HEAD struct structName* ob_value; \
        int s_valid;                               \
        PyObject* ob_parent;                       \
    } PyAsn##name##Object;                         \
    typedef struct structName name##_t;

#define PyCompat_DEF_TYPE(name) extern PyTypeObject PyAsn##name##_Type;

#define PyCompat_QuickCheck(typeDef, self) \
    (asn_check_constraints(&typeDef, self->ob_value, NULL, NULL))

/* Type implementation macros */
#define PY_IMPL_MALLOC(qtypeName) (qtypeName*)PyMem_RawMalloc(sizeof(qtypeName))
#define PY_IMPL_SAFE_MALLOC(target, qtypeName)                    \
    do {                                                          \
        target = PY_IMPL_MALLOC(qtypeName);                       \
        if (target != NULL) memset(target, 0, sizeof(qtypeName)); \
    } while (0)

#define PY_IMPL_MALLOC_CHECK(target, qtypeName, ret) \
    do {                                             \
        target = PY_IMPL_MALLOC(qtypeName);          \
        if ((target == NULL)) {                      \
            PyErr_NoMemory();                        \
            return ret;                              \
        }                                            \
    } while (0)

#define PY_IMPL_FREE(value) PyMem_RawFree((void*)(value))

#define PY_IMPL_XFREE(value)               \
    do {                                   \
        if (value) {                       \
            PyMem_RawFree((void*)(value)); \
        }                                  \
    } while (0)

#define PY_IMPL_XCLEAR(value)    \
    do {                         \
        if ((value)) {           \
            PY_IMPL_FREE(value); \
            value = NULL;        \
        }                        \
    } while (0)

#define PY_IMPL_FROMPY_COMPAT(typeName, obj, dst) \
    PY_IMPL_FROMPY_COMPAT_INTERNAL(typeName, obj, dst, &asn_DEF_##typeName)

#define PY_IMPL_FROMPY_COMPAT_INTERNAL(typeName, obj, dst, type_DEF)     \
    do {                                                                 \
        if (PyObject_TypeCheck((obj), &PyAsn##typeName##_Type)) {        \
            if (asn_copy((type_DEF), (void**)&dst,                       \
                         ((PyCompatAsnObject_t*)(obj))->ob_value) < 0) { \
                PyErr_BadInternalCall();                                 \
                return -1;                                               \
            }                                                            \
            return 0;                                                    \
        }                                                                \
    } while (0)

#define PY_IMPL_GENERIC_NEW(name, type_DEF)                                 \
    static PyObject* PyAsn##name##__new(PyTypeObject* type, PyObject* args, \
                                        PyObject* kwds) {                   \
        PyAsn##name##Object* self =                                         \
            (PyAsn##name##Object*)type->tp_alloc(type, 0);                  \
        if (self) {                                                         \
            self->ob_value = NULL;                                          \
            self->s_valid = 0;                                              \
            self->ob_parent = NULL;                                         \
            PY_IMPL_SAFE_MALLOC(self->ob_value, name##_t);                  \
            if (!self->ob_value) {                                          \
                Py_CLEAR(self);                                             \
            } else {                                                        \
                if ((type_DEF) != NULL) {                                   \
                    if (ASN_STRUCT_INIT((type_DEF), self->ob_value) < 0) {  \
                        Py_CLEAR(self);                                     \
                        PyErr_SetFromErrno(PyExc_ValueError);               \
                        return NULL;                                        \
                    }                                                       \
                }                                                           \
            }                                                               \
        }                                                                   \
        return (PyObject*)self;                                             \
    }

#define PY_IMPL_GENERIC_DEALLOC(name) PY_IMPL_DEALLOC(name, asn_DEF_##name)

#define PY_IMPL_DEALLOC(name, type_DEF)                                   \
    static void PyAsn##name##__dealloc(PyAsn##name##Object* self) {       \
        ASN_DEBUG("Freeing " #name " at %p (parent: %p)", self->ob_value, \
                  self->ob_parent);                                       \
        if (self->ob_parent != NULL) {                                    \
            Py_DECREF(self->ob_parent);                                   \
            self->ob_value = NULL;                                        \
        } else {                                                          \
            if (self->ob_value != NULL && self->s_valid) {                \
                ASN_STRUCT_RESET((type_DEF), self->ob_value);             \
                PyMem_RawFree(self->ob_value);                            \
            }                                                             \
            self->ob_value = NULL;                                        \
            self->ob_parent = NULL;                                       \
        }                                                                 \
        Py_TYPE(self)->tp_free((PyObject*)self);                          \
    }

#define PY_IMPL_REPR(name) PY_IMPL_GENERIC_REPR(name, name)

#define PY_IMPL_GENERIC_REPR(name, targetReprName)                    \
    static PyObject* PyAsn##name##__repr(PyAsn##name##Object* self) { \
        return PyUnicode_FromString(("<" #targetReprName ">"));       \
    }

#define PY_IMPL_GENERIC_STR(name)                                              \
    static PyObject* PyAsn##name##__str(PyAsn##name##Object* self) {           \
        PyObject *nValue = NULL, *nResult = NULL;                              \
        if (!self->s_valid) {                                                  \
            return PyUnicode_FromString(("<" #name ">"));                      \
        }                                                                      \
        if ((nValue = PyAsn##name##_ToPython(self->ob_value, NULL)) == NULL) { \
            return NULL;                                                       \
        }                                                                      \
        nResult = PyObject_Str(nValue);                                        \
        Py_DECREF(nValue);                                                     \
        return nResult;                                                        \
    }

#define PY_IMPL_GENERIC_CHECK_CONSTRAINTS(name) \
    PY_IMPL_CHECK_CONSTRAINTS(name, (&asn_DEF_##name))

#define PY_IMPL_CHECK_CONSTRAINTS(name, type_DEF)                         \
    static PyObject* PyAsn##name##__check_constraints(                    \
        PyAsn##name##Object* self, PyObject* Py_UNUSED(ignored)) {        \
        PyObject* nResult = NULL;                                         \
        if (!self | !self->ob_value) {                                    \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        nResult = PyCompat_CheckConstraints((type_DEF),                   \
                                            (const void*)self->ob_value); \
        if (!nResult) {                                                   \
            return NULL;                                                  \
        }                                                                 \
        if (Py_IsNone(nResult)) {                                         \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        PyErr_SetObject(PyExc_ValueError, nResult);                       \
        Py_DECREF(nResult);                                               \
        return NULL;                                                      \
    }

#define PY_IMPL_GENERIC_IS_VALID(name)                                    \
    static PyObject* PyAsn##name##__is_valid(PyAsn##name##Object* self) { \
        if (!self->s_valid) Py_RETURN_FALSE;                              \
        if (!PyAsn##name##__check_constraints(self, NULL)) {              \
            PyErr_Clear();                                                \
            Py_RETURN_FALSE;                                              \
        }                                                                 \
        Py_RETURN_TRUE;                                                   \
    }

/* Encode */
#define PY_IMPL_GENERIC_ENCODE(name) PY_IMPL_ENCODE(name, &asn_DEF_##name)

#define PY_IMPL_ENCODE(name, type_DEF)                                     \
    static PyObject* PyAsn##name##__encode(PyAsn##name##Object* self,      \
                                           enum asn_transfer_syntax ats) { \
        if (!self->s_valid) {                                              \
            PyErr_SetString(PyExc_ValueError,                              \
                            "ASN.1 object does not contain valid data");   \
            return NULL;                                                   \
        }                                                                  \
        if (PyAsn##name##__check_constraints(self, NULL) == NULL) {        \
            return NULL;                                                   \
        }                                                                  \
        return PyCompat_Encode((ats), (type_DEF), self->ob_value);         \
    }

#define PY_IMPL_ENCODE_XER(typeName)                                       \
    static PyObject* PyAsn##typeName##__xer_encode(                        \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                                \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {               \
            return NULL;                                                   \
        }                                                                  \
        return PyAsn##typeName##__encode(                                  \
            self, flags.canonical ? ATS_CANONICAL_XER : ATS_BASIC_XER);    \
    }

#define PY_IMPL_ENCODE_JER(typeName)                                       \
    static PyObject* PyAsn##typeName##__jer_encode(                        \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                                \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {               \
            return NULL;                                                   \
        }                                                                  \
        return PyAsn##typeName##__encode(                                  \
            self, flags.minified ? ATS_JER_MINIFIED : ATS_JER);            \
    }

#define PY_IMPL_ENCODE_PER(typeName)                                       \
    static PyObject* PyAsn##typeName##__per_encode(                        \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                                \
        e_asn_transfer_syntax_t syntax = ATS_UNALIGNED_BASIC_PER;          \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {               \
            return NULL;                                                   \
        }                                                                  \
        if (flags.aligned) {                                               \
            syntax = flags.canonical ? ATS_ALIGNED_CANONICAL_PER           \
                                     : ATS_ALIGNED_BASIC_PER;              \
        } else {                                                           \
            syntax = flags.canonical ? ATS_UNALIGNED_CANONICAL_PER         \
                                     : ATS_UNALIGNED_BASIC_PER;            \
        }                                                                  \
        return PyAsn##typeName##__encode(self, syntax);                    \
    }

#define PY_IMPL_ENCODE_OER(typeName)                                       \
    static PyObject* PyAsn##typeName##__oer_encode(                        \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                                \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {               \
            return NULL;                                                   \
        }                                                                  \
        return PyAsn##typeName##__encode(                                  \
            self, flags.canonical ? ATS_CANONICAL_OER : ATS_BASIC_OER);    \
    }

#define PY_IMPL_ENCODE_SPECIFIC(typeName, atsName, atsValue) \
    static PyObject* PyAsn##typeName##__##atsName##_encode(  \
        PyAsn##typeName##Object* self) {                     \
        return PyAsn##typeName##__encode(self, atsValue);    \
    }

/* Decode */
#define PY_IMPL_GENERIC_DECODE(name) PY_IMPL_DECODE(name, &asn_DEF_##name)

#define PY_IMPL_DECODE(name, type_DEF)                                         \
    static PyObject* PyAsn##name##__decode(PyObject* args,                     \
                                           enum asn_transfer_syntax ats) {     \
        Py_buffer view;                                                        \
        PyAsn##name##Object* self = NULL;                                      \
        asn_dec_rval_t rval;                                                   \
        if (PyArg_ParseTuple(args, "y*", &view) < 0) return NULL;              \
        if (view.len > 0 && !view.buf) {                                       \
            PyBuffer_Release(&view);                                           \
            PyErr_SetString(PyExc_ValueError,                                  \
                            "NULL buffer with positive length");               \
            Py_CLEAR(self);                                                    \
            return NULL;                                                       \
        }                                                                      \
        self = (PyAsn##name##Object*)PyObject_CallNoArgs(                      \
            (PyObject*)&PyAsn##name##_Type);                                   \
        if (self == NULL) {                                                    \
            goto end;                                                          \
        }                                                                      \
        rval = asn_decode(NULL, ats, (type_DEF), (void**)&self->ob_value,      \
                          (const void*)view.buf, view.len);                    \
        self->s_valid = rval.code == RC_OK;                                    \
        switch (rval.code) {                                                   \
            case RC_WMORE:                                                     \
                PyErr_SetString(PyExc_ValueError, "Failed to decode " #name    \
                                                  " from data! "               \
                                                  "(need more data)");         \
                Py_CLEAR(self);                                                \
                break;                                                         \
            case RC_OK:                                                        \
                break;                                                         \
            default:                                                           \
                PyErr_Format(                                                  \
                    PyExc_ValueError,                                          \
                    ("Failed to decode " #name " at byte %zu: Invalid data!"), \
                    rval.consumed);                                            \
                Py_CLEAR(self);                                                \
                break;                                                         \
        };                                                                     \
        if (self != NULL && !PyAsn##name##__check_constraints(self, NULL)) {   \
            Py_CLEAR(self);                                                    \
        }                                                                      \
    end:                                                                       \
        PyBuffer_Release(&view);                                               \
        return (PyObject*)self;                                                \
    }

#define PY_IMPL_DECODE_PER(typeName)                                   \
    static PyObject* PyAsn##typeName##__per_decode(                    \
        PyObject* Py_UNUSED(type), PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                            \
        e_asn_transfer_syntax_t syntax = ATS_UNALIGNED_BASIC_PER;      \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {           \
            return NULL;                                               \
        }                                                              \
        if (flags.aligned) {                                           \
            syntax = flags.canonical ? ATS_ALIGNED_CANONICAL_PER       \
                                     : ATS_ALIGNED_BASIC_PER;          \
        } else {                                                       \
            syntax = flags.canonical ? ATS_UNALIGNED_CANONICAL_PER     \
                                     : ATS_UNALIGNED_BASIC_PER;        \
        }                                                              \
        return PyAsn##typeName##__decode(args, syntax);                \
    }

#define PY_IMPL_DECODE_OER(typeName)                                    \
    static PyObject* PyAsn##typeName##__oer_decode(                     \
        PyObject* Py_UNUSED(type), PyObject* args, PyObject* kwargs) {  \
        PyAsnFlags_t flags;                                             \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {            \
            return NULL;                                                \
        }                                                               \
        return PyAsn##typeName##__decode(                               \
            args, flags.canonical ? ATS_CANONICAL_OER : ATS_BASIC_OER); \
    }

#define PY_IMPL_DECODE_XER(typeName)                                    \
    static PyObject* PyAsn##typeName##__xer_decode(                     \
        PyObject* Py_UNUSED(type), PyObject* args, PyObject* kwargs) {  \
        PyAsnFlags_t flags;                                             \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {            \
            return NULL;                                                \
        }                                                               \
        return PyAsn##typeName##__decode(                               \
            args, flags.canonical ? ATS_CANONICAL_XER : ATS_BASIC_XER); \
    }

#define PY_IMPL_DECODE_JER(typeName)                                   \
    static PyObject* PyAsn##typeName##__jer_decode(                    \
        PyObject* Py_UNUSED(type), PyObject* args, PyObject* kwargs) { \
        PyAsnFlags_t flags;                                            \
        if (PyCompat_GetFlagsFromArgs(kwargs, &flags) < 0) {           \
            return NULL;                                               \
        }                                                              \
        return PyAsn##typeName##__decode(                              \
            args, flags.minified ? ATS_JER_MINIFIED : ATS_JER);        \
    }

#define PY_IMPL_DECODE_SPECIFIC(typeName, atsName, atsValue) \
    static PyObject* PyAsn##typeName##__##atsName##_decode(  \
        PyObject* Py_UNUSED(type), PyObject* args) {         \
        return PyAsn##typeName##__decode(args, atsValue);    \
    }

#define PY_IMPL_DECODE_BER(typeName) \
    PY_IMPL_DECODE_SPECIFIC(typeName, ber, ATS_BER)

#define PY_IMPL_DECODE_DER(typeName) \
    PY_IMPL_DECODE_SPECIFIC(typeName, der, ATS_BER)

// REVISIT: CER is the same as BER here
#define PY_IMPL_DECODE_CER(typeName) \
    PY_IMPL_DECODE_SPECIFIC(typeName, cer, ATS_BER)

#define PY_IMPL_MEMBER_GETSET(typeName, memberName, memberType, attr) \
    static PyObject* PyAsn##typeName##__get_##memberName(             \
        PyAsn##typeName##Object* self) {                              \
        if (!self->s_valid) {                                         \
            return Py_None;                                           \
        }                                                             \
        return PyAsn##memberType##_ToPython((attr), (PyObject*)self); \
    }                                                                 \
    static int PyAsn##typeName##__set_##memberName(                   \
        PyAsn##typeName##Object* self, PyObject* value) {             \
        int res = PyAsn##memberType##_FromPython(value, (attr));      \
        self->s_valid = res == 0;                                     \
        return res;                                                   \
    }

#define PY_IMPL_METHODDEF_ITEM(typeName, name, flags) \
    {#name, (PyCFunction)PyAsn##typeName##__##name, (flags), NULL}

#define PY_IMPL_GETSET_ITEM(typeName, itemName) \
    PY_IMPL_GETSET_ITEM_INTERNAL(typeName, itemName, itemName)

#define PY_IMPL_GETSET_ITEM_INTERNAL(typeName, pyItemName, attrName) \
    {#pyItemName, (getter)PyAsn##typeName##__get_##attrName,         \
     (setter)PyAsn##typeName##__set_##attrName, NULL, NULL}

#define PY_IMPL_GENERIC_INIT(typeName)                                      \
    static int PyAsn##typeName##__init(PyAsn##typeName##Object* self,       \
                                       PyObject* args, PyObject* kwds) {    \
        static char* kwlist[] = {"value", NULL};                            \
        PyObject* value = NULL;                                             \
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &value)) \
            return -1;                                                      \
        if (value) {                                                        \
            if (PyAsn##typeName##_FromPython(value, self->ob_value) < 0)    \
                return -1;                                                  \
            self->s_valid = 1;                                              \
        }                                                                   \
        return 0;                                                           \
    }

#define PY_IMPL_MOD_ADD_OBJECT(mod, typeName)                         \
    Py_INCREF(&PyAsn##typeName##_Type);                               \
    if (PyModule_AddObject(mod, #typeName,                            \
                           (PyObject*)&PyAsn##typeName##_Type) < 0) { \
        return -1;                                                    \
    }

#define PY_IMPL_NEW_ENUM(typeName, target, ret, ...) \
    PY_IMPL_NEW_ENUM_TYPE(PyIntEnum_Type, typeName, target, ret, __VA_ARGS__)

#define PY_IMPL_NEW_ENUM_TYPE(enumType, typeName, target, ret, ...)          \
    do {                                                                     \
        PyObject *nName = NULL, *nBases = NULL, *nNamespace = NULL,          \
                 *nTmpName = NULL, *nTmpValue = NULL;                        \
        int result = 0;                                                      \
        if ((nName = PyUnicode_FromString((#typeName))) == NULL) {           \
            return (ret);                                                    \
        }                                                                    \
        nBases = Py_BuildValue("(O)", (PyObject*)PyCompatTable->enumType);   \
        if (nBases) {                                                        \
            nNamespace = PyObject_CallMethodObjArgs(                         \
                PyCompatTable->PyEnumMeta_Type, PyCompatTable->str__prepare, \
                nName, nBases, NULL);                                        \
            if (nNamespace) {                                                \
                __VA_ARGS__;                                                 \
                if (result >= 0) {                                           \
                    target = PyObject_CallFunctionObjArgs(                   \
                        PyCompatTable->PyEnumMeta_Type, nName, nBases,       \
                        nNamespace, NULL);                                   \
                }                                                            \
            }                                                                \
        }                                                                    \
        Py_XDECREF(nName);                                                   \
        Py_XDECREF(nBases);                                                  \
        Py_XDECREF(nNamespace);                                              \
        Py_XDECREF(nTmpName);                                                \
        Py_XDECREF(nTmpValue);                                               \
        if (!target) {                                                       \
            return (ret);                                                    \
        }                                                                    \
    } while (0)

#define PY_IMPL_ENUM_VALUE(name, value, isSigned)                          \
    do {                                                                   \
        if (result >= 0) {                                                 \
            result = -1;                                                   \
            if ((nTmpName = PyUnicode_FromString(#name)) != NULL) {        \
                if ((isSigned)) {                                          \
                    nTmpValue = PyLong_FromSsize_t((Py_ssize_t)value);     \
                } else {                                                   \
                    nTmpValue = PyLong_FromSize_t((size_t)value);          \
                }                                                          \
                if (nTmpValue) {                                           \
                    result =                                               \
                        PyObject_SetItem(nNamespace, nTmpName, nTmpValue); \
                }                                                          \
            }                                                              \
        }                                                                  \
        Py_CLEAR(nTmpName);                                                \
        Py_CLEAR(nTmpValue);                                               \
    } while (0)

#define PY_IMPL_FLAG_VALUE(name, bitPos)                                      \
    do {                                                                      \
        PyObject *nTmpShift = NULL, *nTmpBitValue = NULL;                     \
        if (result >= 0) {                                                    \
            result = -1;                                                      \
            if ((nTmpName = PyUnicode_FromString(#name)) != NULL) {           \
                nTmpValue = PyLong_FromSize_t((size_t)1);                     \
                if (nTmpValue != NULL) {                                      \
                    nTmpShift = PyLong_FromSize_t(                            \
                        (size_t)((bitPos > 0) ? bitPos - 1 : 0));             \
                    if (nTmpShift != NULL) {                                  \
                        nTmpBitValue = PyNumber_Lshift(nTmpValue, nTmpShift); \
                        if (nTmpBitValue != NULL) {                           \
                            result = PyObject_SetItem(nNamespace, nTmpName,   \
                                                      nTmpBitValue);          \
                        }                                                     \
                    }                                                         \
                }                                                             \
            }                                                                 \
        }                                                                     \
        Py_CLEAR(nTmpName);                                                   \
        Py_CLEAR(nTmpValue);                                                  \
        Py_CLEAR(nTmpShift);                                                  \
        Py_CLEAR(nTmpBitValue);                                               \
    } while (0)

#define PY_IMPL_ASSIGN_ENUM(typeName) \
    PY_IMPL_ASSIGN_ENUM_DIRECT(typeName, typeName, VALUES)

#define PY_IMPL_ASSIGN_ENUM_DIRECT(typeName, enumTypeName, attrName)           \
    if (PyDict_SetItemString((PyObject*)PyAsn##typeName##_Type.tp_dict,        \
                             #attrName, PyAsnEnum##enumTypeName##_Type) < 0) { \
        return -1;                                                             \
    }

#define PY_IMPL_CHOICE_ATTR_FROMPY(typeName, enumTypeName, safeName, attrName, \
                                   ...)                                        \
    static inline int PyAsn##typeName##__##safeName##_FromPython(              \
        PyObject* value, typeName##_t* dst) {                                  \
        if (value == NULL) {                                                   \
            dst->present = enumTypeName##_PR_NOTHING;                          \
            return 0;                                                          \
        }                                                                      \
        if ((__VA_ARGS__) < 0) return -1;                                      \
        dst->present = enumTypeName##_PR_##attrName;                           \
        return 0;                                                              \
    }

#define PY_IMPL_CHOICE_SETATTR(typeName, enumTypeName, safeName, attrName)     \
    PY_IMPL_CHOICE_GENERIC_SETATTR(typeName, enumTypeName, safeName, attrName, \
                                   asn_DEF_##typeName)

#define PY_IMPL_CHOICE_GENERIC_SETATTR(typeName, enumTypeName, safeName, \
                                       attrName, type_DEF)               \
    static int PyAsn##typeName##__set_##safeName(                        \
        PyAsn##typeName##Object* self, PyObject* value,                  \
        void* Py_UNUSED(arg)) {                                          \
        int result = 0;                                                  \
        if (!self || !self->ob_value) {                                  \
            PyErr_SetString(PyExc_RuntimeError, "Invalid ASN.1 object"); \
            return -1;                                                   \
        }                                                                \
        ASN_STRUCT_RESET((type_DEF), self->ob_value);                    \
        self->ob_value->present = enumTypeName##_PR_NOTHING;             \
        if (value != NULL) {                                             \
            result = PyAsn##typeName##__##safeName##_FromPython(         \
                value, self->ob_value);                                  \
        } else {                                                         \
            self->s_valid = 0;                                           \
            return 0;                                                    \
        }                                                                \
        self->s_valid = result != -1;                                    \
        if (result < 0) {                                                \
            return -1;                                                   \
        }                                                                \
        self->ob_value->present = enumTypeName##_PR_##attrName;          \
        return 0;                                                        \
    }

#define PY_IMPL_CHOICE_ATTR_TOPY(typeName, attrName, topyfunc)        \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython( \
        const typeName##_t* src, PyObject* parent) {                  \
        return (topyfunc);                                            \
    }

#define PY_IMPL_CHOICE_GETATTR(typeName, enumTypeName, safeName, attrName) \
    static PyObject* PyAsn##typeName##__get_##safeName(                    \
        PyAsn##typeName##Object* self, void* Py_UNUSED(arg)) {             \
        if (self->ob_value->present != enumTypeName##_PR_##attrName)       \
            Py_RETURN_NONE;                                                \
        return PyAsn##typeName##__##safeName##_ToPython(self->ob_value,    \
                                                        (PyObject*)self);  \
    }

#define PY_IMPL_INIT_KWONLY(typeName, args, kwargs)                       \
    if ((args) && (PyTuple_Size(args) > 0)) {                             \
        PyErr_SetString(PyExc_TypeError,                                  \
                        (#typeName ": unexpected positional arguments")); \
        return -1;                                                        \
    }                                                                     \
    if (!kwargs || !PyDict_Size(kwargs)) {                                \
        return 0;                                                         \
    }

#define PY_IMPL_CHOICE_FROMPY(typeName, type_DEF, ...)                     \
    int PyAsn##typeName##_FromPython(PyObject* pObj, typeName##_t* pDst) { \
        PyObject* tmp = NULL;                                              \
        int result = 0;                                                    \
        void* src = NULL;                                                  \
        if (PyObject_TypeCheck((pObj), &PyAsn##typeName##_Type)) {         \
            src = ((PyCompatAsnObject_t*)(pObj))->ob_value;                \
            if (src != NULL && ((typeName##_t*)src)->present != 0) {       \
                if (asn_copy((type_DEF), (void**)&pDst, src) < 0) {        \
                    PyErr_BadInternalCall();                               \
                    return -1;                                             \
                }                                                          \
            }                                                              \
            return 0;                                                      \
        }                                                                  \
        __VA_ARGS__;                                                       \
        Py_XDECREF(tmp);                                                   \
        return result;                                                     \
    }

#define PY_IMPL_CHOICE_INIT_ATTR(typeName, enumTypeName, pyAttrName, safeName, \
                                 attrName)                                     \
    if (result == 0) {                                                         \
        PyCompat_GenericGetAttr(pObj, pyAttrName, tmp);                        \
        if (tmp != NULL && tmp != Py_None) {                                   \
            if (PyAsn##typeName##__##safeName##_FromPython(tmp, pDst) < 0) {   \
                ASN_DEBUG("Failed to set " #attrName " attribute");            \
                result = -1;                                                   \
            } else {                                                           \
                pDst->present = enumTypeName##_PR_##attrName;                  \
                Py_CLEAR(tmp);                                                 \
                return 0;                                                      \
            }                                                                  \
        } else {                                                               \
            PyErr_Clear();                                                     \
        }                                                                      \
        Py_XDECREF(tmp);                                                       \
    }

#define PY_IMPL_CHOICE_INIT(typeName) \
    PY_IMPL_CHOICE_INIT_GENERIC(typeName, typeName)

#define PY_IMPL_CHOICE_INIT_GENERIC(typeName, enumTypeName)                   \
    static int PyAsn##typeName##__init(PyAsn##typeName##Object* self,         \
                                       PyObject* args, PyObject* kwargs) {    \
        PY_IMPL_INIT_KWONLY(typeName, args, kwargs);                          \
        if (PyAsn##typeName##_FromPython(kwargs, self->ob_value) < 0)         \
            return -1;                                                        \
        self->s_valid = self->ob_value->present != enumTypeName##_PR_NOTHING; \
        return 0;                                                             \
    }

#define PY_IMPL_CHOICE_TOPY(typeName)                                         \
    PyObject* PyAsn##typeName##_ToPython(typeName##_t* src,                   \
                                         PyObject* parent) {                  \
        PyAsn##typeName##Object* self = PyCompatCHOICE_New(typeName);         \
        if (parent == NULL) {                                                 \
            if (asn_copy(&asn_DEF_##typeName, (void**)&self->ob_value, src) < \
                0) {                                                          \
                Py_DECREF(self);                                              \
                return NULL;                                                  \
            }                                                                 \
        } else {                                                              \
            PyMem_RawFree(self->ob_value);                                    \
            self->ob_value = (typeName##_t*)src;                              \
            self->ob_parent = Py_NewRef(parent);                              \
        }                                                                     \
        self->s_valid = self->ob_value->present != typeName##_PR_NOTHING;     \
        return (PyObject*)self;                                               \
    }

#define PY_IMPL_CHOICE_PRESENT_ATTR(typeName)                             \
    static PyObject* PyAsn##typeName##__get_present(                      \
        PyAsn##typeName##Object* self, void* Py_UNUSED(arg)) {            \
        return PyCompatEnum_AsObject(PyAsnEnum##typeName##_PRESENT_Type,  \
                                     (void*)&self->ob_value->present, 0); \
    }

#define PY_IMPL_SEQ_ATTR_FREE(typeName, attrName, ...)      \
    static inline int PyAsn##typeName##__##attrName##_Free( \
        typeName##_t* dst) {                                \
        if (dst != NULL && dst->attrName != NULL) {         \
            __VA_ARGS__;                                    \
        }                                                   \
        return 0;                                           \
    }

#define PY_IMPL_SEQ_ATTR_GENERIC_FREE(typeName, attrName) \
    PY_IMPL_SEQ_ATTR_FREE(typeName, attrName, PyMem_RawFree(dst->attrName))

#define PY_IMPL_SEQ_ATTR_GENERIC_NEW(typeName, attrName, attrType)          \
    static inline attrType* PyAsn##typeName##__##attrName##_New(void) {     \
        static const size_t _##typeName##__##attrName##_size =              \
            sizeof(attrType);                                               \
        void* newValue = PyMem_RawMalloc(_##typeName##__##attrName##_size); \
        memset(newValue, 0, _##typeName##__##attrName##_size);              \
        return (attrType*)newValue;                                         \
    }

#define PY_IMPL_SEQ_ATTR_INDIRECT_FROMPY(typeName, attrName, ...) \
    static inline int PyAsn##typeName##__##attrName##_FromPython( \
        PyObject* value, typeName##_t* dst) {                     \
        void* target = NULL;                                      \
        if (PyAsn##typeName##__##attrName##_Free(dst) < 0) {      \
            return -1;                                            \
        }                                                         \
        dst->attrName = PyAsn##typeName##__##attrName##_New();    \
        if (!dst->attrName) {                                     \
            return -1;                                            \
        }                                                         \
        target = dst->attrName;                                   \
        return __VA_ARGS__;                                       \
    }

#define PY_IMPL_SEQ_ATTR_FROMPY(typeName, attrName, ...)          \
    static inline int PyAsn##typeName##__##attrName##_FromPython( \
        PyObject* value, typeName##_t* dst) {                     \
        void* target = (void*)&dst->attrName;                     \
        if (value == NULL) return 0;                              \
        return __VA_ARGS__;                                       \
    }

#define PY_IMPL_SEQ_ATTR_INDIRECT_TOPY(typeName, attrName, ...)       \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython( \
        typeName##_t* src, PyObject* parent) {                        \
        void* target = (void*)src->attrName;                          \
        if (!target) {                                                \
            Py_RETURN_NONE;                                           \
        };                                                            \
        return __VA_ARGS__;                                           \
    }

#define PY_IMPL_SEQ_ATTR_TOPY(typeName, attrName, ...)                \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython( \
        typeName##_t* src, PyObject* parent) {                        \
        void* target = (void*)&src->attrName;                         \
        return __VA_ARGS__;                                           \
    }

#define PY_IMPL_SEQ_REF_ATTR_TOPY(typeName, attrName, targetTypeName) \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython( \
        typeName##_t* src, PyObject* parent) {                        \
        void* target = (void*)&src->attrName;                         \
        PyAsn##targetTypeName##Object* targetObj =                    \
            PyCompatAsnType_New(targetTypeName);                      \
        if (!targetObj) {                                             \
            return NULL;                                              \
        }                                                             \
        targetObj->ob_value = (targetTypeName##_t*)target;            \
        targetObj->ob_parent = Py_NewRef(parent);                     \
        targetObj->s_valid = 1;                                       \
        return (PyObject*)targetObj;                                  \
    }

#define PY_IMPL_SEQ_REF_ATTR_INDIRECT_TOPY(typeName, attrName, targetTypeName) \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython(          \
        typeName##_t* src, PyObject* parent) {                                 \
        void* target = (void*)src->attrName;                                   \
        PyAsn##targetTypeName##Object* targetObj = NULL;                       \
        if (target == NULL) Py_RETURN_NONE;                                    \
        targetObj = PyCompatAsnType_New(targetTypeName);                       \
        if (targetObj == NULL) return NULL;                                    \
        targetObj->ob_value = (targetTypeName##_t*)target;                     \
        targetObj->ob_parent = Py_NewRef(parent);                              \
        targetObj->s_valid = 1;                                                \
        return (PyObject*)targetObj;                                           \
    }

#define PY_IMPL_SEQ_OPT_GETATTR(typeName, attrName)                       \
    static PyObject* PyAsn##typeName##__get_##attrName(                   \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {        \
        if (!(self->ob_value->attrName)) {                                \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        return PyAsn##typeName##__##attrName##_ToPython(self->ob_value,   \
                                                        (PyObject*)self); \
    }

#define PY_IMPL_SEQ_GETATTR(typeName, attrName)                           \
    static PyObject* PyAsn##typeName##__get_##attrName(                   \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {        \
        return PyAsn##typeName##__##attrName##_ToPython(self->ob_value,   \
                                                        (PyObject*)self); \
    }

#define PY_IMPL_SEQ_SETATTR(typeName, attrName)                            \
    static int PyAsn##typeName##__set_##attrName(                          \
        PyAsn##typeName##Object* self, PyObject* value,                    \
        void* Py_UNUSED(closure)) {                                        \
        return PyAsn##typeName##__##attrName##_FromPython(value,           \
                                                          self->ob_value); \
    }

#define PY_IMPL_SEQ_OPT_SETATTR(typeName, attrName)                            \
    static int PyAsn##typeName##__set_##attrName(                              \
        PyAsn##typeName##Object* self, PyObject* value,                        \
        void* Py_UNUSED(closure)) {                                            \
        if (value == NULL || Py_IsNone(value)) {                               \
            self->ob_value->attrName = NULL;                                   \
            return 0;                                                          \
        } else {                                                               \
            return PyAsn##typeName##__##attrName##_FromPython(value,           \
                                                              self->ob_value); \
        }                                                                      \
    }

#define PY_IMPL_SEQ_GENERIC_TOPY(typeName) \
    PY_IMPL_SEQ_TOPY(typeName, &asn_DEF_##typeName)

#define PY_IMPL_SEQ_TOPY(typeName, type_DEF)                              \
    PyObject* PyAsn##typeName##_ToPython(typeName##_t* src,               \
                                         PyObject* parent) {              \
        PyAsn##typeName##Object* self = PyCompatAsnType_New(typeName);    \
        if (!parent) {                                                    \
            if (asn_copy((type_DEF), (void**)&self->ob_value, src) < 0) { \
                Py_DECREF(self);                                          \
                return NULL;                                              \
            }                                                             \
        } else {                                                          \
            PyMem_RawFree(self->ob_value);                                \
            self->ob_value = (typeName##_t*)src;                          \
            self->ob_parent = Py_NewRef(parent);                          \
        }                                                                 \
        self->s_valid = 1;                                                \
        return (PyObject*)self;                                           \
    }

#define PY_IMPL_SEQ_INIT_ATTR(typeName, pyAttrName, attrName)                \
    if (result == 0) {                                                       \
        PyCompat_GenericGetAttr(pObj, pyAttrName, tmp);                      \
        if (tmp != NULL && tmp != Py_None) {                                 \
            if (PyAsn##typeName##__##attrName##_FromPython(tmp, pDst) < 0) { \
                ASN_DEBUG("Failed to set " #pyAttrName " attribute");        \
                result = -1;                                                 \
            } else {                                                         \
                Py_CLEAR(tmp);                                               \
            }                                                                \
        } else                                                               \
            PyErr_Clear();                                                   \
    }

#define PY_IMPL_SEQ_FROMPY(typeName, type_DEF, ...)                         \
    int PyAsn##typeName##_FromPython(PyObject* pObj, typeName##_t* pDst) {  \
        PyObject* tmp = NULL;                                               \
        int result = 0;                                                     \
        if (pObj != NULL) {                                                 \
            PY_IMPL_FROMPY_COMPAT_INTERNAL(typeName, pObj, pDst, type_DEF); \
            __VA_ARGS__;                                                    \
        }                                                                   \
        Py_XDECREF(tmp);                                                    \
        return result;                                                      \
    }

#define PY_IMPL_SEQ_INIT(typeName)                                         \
    static int PyAsn##typeName##__init(PyAsn##typeName##Object* self,      \
                                       PyObject* args, PyObject* kwargs) { \
        self->s_valid = 1;                                                 \
        PY_IMPL_INIT_KWONLY(typeName, args, kwargs);                       \
        if (PyAsn##typeName##_FromPython(kwargs, self->ob_value) < 0) {    \
            return -1;                                                     \
        }                                                                  \
        return 0;                                                          \
    }

#define PY_IMPL_MOD_ASSIGN_OBJECT(typeName, attrName, obj)              \
    if (PyDict_SetItemString((PyObject*)PyAsn##typeName##_Type.tp_dict, \
                             #attrName, (PyObject*)(obj)) < 0) {        \
        return -1;                                                      \
    }

#define PY_IMPL_MOD_ASSIGN_INNER(innerTypeName, attrName, obj)    \
    if (PyDict_SetItemString(                                     \
            (PyObject*)((PyAsn##innerTypeName##_Type))->tp_dict), \
        #attrName, (obj))                                         \
        < 0) {                                                   \
            return -1;                                           \
        }

/* inner anonymous types */
#define PY_IMPL_SEQ_ANON_ATTR_FROMPY(typeName, attrName, attr, innerTypeName) \
    static inline int PyAsn##typeName##__##attrName##_FromPython(             \
        PyObject* value, typeName##_t* src) {                                 \
        return PyAsn##innerTypeName##_FromPython(value, (attr));              \
    }

#define PY_IMPL_SEQ_ANON_ATTR_TOPY(typeName, attrName, attr, innerTypeName) \
    static inline PyObject* PyAsn##typeName##__##attrName##_ToPython(       \
        typeName##_t* src, PyObject* parent) {                              \
        return PyAsn##innerTypeName##_ToPython((attr), parent);             \
    }

#define PY_IMPL_SEQ_INNER_GETATTR(typeName, attrName, attr, innerTypeName) \
    static PyObject* PyAsn##typeName##__get_##attrName(                    \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {         \
        if ((attr) == NULL) Py_RETURN_NONE;                                \
        return PyAsn##innerTypeName##_ToPython((attr), (PyObject*)self);   \
    }

#define PY_IMPL_SEQ_INNER_OPT_GETATTR(typeName, attrName, innerTypeName) \
    static PyObject* PyAsn##typeName##__get_##attrName(                  \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {       \
        if (self->ob_value->attrName == NULL) {                          \
            Py_RETURN_NONE;                                              \
        }                                                                \
        return PyAsn##innerTypeName##_ToPython(self->ob_value->attrName, \
                                               (PyObject*)self);         \
    }

#define PY_IMPL_SEQ_INNER_SETATTR(typeName, attrName, attr, innerTypeName) \
    static int PyAsn##typeName##__set_##attrName(                          \
        PyAsn##typeName##Object* self, PyObject* value,                    \
        void* Py_UNUSED(closure)) {                                        \
        return PyAsn##innerTypeName##_FromPython(value,                    \
                                                 &self->ob_value->attr);   \
    }

#define PY_IMPL_SEQ_INNER_OPT_SETATTR(typeName, attrName, attr, innerTypeName, \
                                      type_DEF)                                \
    static int PyAsn##typeName##__set_##attrName(                              \
        PyAsn##typeName##Object* self, PyObject* value,                        \
        void* Py_UNUSED(closure)) {                                            \
        if (value == Py_None) {                                                \
            if (self->ob_value->attrName != NULL) {                            \
                ASN_STRUCT_RESET((type_DEF), self->ob_value->attr);            \
                PyMem_RawFree(self->ob_value->attr);                           \
            }                                                                  \
            self->ob_value->attrName = NULL;                                   \
            return 0;                                                          \
        }                                                                      \
        if (self->ob_value->attrName == NULL) {                                \
            PY_IMPL_SAFE_MALLOC(self->ob_value->attrName, innerTypeName##_t);  \
            if (self->ob_value->attrName == NULL) {                            \
                return -1;                                                     \
            }                                                                  \
            ASN_STRUCT_RESET((type_DEF), self->ob_value->attrName);            \
        }                                                                      \
        return PyAsn##innerTypeName##_FromPython(value, self->ob_value->attr); \
    }

/* SET */
#define PY_IMPL_SET_FROMPY(typeName, type_DEF, ...)                        \
    int PyAsn##typeName##_FromPython(PyObject* pObj, typeName##_t* pDst) { \
        PyObject* tmp = NULL;                                              \
        int result = 0;                                                    \
        if (pObj != NULL) {                                                \
            __VA_ARGS__;                                                   \
        }                                                                  \
        Py_XDECREF(tmp);                                                   \
        return result;                                                     \
    }

#define PY_IMPL_SET_INNER_SETATTR(typeName, enumTypeName, attrName, attr,    \
                                  innerTypeName)                             \
    static int PyAsn##typeName##__set_##attrName(                            \
        PyAsn##typeName##Object* self, PyObject* value,                      \
        void* Py_UNUSED(closure)) {                                          \
        int result = 0;                                                      \
        result =                                                             \
            PyAsn##innerTypeName##_FromPython(value, &self->ob_value->attr); \
        if (result == 0) {                                                   \
            ASN_SET_MKPRESENT(&self->ob_value->_presence_map,                \
                              enumTypeName##_PR_##attrName);                 \
        }                                                                    \
        return result;                                                       \
    }

#define PY_IMPL_SET_INNER_OPT_SETATTR(typeName, enumTypeName, attrName, attr,  \
                                      innerTypeName, type_DEF)                 \
    static int PyAsn##typeName##__set_##attrName(                              \
        PyAsn##typeName##Object* self, PyObject* value,                        \
        void* Py_UNUSED(closure)) {                                            \
        if (value == Py_None) {                                                \
            if (self->ob_value->attrName != NULL) {                            \
                ASN_STRUCT_RESET((type_DEF), self->ob_value->attr);            \
                PyMem_RawFree(self->ob_value->attr);                           \
            }                                                                  \
            self->ob_value->attrName = NULL;                                   \
            ASN_SET_RMPRESENT(&self->ob_value->_presence_map,                  \
                              enumTypeName##_PR_##attrName);                   \
            return 0;                                                          \
        }                                                                      \
        if (self->ob_value->attrName == NULL) {                                \
            PY_IMPL_SAFE_MALLOC(self->ob_value->attrName, innerTypeName##_t);  \
            if (self->ob_value->attrName == NULL) {                            \
                return -1;                                                     \
            }                                                                  \
        }                                                                      \
        return PyAsn##innerTypeName##_FromPython(value, self->ob_value->attr); \
    }

#define PY_IMPL_SET_INNER_GETATTR(typeName, enumTypeName, attrName, attr, \
                                  innerTypeName)                          \
    static PyObject* PyAsn##typeName##__get_##attrName(                   \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {        \
        if (!(ASN_SET_ISPRESENT(self->ob_value,                           \
                                enumTypeName##_PR_##attrName))) {         \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        return PyAsn##innerTypeName##_ToPython((attr), (PyObject*)self);  \
    }

#define PY_IMPL_SET_INNER_OPT_GETATTR(typeName, enumTypeName, attrName,  \
                                      innerTypeName)                     \
    static PyObject* PyAsn##typeName##__get_##attrName(                  \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {       \
        if (self->ob_value->attrName == NULL ||                          \
            !(ASN_SET_ISPRESENT(self->ob_value,                          \
                                enumTypeName##_PR_##attrName))) {        \
            Py_RETURN_NONE;                                              \
        }                                                                \
        return PyAsn##innerTypeName##_ToPython(self->ob_value->attrName, \
                                               (PyObject*)self);         \
    }

#define PY_IMPL_SET_OPT_GETATTR(typeName, enumTypeName, attrName)         \
    static PyObject* PyAsn##typeName##__get_##attrName(                   \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {        \
        if (!(self->ob_value->attrName) ||                                \
            !(ASN_SET_ISPRESENT(self->ob_value,                           \
                                enumTypeName##_PR_##attrName))) {         \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        return PyAsn##typeName##__##attrName##_ToPython(self->ob_value,   \
                                                        (PyObject*)self); \
    }

#define PY_IMPL_SET_GETATTR(typeName, enumTypeName, attrName)             \
    static PyObject* PyAsn##typeName##__get_##attrName(                   \
        PyAsn##typeName##Object* self, void* Py_UNUSED(closure)) {        \
        if (!(ASN_SET_ISPRESENT(self->ob_value,                           \
                                enumTypeName##_PR_##attrName))) {         \
            Py_RETURN_NONE;                                               \
        }                                                                 \
        return PyAsn##typeName##__##attrName##_ToPython(self->ob_value,   \
                                                        (PyObject*)self); \
    }

#define PY_IMPL_SET_SETATTR(typeName, enumTypeName, attrName)                  \
    static int PyAsn##typeName##__set_##attrName(                              \
        PyAsn##typeName##Object* self, PyObject* value,                        \
        void* Py_UNUSED(closure)) {                                            \
        int result = 0;                                                        \
        result =                                                               \
            PyAsn##typeName##__##attrName##_FromPython(value, self->ob_value); \
        if (result == 0) {                                                     \
            ASN_SET_MKPRESENT(&self->ob_value->_presence_map,                  \
                              enumTypeName##_PR_##attrName);                   \
        }                                                                      \
        return result;                                                         \
    }

#define PY_IMPL_SET_OPT_SETATTR(typeName, enumTypeName, attrName)             \
    static int PyAsn##typeName##__set_##attrName(                             \
        PyAsn##typeName##Object* self, PyObject* value,                       \
        void* Py_UNUSED(closure)) {                                           \
        if (value == NULL || Py_IsNone(value)) {                              \
            self->ob_value->attrName = NULL;                                  \
            ASN_SET_RMPRESENT(&self->ob_value->_presence_map,                 \
                              enumTypeName##_PR_##attrName);                  \
            return 0;                                                         \
        }                                                                     \
        if (PyAsn##typeName##__##attrName##_FromPython(value,                 \
                                                       self->ob_value) < 0) { \
            return -1;                                                        \
        }                                                                     \
        ASN_SET_MKPRESENT(&self->ob_value->_presence_map,                     \
                          enumTypeName##_PR_##attrName);                      \
        return 0;                                                             \
    }

#define PY_IMPL_SET_INIT_ATTR(typeName, enumTypeName, pyAttrName, attrName)  \
    if (result == 0) {                                                       \
        PyCompat_GenericGetAttr(pObj, pyAttrName, tmp);                      \
        if (tmp && tmp != Py_None) {                                         \
            if (PyAsn##typeName##__##attrName##_FromPython(tmp, pDst) < 0) { \
                result = -1;                                                 \
            } else {                                                         \
                ASN_SET_MKPRESENT(&pDst->_presence_map,                      \
                                  enumTypeName##_PR_##attrName);             \
                Py_CLEAR(tmp);                                               \
            }                                                                \
        } else                                                               \
            PyErr_Clear();                                                   \
        if (tmp) Py_CLEAR(tmp);                                              \
    }

/* SEQ OF / SET OF*/
#define PY_IMPL_SEQ_OF_COMPONENT_TYPE(ptrType_DEF) \
    ((ptrType_DEF)->elements[0].type)

#define PY_IMPL_SEQ_OF_NEW(typeName)                              \
    static PyObject* PyAsn##typeName##__new(                      \
        PyTypeObject* type, PyObject* args, PyObject* kwargs) {   \
        PyAsn##typeName##Object* self;                            \
        self = (PyAsn##typeName##Object*)type->tp_alloc(type, 0); \
        if (self == NULL) {                                       \
            return NULL;                                          \
        }                                                         \
        PY_IMPL_SAFE_MALLOC(self->ob_value, typeName##_t);        \
        if (self->ob_value == NULL) {                             \
            Py_CLEAR(self);                                       \
        } else {                                                  \
            self->s_valid = 1;                                    \
            self->ob_parent = NULL;                               \
        }                                                         \
        return (PyObject*)self;                                   \
    }

#define PY_IMPL_SEQ_OF_DEALLOC(typeName, EMPTY_FUNC)                        \
    static void PyAsn##typeName##__dealloc(PyAsn##typeName##Object* self) { \
        ASN_DEBUG("Freeing " #typeName " object (value=%p, parent=%p)",     \
                  self->ob_value, self->ob_parent);                         \
        if (self->ob_parent) {                                              \
            if (Py_REFCNT(self->ob_parent) < 1) {                           \
                PyErr_SetString(PyExc_MemoryError,                          \
                                "UAF: parent object already deleted!");     \
                return;                                                     \
            }                                                               \
            Py_DECREF(self->ob_parent);                                     \
            self->ob_value = NULL;                                          \
        } else {                                                            \
            if (self->ob_value != NULL) {                                   \
                if (self->ob_value->list.count > 0) {                       \
                    EMPTY_FUNC((void*)&self->ob_value->list);               \
                }                                                           \
                PyMem_RawFree(self->ob_value);                              \
            }                                                               \
            self->ob_value = NULL;                                          \
            self->ob_parent = NULL;                                         \
        }                                                                   \
        Py_TYPE(self)->tp_free((PyObject*)self);                            \
    }

#define PY_IMPL_SEQ_OF_REPR(typeName)                                         \
    static PyObject* PyAsn##typeName##__repr(PyAsn##typeName##Object* self) { \
        return PyUnicode_FromFormat("<%s elements=%zd>", #typeName,           \
                                    self->ob_value->list.count);              \
    }

#define PY_IMPL_SEQ_OF_FROMPY(typeName, memberTypeName)                      \
    int PyAsn##typeName##_FromPython(PyObject* p_obj, typeName##_t* p_dst) { \
        PyObject *iterator = NULL, *item = NULL, *list = NULL;               \
        memberTypeName* item_value = NULL;                                   \
        if ((iterator = PyObject_GetIter(p_obj)) == NULL) {                  \
            PyErr_Clear();                                                   \
            list = PySequence_List(p_obj);                                   \
            if (!list) return -1;                                            \
            iterator = PyObject_GetIter(list);                               \
            if (!iterator) {                                                 \
                Py_XDECREF(list);                                            \
                return -1;                                                   \
            }                                                                \
        }                                                                    \
        while ((item = PyIter_Next(iterator)) != NULL) {                     \
            PY_IMPL_SAFE_MALLOC(item_value, memberTypeName);                 \
            if (item_value == NULL) {                                        \
                goto end;                                                    \
            }                                                                \
            if (PyAsn##typeName##__component_FromPython(item, item_value) <  \
                0) {                                                         \
                goto end;                                                    \
            }                                                                \
            if (asn_set_add(&p_dst->list, item_value) < 0) {                 \
                PyErr_BadInternalCall();                                     \
                PY_IMPL_FREE(item_value);                                    \
                goto end;                                                    \
            }                                                                \
            Py_CLEAR(item);                                                  \
        }                                                                    \
    end:                                                                     \
        Py_XDECREF(iterator);                                                \
        Py_XDECREF(list);                                                    \
        return PyErr_Occurred() ? -1 : 0;                                    \
    }

#define PY_IMPL_SEQ_OF_LEN(typeName)                                          \
    static Py_ssize_t PyAsn##typeName##__len(PyAsn##typeName##Object* self) { \
        return self->ob_value->list.count;                                    \
    }

#define PY_IMPL_SEQ_OF_ITEM_TOPY(typeName, memberTypeName, ...)    \
    static inline PyObject* PyAsn##typeName##__component_ToPython( \
        memberTypeName* src, PyObject* parent) {                   \
        return __VA_ARGS__;                                        \
    }

#define PY_IMPL_SEQ_OF_ITEM_FROMPY(typeName, memberTypeName, ...) \
    static inline int PyAsn##typeName##__component_FromPython(    \
        PyObject* value, memberTypeName* target) {                \
        return __VA_ARGS__;                                       \
    }

#define PY_IMPL_SEQ_OF_GETITEM(typeName)                                       \
    static PyObject* PyAsn##typeName##__getitem(PyAsn##typeName##Object* self, \
                                                Py_ssize_t index) {            \
        if (!self || !self->ob_value) {                                        \
            PyErr_SetString(PyExc_ValueError,                                  \
                            #typeName ": object has no value");                \
            return NULL;                                                       \
        }                                                                      \
        if (index < 0) index += (Py_ssize_t)self->ob_value->list.count;        \
        if (index < 0 || index >= self->ob_value->list.count) {                \
            PyErr_SetString(PyExc_IndexError, "list index out of range");      \
            return NULL;                                                       \
        }                                                                      \
        return PyAsn##typeName##__component_ToPython(                          \
            self->ob_value->list.array[index], (PyObject*)self);               \
    }

#define PY_IMPL_SEQ_OF_SETITEM(typeName, memberTypeName) \
    PY_IMPL_SEQ_OF_GENERIC_SETITEM(                      \
        typeName, memberTypeName,                        \
        *(PY_IMPL_SEQ_OF_COMPONENT_TYPE(&asn_DEF_##typeName)))

#define PY_IMPL_SEQ_OF_GENERIC_SETITEM(typeName, memberTypeName, type_DEF)     \
    static int PyAsn##typeName##__setitem(PyAsn##typeName##Object* self,       \
                                          Py_ssize_t index, PyObject* value) { \
        void** target = NULL;                                                  \
        if (index >= self->ob_value->list.count) {                             \
            PyErr_SetString(PyExc_IndexError, "list index out of range");      \
            return -1;                                                         \
        }                                                                      \
        target = (void**)&self->ob_value->list.array[index];                   \
        if (target != NULL) {                                                  \
            ASN_STRUCT_FREE((type_DEF), *target);                              \
        }                                                                      \
        if (value == NULL) {                                                   \
            if (index + 1 != self->ob_value->list.count) {                     \
                memmove(                                                       \
                    &self->ob_value->list.array[index],                        \
                    &self->ob_value->list.array[index + 1],                    \
                    sizeof(void*) * (self->ob_value->list.count - index - 1)); \
            }                                                                  \
            self->ob_value->list.count--;                                      \
            return 0;                                                          \
        }                                                                      \
        *target = (void*)PY_IMPL_MALLOC(memberTypeName);                       \
        if (*target == NULL) {                                                 \
            return -1;                                                         \
        }                                                                      \
        memset(*target, 0, sizeof(memberTypeName));                            \
        if (PyAsn##typeName##__component_FromPython(                           \
                value, (memberTypeName*)(*target)) < 0) {                      \
            PY_IMPL_FREE(*target);                                             \
            *target = NULL;                                                    \
            return -1;                                                         \
        }                                                                      \
        return 0;                                                              \
    }

#define PY_IMPL_SEQ_OF_ADD(typeName, memberTypeName)                         \
    static PyObject* PyAsn##typeName##__add(PyAsn##typeName##Object* self,   \
                                            PyObject* args) {                \
        static char* kwlist[] = {"value", NULL};                             \
        PyObject* value = NULL;                                              \
        memberTypeName* dst = NULL;                                          \
        if (!PyArg_ParseTupleAndKeywords(args, NULL, "O", kwlist, &value))   \
            return NULL;                                                     \
        dst = PY_IMPL_MALLOC(memberTypeName);                                \
        if (dst == NULL) {                                                   \
            return NULL;                                                     \
        }                                                                    \
        memset(dst, 0, sizeof(memberTypeName));                              \
        if (PyAsn##typeName##__component_FromPython(value, dst) < 0) {       \
            PyMem_RawFree(dst);                                              \
            return NULL;                                                     \
        }                                                                    \
        if (asn_set_add(&self->ob_value->list, (void*)dst) < 0) return NULL; \
        Py_RETURN_NONE;                                                      \
    }

#define PY_IMPL_SEQ_OF_CLEAR(typeName)                                         \
    static PyObject* PyAsn##typeName##__clear(PyAsn##typeName##Object* self) { \
        asn_set_empty(&self->ob_value->list);                                  \
        Py_RETURN_NONE;                                                        \
    }

#define PY_IMPL_SEQ_OF_EXTEND(typeName)                                       \
    static PyObject* PyAsn##typeName##__extend(PyAsn##typeName##Object* self, \
                                               PyObject* args) {              \
        static char* kwlist[] = {"value", NULL};                              \
        PyObject* value = NULL;                                               \
        if (!PyArg_ParseTupleAndKeywords(args, NULL, "O", kwlist, &value))    \
            return NULL;                                                      \
        return PyAsn##typeName##_FromPython(value, self->ob_value) < 0        \
                   ? NULL                                                     \
                   : Py_None;                                                 \
    }

#define PY_IMPL_SEQ_OF_INIT(typeName)                                          \
    static int PyAsn##typeName##__init(PyAsn##typeName##Object* self,          \
                                       PyObject* args, PyObject* kwargs) {     \
        static char* kwlist[] = {"values", NULL};                              \
        PyObject* values = NULL;                                               \
        if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", kwlist, &values)) \
            return -1;                                                         \
        if (values) {                                                          \
            if (PyAsn##typeName##_FromPython(values, self->ob_value) < 0)      \
                return -1;                                                     \
        }                                                                      \
        return 0;                                                              \
    }

/* MODULE */
#define PY_IMPL_MODULE_CLEAR(mod, ...)                   \
    static int PyAsnModule_##mod##__clear(PyObject* m) { \
        __VA_ARGS__;                                     \
        return 0;                                        \
    }                                                    \
    static void PyAsnModule_##mod##__free(void* m) {     \
        PyAsnModule_##mod##__clear((PyObject*)m);        \
    }

#define PY_IMPL_MODULE_DEF(mod)                \
    PyModuleDef PyAsnModule_##mod = {          \
        PyModuleDef_HEAD_INIT,                 \
        .m_name = #mod,                        \
        .m_doc = NULL,                         \
        .m_size = 0,                           \
        .m_free = PyAsnModule_##mod##__free,   \
        .m_clear = PyAsnModule_##mod##__clear, \
    };

#define PY_IMPL_MODULE_INIT_BEGIN(mod)                              \
    PyMODINIT_FUNC PyInit_##mod(void) {                             \
        PyObject* nModule = PyState_FindModule(&PyAsnModule_##mod); \
        if (nModule) return Py_NewRef(nModule);

#define PY_IMPL_MODULE_INIT_END \
    return nModule;             \
    }

/* BIT STRING */
#define PY_IMPL_BIT_STRING_RESIZE(typeName)                                  \
    static PyObject* PyAsn##typeName##__resize(                              \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) {   \
        static char* kwlist[] = {"size", NULL};                              \
        Py_ssize_t target_size = 0, old_size = 0;                            \
        if (!PyArg_ParseTupleAndKeywords(args, kwargs, "n", kwlist,          \
                                         &target_size))                      \
            return NULL;                                                     \
        if (target_size <= 0) {                                              \
            PyErr_SetString(PyExc_ValueError,                                \
                            "size must be non-negative and non-zero");       \
            return NULL;                                                     \
        }                                                                    \
        if (target_size <= self->ob_value->size) {                           \
            PyErr_SetString(PyExc_ValueError,                                \
                            "size must be greater than current size");       \
            return NULL;                                                     \
        }                                                                    \
        if (PyCompatBITSTRING_Resize(self->ob_value, (size_t)target_size) == \
            -1)                                                              \
            return NULL;                                                     \
        Py_RETURN_NONE;                                                      \
    }

#define PY_IMPL_BIT_STRING_CLEAR(typeName)                                     \
    static PyObject* PyAsn##typeName##__clear(PyAsn##typeName##Object* self) { \
        if (self->ob_value != NULL && self->ob_value->buf != NULL)             \
            memset(self->ob_value->buf, 0, (size_t)self->ob_value->size);      \
        Py_RETURN_NONE;                                                        \
    }

#define PY_IMPL_BIT_STRING_INIT(typeName)                                   \
    static int PyAsn##typeName##__init(PyAsn##typeName##Object* self,       \
                                       PyObject* args, PyObject* kwds) {    \
        static char* kwlist[] = {"size", NULL};                             \
        Py_ssize_t target_size = PyAsn##typeName##_MAX_SIZE;                \
        int res = 0;                                                        \
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|n", kwlist,          \
                                         &target_size))                     \
            return -1;                                                      \
        if (target_size < 0) {                                              \
            PyErr_SetString(PyExc_ValueError, "size must be non-negative"); \
            return -1;                                                      \
        }                                                                   \
        res = PyCompatBITSTRING_New(self->ob_value, (size_t)target_size);   \
        self->s_valid = res != -1;                                          \
        return res;                                                         \
    }

#define PY_IMPL_BIT_STRING_GETATTR(typeName, attrName, attrValue)       \
    static PyObject* PyAsn##typeName##__get_##attrName(                 \
        PyAsn##typeName##Object* self, void* closure) {                 \
        return PyCompatBITSTRING_GetFlag(self->ob_value, (attrValue),   \
                                         (PyAsn##typeName##_MAX_SIZE)); \
    }

#define PY_IMPL_BIT_STRING_SETATTR(typeName, attrName, attrValue)            \
    static int PyAsn##typeName##__set_##attrName(                            \
        PyAsn##typeName##Object* self, PyObject* value, void* closure) {     \
        return PyCompatBITSTRING_SetFlag(self->ob_value, (attrValue), value, \
                                         (PyAsn##typeName##_MAX_SIZE));      \
    }

#define PY_IMPL_BIT_STRING_SIZE(typeName)                                     \
    static PyObject* PyAsn##typeName##__size(PyAsn##typeName##Object* self) { \
        return PyLong_FromSize_t(self->ob_value->size);                       \
    }

#define PY_IMPL_BIT_STRING_SET(typeName)                                   \
    static PyObject* PyAsn##typeName##__set(                               \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        static char* kwlist[] = {"bit", "flag", NULL};                     \
        PyObject* obj = NULL;                                              \
        Py_ssize_t bit = -1;                                               \
        if (!PyArg_ParseTupleAndKeywords(args, kwargs, "nO", kwlist, &bit, \
                                         &obj))                            \
            return NULL;                                                   \
        if (bit < 0 || PyCompatBITSTRING_index((size_t)bit, uint8_t) >=    \
                           self->ob_value->size) {                         \
            PyErr_SetString(PyExc_IndexError, "bit index out of range");   \
            return NULL;                                                   \
        }                                                                  \
        PyCompatBITSTRING_SetFlag(self->ob_value, (size_t)bit, obj,        \
                                  PyAsn##typeName##_MAX_SIZE);             \
        Py_RETURN_NONE;                                                    \
    }

#define PY_IMPL_BIT_STRING_GET(typeName)                                   \
    static PyObject* PyAsn##typeName##__get(                               \
        PyAsn##typeName##Object* self, PyObject* args, PyObject* kwargs) { \
        static char* kwlist[] = {"bit", NULL};                             \
        Py_ssize_t bit = -1;                                               \
        if (!PyArg_ParseTupleAndKeywords(args, kwargs, "n", kwlist, &bit)) \
            return NULL;                                                   \
        if (bit < 0 || PyCompatBITSTRING_index((size_t)bit, uint8_t) >=    \
                           self->ob_value->size) {                         \
            PyErr_SetString(PyExc_IndexError, "bit index out of range");   \
            return NULL;                                                   \
        }                                                                  \
        return PyCompatBITSTRING_GetFlag(self->ob_value, (size_t)bit,      \
                                         PyAsn##typeName##_MAX_SIZE);      \
    }

#define PY_IMPL_BIT_STRING_NEW(name)                                        \
    static PyObject* PyAsn##name##__new(PyTypeObject* type, PyObject* args, \
                                        PyObject* kwds) {                   \
        PyAsn##name##Object* self =                                         \
            (PyAsn##name##Object*)type->tp_alloc(type, 0);                  \
        if (self) {                                                         \
            self->ob_value = NULL;                                          \
            self->s_valid = 0;                                              \
            self->ob_parent = NULL;                                         \
            PY_IMPL_SAFE_MALLOC(self->ob_value, BIT_STRING_t);              \
            if (self->ob_value == NULL) {                                   \
                Py_CLEAR(self);                                             \
            }                                                               \
        }                                                                   \
        return (PyObject*)self;                                             \
    }

#endif