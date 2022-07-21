#include"ros/ros.h"
#include"std_msgs/String.h"
#include<sstream>

int main(int argc, char *argv[])
{
    ros::init(argc, argv, "talker");

    //定义节点句柄
    ros::NodeHandle n;
    
    //定义发布者对象，<>里写该发布者消息类型
    //（）里写话题名字，和缓存区大小
    ros::Publisher chatter_pub = n.advertise<std_msgs::String>("chatter", 1000);

    //定义发布频率
    ros::Rate loop_rate(10);

    int count = 0;

    while(ros::ok())
    {
        //定义ros里的string类型的消息message对象
        std_msgs::String msg;

        std::stringstream ss;

        //将需要发布的消息存到ss里
        ss << "hello world! " << count;

        //ss赋给msg.data
        msg.data = ss.str();

        //设置ROSINFO输出格式
        ROS_INFO("%s", msg.data.c_str());

        //核心：发布
        chatter_pub.publish(msg);

        ros::spinOnce();

        loop_rate.sleep();
        ++count;
    }

    return 0;
}

