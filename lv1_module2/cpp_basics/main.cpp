// main.cpp — Motor 클래스 사용 예시
#include "motor.hpp"
#include <iostream>
 
int main() {
    Motor left("left-wheel", 6000.0f);
    Motor right("right-wheel", 6000.0f);
 
    left.set_throttle(0.5f);
    right.set_throttle(1.2f);   // 1.0 초과 → clamp 되어 1.0
 
    std::cout << left.name()  << ": "  << left.rpm()  << " rpm\n";
    std::cout << right.name() << ": " << right.rpm() << " rpm\n";
    return 0;
}
 