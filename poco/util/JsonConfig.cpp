#include<iostream>
#include<fstream>

#include<Poco/Util/JSONConfiguration.h>

int main()
{
    Poco::Util::JSONConfiguration jsconf("config.json");
    std::string name1 = jsconf.getString("config.Name");
    std::cout << "name1: " << name1 << "\n";
    //修改配置文件
    jsconf.setString("config.Name", "xiaoming");
    std::string name2= jsconf.getString("config.Name");
    std::cout << "name2: " << name2 << "\n";
    //增、删
    
    //将修改的配置文件存储到磁盘
    std::filebuf fb;
    fb.open("config.json", std::ios::out);
    std::ostream os(&fb);
    jsconf.save(os);
    fb.close();
}