#ifndef	_ASN_PY_MODULE_H_
#define	_ASN_PY_MODULE_H_


#include <py_application.h>

/* Includes */
#include <Data_Py.h>
#include <MMSString_Py.h>
#include <FloatingPoint_Py.h>
#include <TimeOfDay_Py.h>
#include <IEC61850-Specific-Protocol_Py.h>
#include <GSEMngtPdu_Py.h>
#include <GSERequestResponse_Py.h>
#include <GSEMngtRequests_Py.h>
#include <GSEMngtResponses_Py.h>
#include <GetReferenceRequestPdu_Py.h>
#include <GetElementRequestPdu_Py.h>
#include <GSEMngtResponsePdu_Py.h>
#include <RequestResults_Py.h>
#include <GlbErrors_Py.h>
#include <ErrorReason_Py.h>
#include <IECGoosePdu_Py.h>
#include <UtcTime_Py.h>
#include <EXTERNAL_Py.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Module Type */
extern PyModuleDef PyAsnModule__iec61850;

#ifdef __cplusplus
}
#endif

#endif	/* _ASN_PY_MODULE_H_ */
