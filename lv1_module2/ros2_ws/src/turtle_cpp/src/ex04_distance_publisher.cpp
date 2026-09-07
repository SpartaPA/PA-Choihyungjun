#include <chrono>
#include <cmath>
#include <optional>
#include <memory>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"
#include "turtlesim/msg/pose.hpp"

using namespace std::chrono_literals;


class DistancePublisher : public rclcpp::Node
{
public:
    DistancePublisher() : Node("turtle_distance_publisher")
    {
        // 파라미터: 발행 주기
        rcl_interfaces::msg::ParameterDescriptor desc;
        desc.description = "/turtle_distance 발행 주기 [Hz], 0 보다 커야 함";
        double rate = this->declare_parameter<double>("publish_rate", 10.0, desc);

        // 구독: 최신 pose 저장만
        pose_sub_ = this->create_subscription<turtlesim::msg::Pose>(
            "turtle1/pose", 10,
            std::bind(&DistancePublisher::on_pose, this, std::placeholders::_1));

        // 발행
        pub_ = this->create_publisher<std_msgs::msg::Float32>("/turtle_distance", 10);

        // 타이머: 계산 + 발행
        timer_ = this->create_wall_timer(
            std::chrono::duration<double>(1.0 / rate),
            std::bind(&DistancePublisher::on_timer, this));

        // 파라미터 변경 콜백
        param_cb_ = this->add_on_set_parameters_callback(
            std::bind(&DistancePublisher::on_set_parameters, this, std::placeholders::_1));

        RCLCPP_INFO(this->get_logger(),
                    "turtle_distance_publisher 시작: publish_rate=%.1f Hz", rate);
    }

private:
    void on_pose(const turtlesim::msg::Pose::SharedPtr msg)  // 저장만
    {
        if (!start_) {
            start_ = *msg;
        }
        latest_ = *msg;
    }

    void on_timer()  // 계산 + 발행
    {
        if (!latest_) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                 "아직 /turtle1/pose 를 받지 못했습니다");
            return;
        }
        double d = std::hypot(latest_->x - start_->x, latest_->y - start_->y);
        std_msgs::msg::Float32 out;
        out.data = static_cast<float>(d);
        pub_->publish(out);
    }

    // publish_rate 검증 후 타이머 재생성 (타이머는 주기 변경 API 가 없어 파괴 후 재생성)
    rcl_interfaces::msg::SetParametersResult
    on_set_parameters(const std::vector<rclcpp::Parameter> & params)
    {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        for (const auto & p : params) {
            if (p.get_name() != "publish_rate") {
                continue;
            }
            if (p.get_type() != rclcpp::ParameterType::PARAMETER_DOUBLE) {
                result.successful = false;
                result.reason = "publish_rate 는 double 이어야 합니다 (예: 5.0)";
                return result;
            }
            double v = p.as_double();
            if (v <= 0.0) {
                result.successful = false;
                result.reason = "publish_rate 는 0 보다 커야 합니다";
                return result;
            }
            timer_ = this->create_wall_timer(
                std::chrono::duration<double>(1.0 / v),
                std::bind(&DistancePublisher::on_timer, this));
            RCLCPP_INFO(this->get_logger(),
                        "publish_rate 변경 → %.1f Hz (타이머 재생성)", v);
        }
        return result;
    }

    std::optional<turtlesim::msg::Pose> start_;   // 시작점
    std::optional<turtlesim::msg::Pose> latest_;  // 최신 pose
    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr pose_sub_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    OnSetParametersCallbackHandle::SharedPtr param_cb_;
};

int main(int argc, char ** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DistancePublisher>());
    rclcpp::shutdown();
    return 0;
}