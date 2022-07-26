#include "pose_extrapolator.h"

#include <iostream>


PoseExtrapolator::PoseExtrapolator()
: pose0_(0, 0, 0)
{

}

void PoseExtrapolator::AddPose(double timestamp, const Pose2D &pose)
{
    poseQueue.push(std::make_pair(timestamp, pose));
}

bool PoseExtrapolator::ExtrapolatePose(double timestamp, Pose2D &pose)
{
    //如果插值时间点不在已有区间内，返回false
    if((timestamp < poseQueue.front().first && timestamp < time0_) || timestamp > poseQueue.back().first)
    {
        return false;
    }

    //std::cout << poseQueue.front().first << poseQueue.front().second <<std::endl;

    //寻找比当前时间点大的值
    while(poseQueue.front().first <= timestamp)
    {
        pose0_ = poseQueue.front().second;
        time0_ = poseQueue.front().first;
        poseQueue.pop();
    }

    Pose2D pose1 = poseQueue.front().second;
    double time1 = poseQueue.front().first;


    double time_scale = (timestamp - time0_) / (time1 - time0_);

    pose = pose0_ * (pose0_.inverse() * pose1 * time_scale);

    return true;
 
}
