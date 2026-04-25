cmake_minimum_required(VERSION 3.20)
project(n_body_problem C)

set(CMAKE_C_STANDARD 11)

find_package(OpenMP REQUIRED)
find_package(BLAS REQUIRED)
find_package(Python3 REQUIRED)

# Regenerate config.h from bodies.json before every build.
add_custom_target(generate_config
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/generate_config.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Generating config.h from bodies.json"
    SOURCES ${CMAKE_SOURCE_DIR}/config.json
)

add_executable(n_body_problem main.c body.h config.h)
add_dependencies(n_body_problem generate_config)

if(OpenMP_C_FOUND)
    target_link_libraries(n_body_problem PUBLIC ${BLAS_LIBRARIES} OpenMP::OpenMP_C m)
endif()
