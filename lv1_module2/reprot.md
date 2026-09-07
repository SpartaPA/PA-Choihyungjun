# 모듈 2 과제 - turtlesim 기반 C++·Python ROS2 패키지 개발

## 과제 소개

실제 로봇은 수십 개의 노드가 서로 메시지를 주고받으며 동작하고, 성능이 중요한 경로는 C++로, 개발 속도가 중요한 경로는 Python으로 쓰입니다. 이 과제는 C++ 빌드 체계를 세우는 것에서 시작해, ROS2 가 기본으로 제공하는 **turtlesim** 을 로봇 대신 놓고 그 로봇과 대화하는 패키지를 밑바닥부터 만듭니다. 거북이의 자세(`/turtle1/pose`)를 읽어 상태를 발행하고, 속도 명령(`/turtle1/cmd_vel`)으로 움직이고, 내장 서비스·액션을 호출하고, 커스텀 인터페이스로 경유점을 주고받고, launch 로 한 번에 기동한 뒤 RViz2·rosbag·pytest 로 검증하는 순서입니다.

## 사용 툴 또는 라이브러리 버전

- Ubuntu 22.04 LTS + **ROS2 Humble Hawksbill**
- `sudo apt install ros-humble-turtlesim` — turtlesim 노드와 그 인터페이스(`turtlesim/msg/Pose`, `turtlesim/srv/*`, `turtlesim/action/RotateAbsolute`)
- g++ 11 이상, C++17, CMake 3.22 이상
- Python 3.10, rclpy / rclcpp, colcon, ament_python / ament_cmake
- RViz2, rqt, rosbag2, pytest 7.0 이상
- turtlesim 은 **GUI 창**이 필요합니다. 네이티브 Ubuntu·가상머신은 그대로 되고, Windows 라면 WSL2 의 WSLg 로, 도커라면 X11 포워딩으로 띄우세요.
- 설치나 실행이 어려운 항목은 실행 불가 사유와 대체 확인 방법을 `report.md` 에 남기면 부분 인정합니다.

## 1. C++ 빌드 체계 세우기 - g++ 다중 파일 빌드와 CMake 전환

### 1. 수동 2단계 빌드 명령
- stop distance 빌드 및 실행 
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics$ g++ -Wall -std=c++17 stop_distance.cpp -o stop_distance
./stop_distance
속도[m/s]: 5
마찰계수: 3
정지 거리: 0.424737 m
```

- motor, main 수동 빌드
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics$ g++ -Wall -std=c++17 -c motor.cpp -o motor.o
g++ -Wall -std=c++17 -c main.cpp  -o main.o
g++ motor.o main.o -o main
./main
left-wheel: 3000 rpm
right-wheel: 6000 rpm
```


### 2. undefined reference 에러 메서지 출력 - 컴파일 에러와의 차이 설명

```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics$ g++ main.o -o main
/usr/bin/ld: main.o: in function `main':
main.cpp:(.text+0x64): undefined reference to `Motor::Motor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, float)'
/usr/bin/ld: main.cpp:(.text+0xce): undefined reference to `Motor::Motor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, float)'
/usr/bin/ld: main.cpp:(.text+0x102): undefined reference to `Motor::set_throttle(float)'
/usr/bin/ld: main.cpp:(.text+0x118): undefined reference to `Motor::set_throttle(float)'
/usr/bin/ld: main.cpp:(.text+0x124): undefined reference to `Motor::name[abi:cxx11]() const'
/usr/bin/ld: main.cpp:(.text+0x15a): undefined reference to `Motor::rpm() const'
/usr/bin/ld: main.cpp:(.text+0x18b): undefined reference to `Motor::name[abi:cxx11]() const'
/usr/bin/ld: main.cpp:(.text+0x1c1): undefined reference to `Motor::rpm() const'
collect2: error: ld returned 1 exit status
```

- 컴파일 에러는 cpp 파일을 컴파일 할떼 발생하고 문법 오류, 타입 불일치, 선언이 없는 경우 발생한다. 하지만 링크 에러는 컴파일된 .o 파일들을 합칠 때 발생하고 선언은 되어 있지만 정의가 되어 있지 않는 경우 발생한다. 
- motor.o를 제외하고 컴파일 하게 되면 motor.hpp 파일에 모터 클래스가 선언 되어있어서 main.o 컴파일까지는 문제가 없다. 하지만 링크 단계에서 링커가 Motor의 심블을 찾지 못하기 때문에 undefined reference 라는 링크 에러가 생기게 된다.

### 3. CMake 빌드 출력
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics/build$ cmake .. && make
-- The CXX compiler identification is GNU 11.4.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to: /home/pa33/git/project/lv1_module2/cpp_basics/build
[ 33%] Building CXX object CMakeFiles/main.dir/motor.cpp.o
[ 66%] Building CXX object CMakeFiles/main.dir/stop_distance.cpp.o
[100%] Linking CXX executable main
[100%] Built target main

```

### 4. 증분 빌드 시 재컴파일된 파일
- motor.cpp 수정후 make
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics/build$ make
Consolidate compiler generated dependencies of target main
[ 33%] Building CXX object CMakeFiles/main.dir/motor.cpp.o
[ 66%] Linking CXX executable main
[100%] Built target main
```


## 2. 현대 C++로 센서 계층 구현 - RAII·다형성·STL
### 1. 다형성 루프 출력
```shell
[lidar] x=4.71 y=5.21
[IMU] x=4.87 y=4.89
[lidar] x=5.09 y=5.24
[IMU] x=5.28 y=4.66
[lidar] x=5.19 y=4.55
[IMU] x=4.71 y=4.99
```
- 같은 s->read() 호출이 Lidar/Imu에 따라 다른 구현으로 분기

### 2. 스택 객체와 힙 객체의 소멸 시점 — 관찰 로그와 설명
```shell
내부 블록 집입
블록 안: 두 객체 살아있음
Lidar 소멸
Lidar 소멸
== 내부 블록 탈출 ==
```
- 스택 객체(`stack_lidar`)와 힙 객체(`make_unique<Lidar>`) 모두 블록 끝에서 소멸
- 소멸 순서는 선언의 역순 — 나중에 선언된 `heap_lidar` 의 unique_ptr 가 먼저 풀리고, 그다음 `stack_lidar` 가 소멸
- 스택 객체는 스코프를 벗어나면 자동 소멸하고, 힙 객체는 원래 `delete` 가 필요하지만 `unique_ptr`가 스코프 끝에서 자동으로 `delete` 해 주므로 둘 다 블록 끝에 소멸


### 3.가상 소멸자를 뺐을 때의 차이: 
```shell
[비가상 소멸자] BadBase* 로 delete:
BadBase 소멸
```
- `BadLidar 소멸`이 출력되지 않음 -> 기반 포인터로 delete 할 때 파생 소멸자가 호출되지 않음. 파생 클래스가 잡은 자원이 해제되지 않는 미정의 동작
- 컴파일 시 GCC 도 이를 경고
```shell
sensor.cpp:59:5: warning: deleting object of abstract class type ‘BadBase’ which has non-virtual destructor will cause undefined behavior [-Wdelete-non-virtual-dtor]
```
- 반면 `Sensor` 는 `virtual ~Sensor()` 라서 `Sensor*` 로 delete 해도 `~Lidar()` → `~Sensor()` 가 정상 호출된다 -> 다형적으로 쓸 기반 클래스는 소멸자를 virtual 로 선언해야 함

### 4. count_if 결과: 0.35 이내 기록 
목표점 (5.0, 5.0) 까지 거리 0.35 이내인 측정 기록:
```shell
목표(5,5) 0.35 이내 기록: 3 개
```
- 0.35 이내 기록: 3 개 


### 5. 누수 검출 결과 → 수정 후 결과 (검출 도구 출력 비교)

**(검출 전) `leak_demo()` — `new` 만 하고 `delete` 없음**
```shell
g++ -std=c++17 -fsanitize=address -g sensor.cpp -o sensor_asan
./sensor_asan
==9408==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 40 byte(s) in 5 object(s) allocated from:
    #0 ... operator new(unsigned long)
    #1 ... leak_demo() sensor.cpp:74
SUMMARY: AddressSanitizer: 40 byte(s) leaked in 5 allocation(s).
```
**(수정 후) `leak_demo()` 제거, `make_unique` 판(`no_leak_demo`)만 실행**
```shell
$ ./sensor_asan
(LeakSanitizer 출력 없음 — 누수 0건, 종료코드 0)
```
- `new`/`delete` 수동 관리에서는 delete 누락으로 40바이트(5건)가 누수됐고, `make_unique`(RAII)로 바꾸자 스코프 끝에서 자동 해제되어 `Lidar 소멸` 이 5번 찍히고 ASan 누수 0건.



## 3. rcply 노드 작성 - 거북이 상태 발행자와 구독자
### 1. /turtle1/pose 필드 구성
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/cpp_basics/ros_ws/src$ ros2 topic echo /turtle1/pose 
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
--- ...
```

### 2. ros2 topic hz /turtle_distance 출력
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 topic hz /turtle_distance 
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00012s window: 12
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00019s window: 22
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00017s window: 33
```
- 평균 10Hz

### 3. 구독자 경고 로그
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 run turtle_py distance_subscriber 
[INFO] [1788492820.038966807] [turtle_distance_subcriber]: distance_watcher up
[WARN] [1788492857.161508438] [turtle_distance_subcriber]: 경고: 원점거리 2.56 m > 임계 2.50 m
[WARN] [1788492857.261374872] [turtle_distance_subcriber]: 경고: 원점거리 2.78 m > 임계 2.50 m
[WARN] [1788492857.361348824] [turtle_distance_subcriber]: 경고: 원점거리 2.98 m > 임계 2.50 m
[WARN] [1788492857.461417491] [turtle_distance_subcriber]: 경고: 원점거리 3.17 m > 임계 2.50 m
[WARN] [1788492857.561619577] [turtle_distance_subcriber]: 경고: 원점거리 3.36 m > 임계 2.50 m
[WARN] [1788492857.661627303] [turtle_distance_subcriber]: 경고: 원점거리 3.58 m > 임계 2.50 m
[WARN] [1788492857.762119786] [turtle_distance_subcriber]: 경고: 원점거리 3.78 m > 임계 2.50 m
[WARN] [1788492857.861493056] [turtle_distance_subcriber]: 경고: 원점거리 3.97 m > 임계 2.50 m
[WARN] [1788492857.961447501] [turtle_distance_subcriber]: 경고: 원점거리 4.00 m > 임계 2.50 m
[WARN] [1788492858.061260695] [turtle_distance_subcriber]: 경고: 원점거리 4.00 m > 임계 2.50 m
[WARN] [1788492858.161106900] [turtle_distance_subcriber]: 경고: 원점거리 4.00 m > 임계 2.50 m
```

### 4, 구독자 2개 동시 수신 확인
- 터미널 1
```
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 run turtle_py distance_subscriber 
[INFO] [1788692169.739261496] [turtle_distance_subcriber]: distance_watcher up
[WARN] [1788692228.377901676] [turtle_distance_subcriber]: 경고: 원점거리 2.69 m > 임계 2.50 m
[WARN] [1788692228.477967978] [turtle_distance_subcriber]: 경고: 원점거리 2.88 m > 임계 2.50 m
[WARN] [1788692228.577518610] [turtle_distance_subcriber]: 경고: 원점거리 3.07 m > 임계 2.50 m
[WARN] [1788692228.677718330] [turtle_distance_subcriber]: 경고: 원점거리 3.26 m > 임계 2.50 m

```

- 터미널 2
```
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 run turtle_py distance_subscriber 
[INFO] [1788692169.739261496] [turtle_distance_subcriber]: distance_watcher up
[WARN] [1788692228.377901676] [turtle_distance_subcriber]: 경고: 원점거리 2.69 m > 임계 2.50 m
[WARN] [1788692228.477967978] [turtle_distance_subcriber]: 경고: 원점거리 2.88 m > 임계 2.50 m
[WARN] [1788692228.577518610] [turtle_distance_subcriber]: 경고: 원점거리 3.07 m > 임계 2.50 m
[WARN] [1788692228.677718330] [turtle_distance_subcriber]: 경고: 원점거리 3.26 m > 임계 2.50 m
```

### 5. 정사각형 주행 캡처 (turtlesim 화면)

![turtle_square](/lv1_module2/screenshots/turtle_square.png)

### 6. Ctrl+C 정상 종료 화면 (출력)
```shell
^C[INFO] [1788692349.454678641] [turtle_distance_publisher]: Ctrl+c - 정상 정료
Failed to publish log message to rosout: publisher's context is invalid, at ./src/rcl/publisher.c:389
```

## 4. rclcpp 노드 작성 - C++ 발행자와 구독자
### 1. colcon build 성공 출력
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ colcon build --packages-select turtle_cpp
Starting >>> turtle_cpp
Finished <<< turtle_cpp [5.07s]                     

Summary: 1 package finished [5.20s]
```

### 2. rclpy 발행에서 rclcpp 구독으로 이어진 로그
- 터미널 1 (rclpy 발행)
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 run turtle_py distance_publisher 
[INFO] [1788501584.270244830] [turtle_distance_publisher]: turtle_distance_publisher 시작: publish_rate=10.0 Hz
```

터미널 2 (rclcpp 구독)
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/git/project/lv1_module2/ros2_ws$ ros2 run turtle_cpp distance_subscriber 
[INFO] [1788696954.229033733] [turtle_distance_subscriber]: turtle_distance_subscriber 시작
[INFO] [1788696954.265802985] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.365798008] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.465894431] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.565764625] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.665873655] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.765822609] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.865929046] [turtle_distance_subscriber]: 거리 = 4.477
[INFO] [1788696954.965940005] [turtle_distance_subscriber]: 거리 = 4.282
[INFO] [1788696955.065931647] [turtle_distance_subscriber]: 거리 = 4.118
[INFO] [1788696955.166045516] [turtle_distance_subscriber]: 거리 = 3.956
[INFO] [1788696955.266075710] [turtle_distance_subscriber]: 거리 = 3.798
[INFO] [1788696955.365789293] [turtle_distance_subscriber]: 거리 = 3.616
[INFO] [1788696955.466175510] [turtle_distance_subscriber]: 거리 = 3.465

```

### 3. rclpy와 rclcpp 대응 관계표

| 구분 | rclpy (Python) | rclcpp (C++) |
| :--- | :--- | :--- |
| 노드 생성 | `rclpy.init()` → `class DistancePublisher(Node)`, `super().__init__('...')` | `rclcpp::init()` → `class DistancePublisher : public rclcpp::Node`, `: Node("...")` |
| 타이머 | `self.create_timer(1.0/rate, self.on_timer)` | `this->create_wall_timer(duration<double>(1.0/rate), std::bind(&::on_timer, this))` |
| 콜백 | 멤버 메서드를 그대로 전달 (`self.on_pose`) | `std::bind(&Class::on_pose, this, _1)` 로 바인딩 |
| 종료 | `try/except`(KeyboardInterrupt) → `destroy_node()` → `rclpy.shutdown()` | `rclcpp::spin()` 이 SIGINT 처리 후 반환 → `rclcpp::shutdown()` |



## 10. 시각화·기록·테스트로 검증하기
### 1. rqt_graph 캡처 — 데이터 미수신 진단 절차 (단계별)
![rqt_graph](/lv1_module2/screenshots/rqt_graph.png)


- 데이터 미수신 진단 절차 : ① ros2 topic hz 로 흐름 확인 → ② ros2 topic list 로 토픽 존재 확인 → ③ ros2 node list 로 발행 노드 살아있는지 → ④ ros2 topic info -v 로 pub/sub 개수·QoS → ⑤ 상류(/turtle1/pose) 부터 역추적

### 2. RViz2 TF + 경유점 마커 캡처
![tf_marker]



### 3.ros2 bag play 재생 중 구독자 로그 — 기록된 토픽과 메시지 수: ___

### 4. pytest 통과 출력 — 작성한 테스트 3개의 의도

### 5. 함수를 틀리게 바꿨을 때 실패 출력

### 6. 예외 처리·logging 동작 확인: ___