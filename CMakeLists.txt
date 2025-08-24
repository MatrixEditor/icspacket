cmake_minimum_required(VERSION 3.15...3.26)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C)

# This CMake file is meant to be executed using 'scikit-build-core'.
if (NOT SKBUILD)
  message(WARNING "\
  This CMake file is meant to be executed using 'scikit-build-core'.
  Running it directly will almost certainly not produce the desired
  result. If you are a user trying to install this package, use the
  command below, which will install all necessary build dependencies,
  compile the package in an isolated environment, and then install it.
  =====================================================================
   $ pip install .
  =====================================================================
  If you are a software developer, and this is your own package, then
  it is usually much more efficient to install the build dependencies
  in your environment once and use the following command that avoids
  a costly creation of a new virtual environment at every compilation:
  =====================================================================
   $ pip install pybind11 scikit-build-core[pyproject]
   $ pip install --no-build-isolation -ve .
  =====================================================================
  You may optionally add -Ceditable.rebuild=true to auto-rebuild when
  the package is imported. Otherwise, you need to rerun the above
  after editing C++ files.")
endif()

include(cmake/icspacket-common.cmake)
include(cmake/icspacket-defs.cmake)

# -----------------------------------------------------------------------------
#                     icspacket ASN.1 extensions
# -----------------------------------------------------------------------------
add_asn1_extension(
  NAME _iso8823
  DIR "${ICS_SOURCE_DIR}/proto/iso_pres/_iso8823"
  INSTALL "proto/iso_pres"
)