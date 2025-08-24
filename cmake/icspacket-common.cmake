# icspacket-common.cmake
# Defines a helper function for building ASN.1-based Python C extensions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Usage
#
# # Minimal usage: build an extension from MOD_DIR sources
# add_asn1_extension(
#     NAME mymodule                                      # Python extension name
#     DIR ${ICS_SOURCE_DIR}/proto/mymodule/_mymodule     # Sources directory
#     INSTALL proto/mymodule                             # Install subdirectory
# )
function(add_asn1_extension)
    # Parse function arguments
    set(options) # (reserved for future boolean flags)
    set(one_value_args NAME DIR INSTALL)
    set(multi_value_args EXTRA_SOURCES INCLUDES DEFINITIONS)

    cmake_parse_arguments(
        ASN1
        "${options}"
        "${one_value_args}"
        "${multi_value_args}"
        ${ARGN}
    )

    file(GLOB MOD_SOURCES "${ASN1_DIR}/*.c")
    python_add_library(
        ${ASN1_NAME}
        MODULE
        ${ICS_BASE_SOURCES}
        ${MOD_SOURCES}
        ${ASN1_EXTRA_SOURCES}
        WITH_SOABI
    )

    message(STATUS "======================= [${ASN1_NAME}] =======================")
    message(STATUS "Adding ASN.1 extension: ${ASN1_NAME} (sources in ${ASN1_DIR})")

    target_include_directories(
        ${ASN1_NAME}
        PRIVATE
        "${ICS_INCLUDE_DIR}/skeletons"
        "${ASN1_DIR}"
        ${ASN1_INCLUDES}
    )
    if(ASN1_DEFINITIONS)
        target_compile_definitions(${ASN1_NAME} PRIVATE ${ASN1_DEFINITIONS})
        message(STATUS "Extra definitions: ${ASN1_DEFINITIONS}")
    endif()

    # Install into the Python package namespace under ASN1_INSTALL_DIR
    install(
        TARGETS ${ASN1_NAME}
        DESTINATION ${SKBUILD_PROJECT_NAME}/${ASN1_INSTALL}
    )
endfunction()

