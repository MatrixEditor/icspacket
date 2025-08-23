# icspacket-common.cmake
# Defines a helper function for building ASN.1-based Python C extensions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Usage
#
# # Minimal usage: build an extension from MOD_DIR sources
# add_asn1_extension(
#     mymodule                                      # Python extension name
#     ${ICS_SOURCE_DIR}/proto/mymodule/_mymodule    # Sources directory
#     proto/mymodule                                # Install subdirectory
# )
function(add_asn1_extension MOD_NAME MOD_DIR INSTALL_SUBDIR)
    # Parse function arguments
    set(options)              # (reserved for future boolean flags)
    set(one_value_args)       # (reserved for single-value args)
    set(multi_value_args EXTRA_SOURCES INCLUDES DEFINITIONS)

    cmake_parse_arguments(
        ASN1
        "${options}"
        "${one_value_args}"
        "${multi_value_args}"
        ${ARGN}
    )

    file(GLOB MOD_SOURCES "${MOD_DIR}/*.c")
    python_add_library(
        ${MOD_NAME}
        MODULE
        ${ICS_BASE_SOURCES}
        ${MOD_SOURCES}
        ${ASN1_EXTRA_SOURCES}
        WITH_SOABI
    )

    message(STATUS "======================= [${MOD_NAME}] =======================")
    message(STATUS "Adding ASN.1 extension: ${MOD_NAME} (sources in ${MOD_DIR})")

    target_include_directories(
        ${MOD_NAME}
        PRIVATE
        "${ICS_INCLUDE_DIR}/skeletons"
        "${MOD_DIR}"
        ${ASN1_INCLUDES}
    )
    if(ASN1_DEFINITIONS)
        target_compile_definitions(${MOD_NAME} PRIVATE ${ASN1_DEFINITIONS})
        message(STATUS "Extra definitions: ${ASN1_DEFINITIONS}")
    endif()

    # Install into the Python package namespace under INSTALL_SUBDIR
    install(
        TARGETS ${MOD_NAME}
        DESTINATION ${SKBUILD_PROJECT_NAME}/${INSTALL_SUBDIR}
    )
endfunction()

