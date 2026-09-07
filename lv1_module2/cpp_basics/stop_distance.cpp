// stop_distance.cpp — 로봇의 제동(정지) 거리 계산
//
// 물리: 바퀴와 바닥 사이 마찰이 유일한 제동력이라고 보면
//   감속도 a = mu * g   (mu: 마찰계수, g: 중력가속도)
//   운동에너지 (1/2)m v^2 이 마찰일 (mu m g d) 로 모두 소모되어 정지하므로
//   d = v^2 / (2 * mu * g)
//
// 빌드: g++ -Wall -std=c++17 stop_distance.cpp -o stop_distance
// 실행: ./stop_distance <속도[m/s]> <마찰계수>
//   인자를 안 주면 값을 직접 입력받는다.

#include <iostream>

namespace {
    constexpr float gravity = 9.81f;
}

float stop_distance(float v, float mu){
    float s_d = v * v / (2 * mu * gravity);
    return s_d;
}

int main(int argc, char* argv[]){
    float v = 0.0f;
    float mu = 0.0f;

    if (argc == 3) {
        try {
            v  = std::stof(argv[1]);
            mu = std::stof(argv[2]);
        } catch (const std::exception&) {
            std::cerr << "오류: 인자를 숫자로 변환할 수 없습니다.\n";
            return 1;
        }
    } else if (argc == 1) {
        std::cout << "속도[m/s]: ";
        std::cin >> v;
        std::cout << "마찰계수: ";
        std::cin >> mu;
        if (!std::cin) {
            std::cerr << "오류: 잘못된 입력입니다.\n";
            return 1;
        }
    } else {
        std::cerr << "사용법: " << argv[0] << " <속도[m/s]> <마찰계수>\n";
        return 1;
    }

    if (mu <= 0.0f) {
        std::cerr << "오류: 마찰계수는 0보다 커야 합니다.\n";
        return 1;
    }
    if (v < 0.0f) {
        std::cerr << "오류: 속도는 음수일 수 없습니다.\n";
        return 1;
    }

    float d = stop_distance(v, mu);
    std::cout << "정지 거리: " << d << " m\n";
    return 0;
}