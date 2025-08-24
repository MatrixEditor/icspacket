/*-
 * Copyright (c) 2003, 2004 Lev Walkin <vlm@lionet.info>. All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
#include <asn_internal.h>
#include <constr_TYPE.h>
#include <errno.h>

/*
 * Version of the ASN.1 infrastructure shipped with compiler.
 */
int get_asn1c_environment_version(void) { return ASN1C_ENVIRONMENT_VERSION; }

static asn_app_consume_bytes_f _print2fp;

/*
 * Return the outmost tag of the type.
 */
ber_tlv_tag_t asn_TYPE_outmost_tag(const asn_TYPE_descriptor_t *type_descriptor,
                                   const void *struct_ptr, int tag_mode,
                                   ber_tlv_tag_t tag) {
    if (tag_mode) return tag;

    if (type_descriptor->tags_count) return type_descriptor->tags[0];

    return type_descriptor->op->outmost_tag(type_descriptor, struct_ptr, 0, 0);
}

/*
 * Print the target language's structure in human readable form.
 */
int asn_fprint(FILE *stream, const asn_TYPE_descriptor_t *td,
               const void *struct_ptr) {
    if (!stream) stream = stdout;
    if (!td || !struct_ptr) {
        errno = EINVAL;
        return -1;
    }

    /* Invoke type-specific printer */
    if (td->op->print_struct(td, struct_ptr, 1, _print2fp, stream)) {
        return -1;
    }

    /* Terminate the output */
    if (_print2fp("\n", 1, stream)) {
        return -1;
    }

    return fflush(stream);
}

/*
 * Copy a structuture.
 */
int asn_copy(const asn_TYPE_descriptor_t *td, void **struct_dst,
             const void *struct_src) {
    if (!td || !struct_dst || !struct_src) {
        errno = EINVAL;
        return -1;
    }

    if (!td->op) {
        errno = ENOSYS;
        return -1;
    }

    return td->op->copy_struct(td, struct_dst, struct_src);
}

/* Dump the data into the specified stdio stream */
static int _print2fp(const void *buffer, size_t size, void *app_key) {
    FILE *stream = (FILE *)app_key;

    if (fwrite(buffer, 1, size, stream) != size) return -1;

    return 0;
}

/* Initialize a structure with default values */
int asn_struct_init(const struct asn_TYPE_descriptor_s *type_descriptor,
                    void *struct_ptr) {
    const asn_TYPE_member_t *memb;
    void *value = NULL;

    if (type_descriptor == NULL || struct_ptr == NULL) {
        errno = EINVAL;
        return -1;
    }

    if (type_descriptor->elements_count == 0 ||
        type_descriptor->elements == NULL) {
        /* nothing to do here */
        return 0;
    }

    for (size_t index = 0; index < type_descriptor->elements_count; ++index) {
        /* either the member has a default value OR it stores a type definition
         */
        memb = &type_descriptor->elements[index];
        if (memb->default_value_set != NULL) {
            if (!(memb->flags & ATF_POINTER)) {
                value = (void *)(((char *)struct_ptr) + memb->memb_offset);
                if (memb->default_value_set(&value) < 0) {
                    return -1;
                }
            }
            /* fall through */
        }
        /* only first-level members are supported for now */
    }
    return 0;
}

/*
 * Some compilers do not support variable args macros.
 * This function is a replacement of ASN_DEBUG() macro.
 */
void CC_PRINTFLIKE(1, 2) ASN_DEBUG_f(const char *fmt, ...);
void ASN_DEBUG_f(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}
