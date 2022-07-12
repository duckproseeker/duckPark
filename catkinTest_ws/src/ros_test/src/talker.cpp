// talker.cpp
#include "ros/ros.h"
#include "std_msgs/String.h"
#include <sstream>

int main(int argc, char **argv)
{

  ros::init(argc, argv, "talker");

  ros::NodeHandle n;   //定义节点句柄

  ros::Publisher chatter_pub = n.advertise<std_msgs::String>("chatter", 1000); //定义发布者对象，<>里写该发布者消息类型，()里写话题名字，和缓存区大小；

  ros::Rate loop_rate(10);  //定义发布频率频率；

  int count = 0;
  
  while (ros::ok())
  {
    std_msgs::String msg;  //定义ros里的string类型的消息message对象；

    std::stringstream ss;
    ss << "hello world " << count;//将需要发布的消息存到ss里；
    msg.data = ss.str(); //将ss赋给msg.data;

    ROS_INFO("%s", msg.data.c_str()); //设置ROSINFO输出格式

    chatter_pub.publish(msg); //核心：发布

    ros::spinOnce();  //与回调相关；

    loop_rate.sleep();
    ++count;
  }
  return 0;
}

