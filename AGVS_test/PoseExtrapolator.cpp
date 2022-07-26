// #include "pose_extrapolator.h"

// #include <iostream>


// PoseExtrapolator::PoseExtrapolator()
// {

// }
// // PoseExtrapolator::PoseExtrapolator(std::map<double, Pose2D> &initMap)
// //     : pose2D_map_(initMap)
// // {

// // }

// void PoseExtrapolator::AddPose(double timestamp, const Pose2D &pose)
// {
//     pose2D_map_.insert(std::pair<double, Pose2D>(timestamp, pose));
// }

// bool PoseExtrapolator::ExtrapolatePose(double timestamp, Pose2D &pose)
// {
//     if (timestamp >= pose2D_map_.begin()->first && timestamp <= (--pose2D_map_.end())->first)
//     {
//         auto it = pose2D_map_.find(timestamp);
//         //先判断插值器是否包含当前时间的位姿
//         if (it != pose2D_map_.end())
//         {
//             //找到。直接返回
//             //pose = pose2D_map_[timestamp];
//             //const Pose2D & t = pose2D_map_[timestamp]
//             //pose = t;
//             pose = it->second;
//             return true;
//         }

//         auto next_poseIter = pose2D_map_.begin();
//         auto front_poseIter = pose2D_map_.begin();

//         //寻找插入位姿的前一个时间点与后一个时间点
//         while (next_poseIter->first < timestamp)
//         {
//             front_poseIter = next_poseIter;
//             next_poseIter++;
//         }

//         //利用公式计算当前位姿
//         double time_scale = (timestamp - front_poseIter->first) / (next_poseIter->first - front_poseIter->first);

//         std::cout << "time_scale: " << time_scale << std::endl;

//         pose =  front_poseIter->second * (front_poseIter->second.inverse() * next_poseIter->second * time_scale);

//         //std::cout << front_poseIter->second << "--->"  << next_poseIter->second << std::endl;
//         return true;

//     }

//     else
//     {
//         std::cout << "error!" << std::endl;

//         return false;
//     }

// }

// void PoseExtrapolator::display()
// {
//     for (auto timePose : pose2D_map_)
//     {
//         std::cout << "time: " << timePose.first
//                   << " pose: " << timePose.second
//                   << std::endl;
//     }
// }
