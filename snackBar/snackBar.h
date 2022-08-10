#ifndef __SNACKBAR_H__
#define __SNACKBAR_H__

#include "commandParse.h"

#include <iostream>
#include <string>
#include <map>

class SnackBar
{

public:

    virtual void run() = 0;

    virtual int sum(std::string&) = 0;

    virtual ~SnackBar(){}

// private:

//     CommandParse CommandParse_; 
};

class DrinkBar : public SnackBar
{
public:
    DrinkBar()
    {
        commodity_[1] = 5;
        commodity_[2] = 6;
        commodity_[3] = 5;
        commodity_[4] = 8;
    }

    void run() override
    {
        std::cout << "饮品店有如下商品可以选择：" << std::endl
                  << "巧克力冰淇淋 5元；" << std::endl
                  << "冰镇酸梅汤 6元；" << std::endl
                  << "柠檬汁 5元；" << std::endl
                  << "珍珠奶茶 8元；" << std::endl; 
    }

    int sum(std::string& command) override
    {
        parse_ = new CommandParse(command);
        std::map<int, int> id_num = parse_->handle();

        int price = 0;
        for(auto elem : id_num)
        {
            price = price + commodity_[elem.first] * elem.second;
        }

        delete parse_;

        return price;
    }

private:

    std::map<int, int> commodity_;
    CommandParse* parse_;
};


class BarbecueBar : public SnackBar
{
public:
    
    BarbecueBar()
    {
        commodity_[1] = 5;
        commodity_[2] = 3;
        commodity_[3] = 4;
        commodity_[4] = 2;
    }

    void run() override
    {
        std::cout << "烧烤店有如下商品可以选择：" << std::endl
                  << "烤羊肉 5元；" << std::endl
                  << "烤鸡柳 3元；" << std::endl
                  << "烤牛肉串 4元；" << std::endl
                  << "烤五花肉 2元；" << std::endl; 
    }

    int sum(std::string& command) override
    {
        parse_ = new CommandParse(command);
        std::map<int, int> id_num = parse_->handle();

        int price = 0;
        for(auto elem : id_num)
        {
            price = price + commodity_[elem.first] * elem.second;
        }

        delete parse_;

        return price;
    }

private:

    std::map<int, int> commodity_;
    CommandParse* parse_;

};


class SweetBar : public SnackBar
{
public:

    SweetBar()
    {
        commodity_[1] = 10;
        commodity_[2] = 5;
        commodity_[3] = 5;
        commodity_[4] = 8;
    }

    void run() override
    {
        std::cout << "甜品店有如下商品可以选择：" << std::endl
                  << "提拉米苏 10元；" << std::endl
                  << "蛋黄派 5元；" << std::endl
                  << "小熊饼干 5元；" << std::endl
                  << "三明治 8元；" << std::endl; 
    }

    int sum(std::string& command) override
    {
        parse_ = new CommandParse(command);
        std::map<int, int> id_num = parse_->handle();
  
        int price = 0;
        for(auto elem : id_num)
        {
            price = price + commodity_[elem.first] * elem.second;
        }

        delete parse_;

        return price;
    }

private:

    std::map<int, int> commodity_;
    CommandParse* parse_;
  
};


class BarFactory
{
public:
    static SnackBar* createBar(int i)
    {
        if(i == 1)
        {
            return new DrinkBar;
        }
        else if(i == 2)
        {
            return new BarbecueBar;
        }
        else if( i == 3)
        {
            return new SweetBar;
        }
        return nullptr;
    }


};


#endif