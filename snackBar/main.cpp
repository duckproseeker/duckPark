#include "snackBar.h"

#include <assert.h>

void start()
{
    std::cout << "商业街有如下店铺：" << std::endl
              << "1.饮品店；" << std::endl
              << "2.烧烤店；" << std::endl
              << "3.甜品店；" << std::endl
              << "请输入数字选择你要进入的店铺：" << std::endl;

    int i;
    std::cin >> i;

    BarFactory* barFactory;
    SnackBar* bar = barFactory->createBar(i);
    //assert(bar);
    if(nullptr == bar )
    {
        std::cout << "quit success!\n";
        return;
    }

    bar->run();

    std::cout << "请输入 商品序号*数量，如果订购多个商品， 请用,隔开" << std::endl;
    
    std::string command;
    std::cin >> command;

    int sumPrice = bar->sum(command);
    std::cout << "您此次订购的商品总价为" << sumPrice << "元" << std::endl;
    delete bar;

}


int main(int argc, char** argv)
{
    start();

    return 0;
}
