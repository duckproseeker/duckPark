#ifndef __PERSION_HXX__
#define __PERSION_HXX__

#include<string>
#include<odb/core.hxx>

//表明接下来的类是数据库相关的类
#pragma db model version(1, 1)
#pragma db object
class Persion
{
public:
    Persion(const std::string first, const std::string last, unsigned short age)
    : _first(first), _last(last), _age(age){}
    const std::string first() const
    {
        return _first;
    }
    const std::string last() const
    {
        return _last;
    }
    unsigned short age() const
    {
        return _age;
    }
    unsigned short id() const
    {
        return _id;
    }
    void age(unsigned short num)
    {
        _age = num;
    }

private:
    Persion(){};

    //友元可以访问类的private成员
    friend class odb::access;

    //表明接下来的字段是持久化类的标识符字段
    #pragma db id auto
    unsigned short _id;

    std::string _first;
    std::string _last;
    unsigned short _age;
};

//视图
#pragma db view object(Persion)
struct Persion_stat
{
    #pragma db column("count(" + Persion::_id + ")")
    std::size_t count;

    #pragma db column("min(" + Persion::_age + ")")
    std::size_t min_age;

    #pragma db column("max(" + Persion::_age + ")")
    std::size_t max_age;
};

#endif