// listener.cpp
#include "ros/ros.h"
#include "std_msgs/String.h"

// 回调函数
void chatterCallback(const std_msgs::String::ConstPtr& msg)
{
  ROS_INFO("I heard: [%s]", msg->data.c_str());
}

int main(int argc, char **argv)
{
  ros::init(argc, argv, "listener");

  ros::NodeHandle n;

  ros::Subscriber sub = n.subscribe("chatter", 1000, chatterCallback); //()里写订阅的话题名字，缓存区大小，收到消息后执行的回调函数

  ros::spin();

  return 0;
}


