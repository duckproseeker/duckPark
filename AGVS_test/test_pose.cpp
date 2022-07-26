#include"pose_extrapolator.h"

#include <iostream>

int main(int argc, char* argv[])
{

    Pose2D p1(0, 0, 0);
    Pose2D p2(1, 0, 0);
    Pose2D p3(1, 1, 0);
    Pose2D p4(2, 2, 0);
    Pose2D p5(2, 3, 1);
    Pose2D p6(3, 3, 1);

    PoseExtrapolator poseExtrapolator;
    poseExtrapolator.AddPose(0, p1);
    poseExtrapolator.AddPose(1, p2);
    poseExtrapolator.AddPose(2, p3);
    poseExtrapolator.AddPose(3, p4);
    poseExtrapolator.AddPose(4, p5);
    poseExtrapolator.AddPose(5, p6);

    Pose2D exPose(0, 0, 0);

    double time;
    while(std::cin >> time)
    {
        if(poseExtrapolator.ExtrapolatePose(time, exPose))
        {
            std::cout << "期望位姿：" << exPose << std::endl;
        }
        
        else
        {
            std::cout << "error!" << std::endl;
        }

    }

}
