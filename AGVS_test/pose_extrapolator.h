#ifndef POSE_EXTRAPOLATOR_H
#define POSE_EXTRAPOLATOR_H

#include <cmath>
#include <queue>
#include <assert.h>
#include <queue>
//#include <map>
#include <ostream>

#ifndef M_PI
#define M_PI 3.14159265
#endif

class Pose2D {
 public:
  Pose2D(double x, double y, double yaw) {
    x_ = x;
    y_ = y;
    yaw_ = yaw;
  }

  static double FormatAngle(double angle) {
    while (angle > M_PI) angle -= 2. * M_PI;
    while (angle < -M_PI) angle += 2. * M_PI;
    return angle;
  }

  Pose2D inverse() const {
    double yaw = -yaw_;
    double sin = std::sin(yaw);
    double cos = std::cos(yaw);
    double x = -x_ * cos + y_ * sin;
    double y = -x_ * sin - y_ * cos;
    return Pose2D(x, y, yaw);
  }

  // Pose2D operator=(const Pose2D& rhs)
  // {
  //   this->x_ = rhs.x_;
  //   this->y_ = rhs.y_;
  //   this->yaw_ = rhs.yaw_;
  //   return *this;
  // }

  friend Pose2D operator*(const Pose2D& lhs, const Pose2D& rhs) {
    double x =
        lhs.x_ + rhs.x_ * std::cos(lhs.yaw_) - rhs.y_ * std::sin(lhs.yaw_);
    double y =
        lhs.y_ + rhs.x_ * std::sin(lhs.yaw_) + rhs.y_ * std::cos(lhs.yaw_);
    double yaw = lhs.yaw_ + rhs.yaw_;
    return Pose2D(x, y, yaw);
  }

  friend Pose2D operator*(const Pose2D& lhs, double scale) {
    return Pose2D(lhs.x_ * scale, lhs.y_ * scale, Pose2D::FormatAngle(lhs.yaw_ * scale));
  }

  friend std::ostream &operator<<(std::ostream &output, const Pose2D &pose){
    output << "(" << pose.x_ << " ,"
           << pose.y_ << " ,"
           << pose.yaw_ << ")";

    return output;
  }

  double x_;
  double y_;
  double yaw_;
};


class PoseExtrapolator {
 public:
  PoseExtrapolator();

  // PoseExtrapolator(std::map<double, Pose2D> &initMap);

  /**
   * 往插值器里添加某个时间点timestamp下的小车位姿pose
   */
  void AddPose(double timestamp, const Pose2D& pose);

  /**
   * 基于已插入的位姿计算在某个时刻对应的期望位姿，这里认为插值只会一直往前插值，
   * 也就是每次调用这个函数的timestamp参数一定比上一次大。
   *
   * 这里需要先根据timestamp找到最近的可用于插值的区间[t0,t1]，其中t0 <
   * timestamp < t1 然后找到这个区间保存的位姿[pose0, pose1]，
   * 用这两个pose计算速度v = (pose1 - pose0) / (t1 - t0) // pose0.inverse() * pose1 / (t1 - t0)
   * 然后根据速度v计算在这个时间点的实际位置：
   * pose = pose0 + v * (timestamp - t0)  // pose0 * (v * (timestamp - t0))
   * 然后返回true
   *
   * 如果没有找到对应区间则返回false
   */
  bool ExtrapolatePose(double timestamp, Pose2D& pose);

  //void display();


 private:
  /**
   * 这里加上需要额外保存的一些信息
   */
  //std::map<double, Pose2D> pose2D_map_;  
  
  std::queue<std::pair<double, Pose2D>> poseQueue;

  Pose2D pose0_;
  double time0_;

};

#endif
