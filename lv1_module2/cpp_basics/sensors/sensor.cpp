#include <iostream>
#include <memory>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <string>
#include <cmath>
#include <unordered_map>

// 측정값 하나(센서가 읽은 위치)
struct Measurement
{
    std::string sensor;
    double x;
    double y;
};

static double rand_coord(){
    return 4.5 + (std::rand() % 101 / 100.0);
} 

class Sensor {
    public:
    virtual ~Sensor() = default;    // 가상 소멸자 선언
    virtual Measurement read() = 0; // 순수 가상 : 측정값 리턴
    virtual std::string name() const = 0;
};

class Lidar: public Sensor{
    public:
    ~Lidar() override {std::cout <<"Lidar 소멸" << std::endl; }
    Measurement read() override{ return {"lidar", rand_coord(), rand_coord()}; }
    std::string name() const override { return "Lidar"; }
};

class Imu: public Sensor{
    public:
    ~Imu() override {std::cout<< "Imu 소멸" << std::endl ; }
    Measurement read() override{ return{"IMU", rand_coord(), rand_coord()}; }
    std::string name() const override { return "IMU"; }
};

// === 가상 소멸자 유무 비교용 (일부러 비가상) ===
class BadBase {
public:
    ~BadBase() { std::cout << "BadBase 소멸\n"; }   // ← virtual 아님!
    virtual void ping() = 0;
};
class BadLidar : public BadBase {
public:
    ~BadLidar() { std::cout << "BadLidar 소멸\n"; }
    void ping() override {}
};

// 기반 포인터로 delete → 비가상이면 파생 소멸자가 호출되지 않음
void non_virtual_dtor_demo() {
    std::cout << "\n[비가상 소멸자] BadBase* 로 delete:\n";
    BadBase* p = new BadLidar();
    delete p;   // "BadBase 소멸" 만 출력 → BadLidar 소멸자 누락 (파생 자원 누수, UB)
}


// 함수 템플릿 : 값 범위 안으로 자르기
template <typename T>
T clamp(T v, T lo, T hi){
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

// 누수 재현 : new 만 하고 delete 안 함 → ASan/valgrind 로 검출됨
void leak_demo(){
    for (int i = 0; i<5; ++i){
        Sensor* s = new Lidar();  // delete 없음 → 누수 (소멸자도 안 불림)
        (void)s;
    }
}

// 누수 수정판 : make_unique 는 스코프 끝에서 자동 해제 → "Lidar 소멸" 출력됨
void no_leak_demo(){
    for (int i = 0; i<5; ++i){
        auto s = std::make_unique<Lidar>();
        (void)s;
    }
}

int main(){
    std::srand(42);   // 시드 고정 → 매번 같은 측정값, count 재현 가능
    std::cout << "내부 블록 집입" << std::endl;
    {
        Lidar stack_lidar;
        auto heap_lidar = std::make_unique<Lidar>();  // 힙(unique_ptr 소유)
        std::cout << "블록 안: 두 객체 살아있음\n";
    }  // 블록 끝: heap_lidar → stack_lidar 순으로 소멸
    std::cout << "== 내부 블록 탈출 ==\n\n";

    // === 다형성 루프 + unordered_map + 측정 로그 ===
    std::vector<std::unique_ptr<Sensor>> sensors;
    sensors.push_back(std::make_unique<Lidar>());
    sensors.push_back(std::make_unique<Imu>());

    std::unordered_map<std::string, Measurement> latest;  // 센서별 최근 측정값
    std::vector<Measurement> log;                         // 전체 측정 로그

    for (int round = 0; round < 3; ++round) {
        for (const auto& s : sensors) {       // 다형성: 기반 포인터로 read()
            Measurement m = s->read();
            std::cout << "[" << m.sensor << "] x=" << m.x << " y=" << m.y << "\n";
            latest[s->name()] = m;            // 최근값 갱신
            log.push_back(m);                 // 로그 적재
        }
    }

    // === count_if: 목표점까지 거리 0.35 이내인 기록 개수 ===
    const double gx = 5.0, gy = 5.0;
    int near = std::count_if(log.begin(), log.end(),
        [&](const Measurement& m) {
            return std::hypot(m.x - gx, m.y - gy) <= 0.35;
        });
    std::cout << "\n목표(" << gx << "," << gy << ") 0.35 이내 기록: " << near << " 개\n";

    // === unordered_map 조회 ===
    std::cout << "Lidar 최근값: x=" << latest["Lidar"].x
              << " y=" << latest["Lidar"].y << "\n";

    // === clamp 템플릿: double 속도 + int 픽셀 양쪽에 적용 ===
    double speed = clamp(3.7, 0.0, 2.0);   // 2.0 으로 잘림
    int    pixel = clamp(300, 0, 255);     // 255 로 잘림
    std::cout << "clamp: speed=" << speed << ", pixel=" << pixel << "\n\n";

    // === 메모리 누수 시연 ===
    leak_demo();     
    no_leak_demo();  
    non_virtual_dtor_demo();

    std::cout << "\n== main 종료: sensors 벡터 소멸 시작 ==\n";
    return 0;
}