cmake_minimum_required(VERSION 3.10)
project(cpp_basics CXX)

# C++17 표준 설정
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 컴파일 경고 옵션 (-Wall)
add_compile_options(-Wall)

# 실행 파일명 및 소스 파일 지정
add_executable(main
    motor.cpp
    main.cpp
    stop_distance.cpp
)
