#include <Poco/Path.h>
#include <Poco/File.h>
#include <Poco/FileStream.h>
#include <Poco/Util/JSONConfiguration.h>

#include <iostream>
#include <unordered_set>

namespace
{
    constexpr const char *AUTO_RUNNER = "autorunner";
    constexpr const char *ROS_MODULES = "rosModules";
    constexpr const char *PROTECTED = "protected";
    constexpr const char *LOG_ARCHIVED = "logArchived";
    constexpr const char *SQLITE = "sqliteDB";
    constexpr const char *CAMEL_CONFIG = "camelConfig";
    constexpr const char *CAMEL_ENDPOINT = "camelServerEndpoint";
    constexpr const char *ROS_PATH = "rosPath";
    constexpr const char *LOCALIZER_DEFAULT_NODE = "localizerDefaultNode";
    constexpr const char *GRPC_PROT = "grpcPort";
    constexpr const char *ASIO_CONTEXTS_SIZE = "asioContextSize";
    constexpr const char *KEEP_ALIVE = "keepAlive";
    constexpr const char *NTP_SERVER = "ntpServer";
    constexpr const char *ROS_SLAVE = "ros.slave";
    constexpr const char *ROS_MASTER_URI = "ros.master";
    constexpr const char *ROS_HOSTNAME = "ros.hostname";
    constexpr const char *COMPOUND_MODE = "packageCompoundMode";
}

class ConfigManager
{
public:
    ConfigManager()
    {
        Poco::File file("./defender.json");

        if (!file.createFile())
        {
            m_jsonConfiguration.load(file.path());
        }

        // 检查配置文件是否完整，如果有配置项缺失，以默认值补充完整
        CheckConfig();
    }

    //~ConfigManager();

private:
    // void Init();
    // void Release();

    // std::string GetConfigPath();

    void CheckConfig()
    {
#define M_CHECK_CONFIG(key, value, func)          \
    do                                            \
    {                                             \
        if (!m_jsonConfiguration.has(key))        \
        {                                         \
            m_jsonConfiguration.func(key, value); \
        }                                         \
    } while (0);

        if (!m_jsonConfiguration.has(AUTO_RUNNER))
        {
            m_jsonConfiguration.setString(std::string(AUTO_RUNNER).append(".1"), "/opt/script/start.sh");
        }
        if (!m_jsonConfiguration.has(ROS_MODULES))
        {
            m_jsonConfiguration.setString(std::string(ROS_MODULES).append(".1"), "localizer");
            m_jsonConfiguration.setString(std::string(ROS_MODULES).append(".2"), "mcu");
        }
        if (!m_jsonConfiguration.has(PROTECTED))
        {
            m_jsonConfiguration.setString(std::string(PROTECTED).append(".1"), "");
        }

        //检查日志存档模块是否齐全，不全则以默认配置补全
        std::unordered_set<std::string> defaultModules = {"camel", "controller", "defender", "plc_core", "nav", "ros_solver", "season", "IDoo","mqtt"};
        std::unordered_set<std::string> VModuleNames;
        int index = 0;

        if (m_jsonConfiguration.has(LOG_ARCHIVED))
        {
            std::vector<std::string> Vkeys;
            m_jsonConfiguration.keys(std::string(LOG_ARCHIVED), Vkeys);
            //根据key将所有对应的模块名取出
            for (auto subKey : Vkeys)
            {
                std::string key = std::string(LOG_ARCHIVED) + "." + subKey;
                std::string modulename = m_jsonConfiguration.getString(key);
                VModuleNames.insert(modulename);
            }

            index = VModuleNames.size();
        }

        for (std::string defaultModule : defaultModules)
        {
            if (VModuleNames.find(defaultModule) == VModuleNames.end())
            {
                index++;
                std::string suffix = std::string(".") + std::to_string(index);
                m_jsonConfiguration.setString(std::string(LOG_ARCHIVED).append(suffix), defaultModule);
            }
        }

        // M_CHECK_CONFIG(ROS_PATH, "/opt/rospackage", setString);
        // M_CHECK_CONFIG(SQLITE, CONFIG_MAIN_DIR "sqlite.db", setString);
        // M_CHECK_CONFIG(CAMEL_CONFIG, CONFIG_MAIN_DIR "config.json", setString);
        // M_CHECK_CONFIG(GRPC_PROT, 5002, setInt);
        // M_CHECK_CONFIG(CAMEL_ENDPOINT, "127.0.0.1:5001", setString);
        // M_CHECK_CONFIG(LOCALIZER_DEFAULT_NODE, "", setString);
        // M_CHECK_CONFIG(ASIO_CONTEXTS_SIZE, 1, setInt);
        // M_CHECK_CONFIG(KEEP_ALIVE, "", setString);
        // M_CHECK_CONFIG(NTP_SERVER, "", setString);
        // M_CHECK_CONFIG(ROS_HOSTNAME, "127.0.0.1", setString);
        // M_CHECK_CONFIG(ROS_MASTER_URI, "http://192.168.0.100:11311 ", setString);
        // M_CHECK_CONFIG(ROS_SLAVE, false, setBool);
        // M_CHECK_CONFIG(COMPOUND_MODE, false, setBool);

        SaveConfig();
    }

    void
    SaveConfig()
    {
        Poco::File file("./defender.json");
        //使用Poco FileOutputStream 支持中文 跨平台
        Poco::FileOutputStream fos(file.path());
        m_jsonConfiguration.save(fos);
        fos.close();
    }

private:
    Poco::Util::JSONConfiguration m_jsonConfiguration;
};

int main()
{
    ConfigManager conf;
    return 0;
}