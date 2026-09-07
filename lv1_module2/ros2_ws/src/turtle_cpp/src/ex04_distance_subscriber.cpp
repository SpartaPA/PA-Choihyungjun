#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

class DistanceSubscriber : public rclcpp::Node
{
public:
    DistanceSubscriber() : Node("turtle_distance_subscriber")
    {
        sub_ = this->create_subscription<std_msgs::msg::Float32>(
            "/turtle_distance", 10,
            std::bind(&DistanceSubscriber::on_distance, this, std::placeholders::_1));

        RCLCPP_INFO(this->get_logger(), "turtle_distance_subscriber 시작");
    }

private:
    void on_distance(const std_msgs::msg::Float32::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "거리 = %.3f", msg->data);
    }

    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_;
};

int main(int argc, char ** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DistanceSubscriber>());
    rclcpp::shutdown();
    return 0;
}