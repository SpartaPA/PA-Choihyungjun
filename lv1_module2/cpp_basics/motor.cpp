// motor.cpp - Motor 클래스 구현
#include "motor.hpp"
#include <cmath>
#include <algorithm>

Motor::Motor(std::string name, float max_rpm)
    : name_(std::move(name)), max_rpm_(max_rpm) {}

void Motor::set_throttle(float t){
    throttle_ = std::clamp(t, 0.0f, 1.0f);
}

float Motor::rpm() const {
    // 수정: 0.1 rpm 단위로 반올림
    float r = throttle_ * max_rpm_;
    return std::round(r * 10.0f) / 10.0f;
}
 
const std::string& Motor::name() const {
    return name_;
}
 