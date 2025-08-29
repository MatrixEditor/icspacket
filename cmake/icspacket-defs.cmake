
if(CMAKE_VERSION VERSION_LESS 3.18)
    set(DEV_MODULE Development)
else()
    set(DEV_MODULE Development.Module)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter ${DEV_MODULE})

# -----------------------------------------------------------------------------
# Workaround for Windows: construct Python_LIBRARY if not set
# (common in CI with hostedtoolcache)
# -----------------------------------------------------------------------------
if(WIN32 AND NOT DEFINED Python_LIBRARY)
    # Dynamically construct the Python_LIBRARY path using version info from
    # find_package(Python)
    if (NOT Python_VERSION)
        message(FATAL_ERROR
            "Python_VERSION not set after find_package(Python). "
            "Cannot construct Python library path."
        )
    endif()

    # Split the version string into major, minor, and patch parts
    string(REGEX MATCH "^([0-9]+)\\.([0-9]+)\\.(.+)" _ ${Python_VERSION})
    set(Python_VERSION_MAJOR ${CMAKE_MATCH_1})
    set(Python_VERSION_MINOR ${CMAKE_MATCH_2})
    set(Python_VERSION_PATCH ${CMAKE_MATCH_3})

    set(DYNAMIC_PYTHON_LIB_FILENAME "python${Python_VERSION_MAJOR}${Python_VERSION_MINOR}_d.lib")
    set(EXPECTED_PYTHON_VERSION_DIR "C:/hostedtoolcache/windows/Python/${Python_VERSION}/x64/libs")
    set(Python_LIBRARY "${EXPECTED_PYTHON_VERSION_DIR}/${DYNAMIC_PYTHON_LIB_FILENAME}")

    message(STATUS "DEBUG: On Windows, constructed DYNAMIC_PYTHON_LIB_FILENAME: ${DYNAMIC_PYTHON_LIB_FILENAME}")
    message(STATUS "DEBUG: On Windows, constructed Python_LIBRARY path: ${Python_LIBRARY}")
endif()

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
        "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# -----------------------------------------------------------------------------
# Project-specific include and source directories for the ICS packet module.
# -----------------------------------------------------------------------------
set(ICS_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/icspacket/include")
set(ICS_SOURCE_DIR  "${CMAKE_CURRENT_SOURCE_DIR}/src/icspacket")

# Collect all base source files under "skeletons" for compilation. This globbing
# automatically pulls in all .c files. We can do that here, because the
# skeletons directory is designed to store only C source and header files.
file(GLOB ICS_BASE_SOURCES "${ICS_INCLUDE_DIR}/skeletons/*.c")

# -----------------------------------------------------------------------------
# Optional debugging flag:
#   Enable ASN.1 debugging output from asn1c-generated code.
#   Uncomment this line during development/troubleshooting.
# -----------------------------------------------------------------------------
# add_definitions(-DASN_EMIT_DEBUG=1)
