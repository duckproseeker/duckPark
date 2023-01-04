#include "json.hpp"

#include <fstream>
#include <iostream>

using nlohmann::json;
constexpr const char *ConfigPath = "cfg.json";
constexpr const char *KEEPA = "keepAlive";



int main()
{
    std::ifstream ifs(ConfigPath);
    json j_config = json::parse(ifs);

    #define M_CHECK_CONFIG(key, value)	    \
    do {									\
        if (!j_config.contains(key)) {		    \
            j_config[key] = value;	        \
        }									\
    } while (0);


    //判断Json对象里是否含有某个key
    // std::cout << j_config.contains(KEEPA) << std::endl;
    // std::cout << j_config.contains("camel_ui") << std::endl;
    // std::cout << j_config.contains("/keepAlive/camel_ui"_json_pointer) << std::endl;
    
    // std::cout << j_config.at("keepAlive") << std::endl;
    // std::cout << j_config.at("/keepAlive/camel_ui"_json_pointer) << std::endl;
    // std::cout << j_config.at("grpcPort") << std::endl;
    std::cout << j_config["ros"]["slave"].get<int>()<< std::endl;

    //迭代嵌套的json
    std::map<std::string, std::string> v = j_config.at("logArchived").get<std::map<std::string, std::string>>();
    for(auto elem : v)
    {
        std::cout << elem.first << elem.second << std::endl;
    }
    // for(int i = 0; i < v.size(); ++i)
    // {
    //     std::cout << v[].dump() << std::endl;
    // }

    //增删
    //j_config["logArchived"]["33"] = "test";

    M_CHECK_CONFIG("key1", true);

    if(j_config.contains("/keepAlive"_json_pointer))
    {
        if(!j_config.contains("/keepAlive/camel_ui"_json_pointer))
        {
            j_config.erase("keepAlive");
            j_config["keepAlive"]["camel_ui"] = "/opt/script/start.sh";
        }
    }

    //保存
    std::ofstream ofs("cfg.json");
    ofs << j_config.dump(4);
}