/*
 * Copyright (c) 2003-2017 Lev Walkin <vlm@lionet.info>. All rights reserved.
 * Redistribution and modifications are permitted subject to BSD license.
 */
/*
 * Miscellaneous system-dependent types.
 */
#ifndef ASN_SYSTEM_H
#define ASN_SYSTEM_H

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

/* Standard headers */
#include <stdio.h>     /* For snprintf(3) */
#include <stdlib.h>    /* For *alloc(3) */
#include <string.h>    /* For memcpy(3) */
#include <sys/types.h> /* For size_t */
#include <limits.h>    /* For LONG_MAX */
#include <stdarg.h>    /* For va_start */
#include <stddef.h>    /* for offsetof and ptrdiff_t */
#include <inttypes.h>  /* for PRIdMAX */

/* --------------------------- Windows branch ----------------------------- */
#ifdef _WIN32

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <math.h>
#include <float.h>

/*
 * MSVC CRT notes:
 * - VS 2015+ (MSVC >= 1900) provides C99 functions like snprintf, ilogb,
 *   copysign, isnan, isfinite, etc. Do NOT remap these.
 * - For very old MSVC, provide minimal, local fallbacks guarded by version.
 */
#if defined(_MSC_VER) && _MSC_VER < 1900
/* Fallbacks for pre-UCRT toolchains ONLY */
#ifndef __MINGW32__
#define snprintf _snprintf
#define vsnprintf _vsnprintf
#endif

/* isnan/isfinite/copysign fallbacks */
#ifndef isnan
#define isnan _isnan
#endif

#ifndef isfinite
static inline int asn_isfinite_double(double x) { return _finite(x); }
#define isfinite asn_isfinite_double
#endif

#ifndef copysign
#define copysign _copysign
#endif

/* Minimal ilogb fallback*/
#ifndef ilogb
static inline int asn_ilogb(double x) { return (int)_logb(x); }
#define ilogb asn_ilogb
#endif

#endif /* _MSC_VER < 1900 */

/* Define ssize_t portably on Windows if missing */
#ifndef HAVE_SSIZE_T
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#define HAVE_SSIZE_T 1
#endif

/* To avoid linking with ws2_32.lib, here's the definition of ntohl() */
#ifndef sys_ntohl
#define sys_ntohl(l)                                          \
    ((((l) << 24) & 0xff000000) | (((l) << 8) & 0x00ff0000) | \
     (((l) >> 8) & 0x0000ff00) | (((l) >> 24) & 0x000000ff))
#endif

#else
/* ------------------------- POSIX / others -------------------------- */

#if defined(__vxworks)
#include <types/vxTypes.h>
#endif

#ifdef HAVE_ARPA_INET_H
#include <arpa/inet.h>
#define sys_ntohl(foo) ntohl(foo)
#elif defined(HAVE_NETINET_IN_H)
#include <netinet/in.h>
#define sys_ntohl(foo) ntohl(foo)
#else
#ifndef sys_ntohl
#define sys_ntohl(l)                                          \
    ((((l) << 24) & 0xff000000) | (((l) << 8) & 0x00ff0000) | \
     (((l) >> 8) & 0x0000ff00) | (((l) >> 24) & 0x000000ff))
#endif
#endif /* HAVE_ARPA_INET_H */

#endif /* _WIN32 */

/* ---------------------------- Attributes -------------------------------- */
#if defined(__GNUC__) || defined(__clang__)
#define CC_UNUSED(name) name __attribute__((unused))
#else
#define CC_UNUSED(name) name
#endif

#if defined(__GNUC__) || defined(__clang__)
#define CC_ATTRIBUTE(attr) __attribute__((attr))
#else
#define CC_ATTRIBUTE(attr)
#endif

#if defined(__GNUC__)
#if (__GNUC__ > 4) || (__GNUC__ == 4 && __GNUC_MINOR__ >= 4)
#define CC_PRINTFLIKE(fmt, var) CC_ATTRIBUTE(format(gnu_printf, fmt, var))
#else
#if defined(ANDROID)
#define CC_PRINTFLIKE(fmt, var) CC_ATTRIBUTE(__format__(__printf__, fmt, var))
#else
#define CC_PRINTFLIKE(fmt, var) CC_ATTRIBUTE(format(printf, fmt, var))
#endif
#endif
#else
#define CC_PRINTFLIKE(fmt, var)
#endif

#define CC_NOTUSED CC_ATTRIBUTE(unused)

#ifndef CC_ATTR_NO_SANITIZE
#if defined(__GNUC__) && (__GNUC__ >= 8)
#define CC_ATTR_NO_SANITIZE(what) CC_ATTRIBUTE(no_sanitize(what))
#else
#define CC_ATTR_NO_SANITIZE(what)
#endif
#endif

/* Thread-safety flag */
#if !defined(ASN_THREAD_SAFE) && (defined(THREAD_SAFE) || defined(_REENTRANT))
#define ASN_THREAD_SAFE 1
#endif

#ifndef MIN /* Suitable for comparing primitive types (integers) */
#if defined(__GNUC__)
#define MIN(a, b)                    \
    ({                               \
        __typeof a _a = a;           \
        __typeof b _b = b;           \
        ((_a) < (_b) ? (_a) : (_b)); \
    })
#else                                     /* !__GNUC__ */
#define MIN(a, b) ((a) < (b) ? (a) : (b)) /* Unsafe variant */
#endif                                    /* __GNUC__ */
#endif                                    /* MIN */

#ifndef SIZE_MAX
#define SIZE_MAX ((size_t)~(size_t)0)
#endif
#ifndef RSIZE_MAX /* C11 Annex K recommendation is implementation-defined; \
                     keep conservative */
#define RSIZE_MAX (SIZE_MAX / 2u)
#endif
#ifndef RSSIZE_MAX
#define RSSIZE_MAX ((ssize_t)(RSIZE_MAX / 2u))
#endif

/* printf-style width macros */
#if defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 199901L)
#define ASN_PRI_SIZE "zu"
#define ASN_PRI_SSIZE "zd"
#define ASN_PRIuMAX PRIuMAX
#define ASN_PRIdMAX PRIdMAX
#define ASN_PRIu64 PRIu64
#define ASN_PRId64 PRId64
#else
#define ASN_PRI_SIZE "zu"
#define ASN_PRI_SSIZE "ld"
#define ASN_PRIu64 "llu"
#define ASN_PRId64 "lld"
#if LLONG_MAX > LONG_MAX
#define ASN_PRIuMAX "llu"
#define ASN_PRIdMAX "lld"
#else
#define ASN_PRIuMAX "lu"
#define ASN_PRIdMAX "ld"
#endif
#endif

#endif /* ASN_SYSTEM_H */
