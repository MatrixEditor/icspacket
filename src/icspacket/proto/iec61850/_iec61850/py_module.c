#include "py_module.h"

/* Module Cleanup */
PY_IMPL_MODULE_CLEAR(_iec61850,
	PyAsnData_ModClear(m);
	PyAsnMMSString_ModClear(m);
	PyAsnFloatingPoint_ModClear(m);
	PyAsnTimeOfDay_ModClear(m);
	PyAsnIEC61850_Specific_Protocol_ModClear(m);
	PyAsnGSEMngtPdu_ModClear(m);
	PyAsnGSERequestResponse_ModClear(m);
	PyAsnGSEMngtRequests_ModClear(m);
	PyAsnGSEMngtResponses_ModClear(m);
	PyAsnGetReferenceRequestPdu_ModClear(m);
	PyAsnGetElementRequestPdu_ModClear(m);
	PyAsnGSEMngtResponsePdu_ModClear(m);
	PyAsnRequestResults_ModClear(m);
	PyAsnGlbErrors_ModClear(m);
	PyAsnErrorReason_ModClear(m);
	PyAsnIECGoosePdu_ModClear(m);
	PyAsnUtcTime_ModClear(m);
	PyAsnEXTERNAL_ModClear(m);
	PyCompat_Clear();
);

/* Module Type */
PY_IMPL_MODULE_DEF(_iec61850);

/* Module Init */
PY_IMPL_MODULE_INIT_BEGIN(_iec61850)
	if (PyAsnData_ModSetupTypes() < 0) return NULL;
	if (PyAsnMMSString_ModSetupTypes() < 0) return NULL;
	if (PyAsnFloatingPoint_ModSetupTypes() < 0) return NULL;
	if (PyAsnTimeOfDay_ModSetupTypes() < 0) return NULL;
	if (PyAsnIEC61850_Specific_Protocol_ModSetupTypes() < 0) return NULL;
	if (PyAsnGSEMngtPdu_ModSetupTypes() < 0) return NULL;
	if (PyAsnGSERequestResponse_ModSetupTypes() < 0) return NULL;
	if (PyAsnGSEMngtRequests_ModSetupTypes() < 0) return NULL;
	if (PyAsnGSEMngtResponses_ModSetupTypes() < 0) return NULL;
	if (PyAsnGetReferenceRequestPdu_ModSetupTypes() < 0) return NULL;
	if (PyAsnGetElementRequestPdu_ModSetupTypes() < 0) return NULL;
	if (PyAsnGSEMngtResponsePdu_ModSetupTypes() < 0) return NULL;
	if (PyAsnRequestResults_ModSetupTypes() < 0) return NULL;
	if (PyAsnGlbErrors_ModSetupTypes() < 0) return NULL;
	if (PyAsnErrorReason_ModSetupTypes() < 0) return NULL;
	if (PyAsnIECGoosePdu_ModSetupTypes() < 0) return NULL;
	if (PyAsnUtcTime_ModSetupTypes() < 0) return NULL;
	if (PyAsnEXTERNAL_ModSetupTypes() < 0) return NULL;

	if((nModule = PyModule_Create(&PyAsnModule__iec61850)) == NULL) { return NULL; }

	if (PyCompat_Init() < 0) return NULL;
	if (PyAsnData_ModInit(nModule) < 0) return NULL;
	if (PyAsnMMSString_ModInit(nModule) < 0) return NULL;
	if (PyAsnFloatingPoint_ModInit(nModule) < 0) return NULL;
	if (PyAsnTimeOfDay_ModInit(nModule) < 0) return NULL;
	if (PyAsnIEC61850_Specific_Protocol_ModInit(nModule) < 0) return NULL;
	if (PyAsnGSEMngtPdu_ModInit(nModule) < 0) return NULL;
	if (PyAsnGSERequestResponse_ModInit(nModule) < 0) return NULL;
	if (PyAsnGSEMngtRequests_ModInit(nModule) < 0) return NULL;
	if (PyAsnGSEMngtResponses_ModInit(nModule) < 0) return NULL;
	if (PyAsnGetReferenceRequestPdu_ModInit(nModule) < 0) return NULL;
	if (PyAsnGetElementRequestPdu_ModInit(nModule) < 0) return NULL;
	if (PyAsnGSEMngtResponsePdu_ModInit(nModule) < 0) return NULL;
	if (PyAsnRequestResults_ModInit(nModule) < 0) return NULL;
	if (PyAsnGlbErrors_ModInit(nModule) < 0) return NULL;
	if (PyAsnErrorReason_ModInit(nModule) < 0) return NULL;
	if (PyAsnIECGoosePdu_ModInit(nModule) < 0) return NULL;
	if (PyAsnUtcTime_ModInit(nModule) < 0) return NULL;
	if (PyAsnEXTERNAL_ModInit(nModule) < 0) return NULL;
PY_IMPL_MODULE_INIT_END;
