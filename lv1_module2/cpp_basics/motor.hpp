// motor.hpp - Motor 클래스 정의
#ifndef MOTOR_HPP
#define MOTOR_HPP

#include <string>

class Motor{
public:
    Motor(std::string name, float max_rpm);

    void set_throttle(float t);
    float rpm() const;
    const std::string& name() const;
private:
    std::string name_;
    float max_rpm_;
    float throttle_ = 0.0f;
};

#endif // MOTOR_HPP
