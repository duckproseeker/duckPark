#ifndef __PICTURE_HXX__
#define __PICTURE_HXX__

#include <string>
#include <odb/core.hxx>

#pragma db model version(1, 1)
#pragma db object

class Picture
{

public:
    Picture(std::string name, std::size_t bytes, time_t time, std::string path, std::string owner, std::string resolution = "1080p", std::string type = "jpg")
    : name_(name)
    , bytes_(bytes)
    , timeUpload_(time)
    , timeModify_(time)
    , path_(path)
    , resolution_(resolution)
    , type_(type)
    , owner_(owner)
    {

    }

    void modify(time_t time)
    {
        timeModify_ = time;
    }


private:

    friend class odb::access;

    #pragma db id auto
    unsigned short id_;

    std::string name_;

    std::size_t bytes_;

    std::string resolution_;

    std::string type_;

    std::string path_;

    time_t timeUpload_;

    time_t timeModify_;

    std::string owner_;

};


#endif