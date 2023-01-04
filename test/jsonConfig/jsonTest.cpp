#include "jsonTest.h"
#include <fstream>
#include <iostream>
#include <Poco/Path.h>
#include <Poco/File.h>

using namespace nlohmann;
using namespace std;

#define CONFIG_FILE "defender.json"
#define CONFIG_MAIN_DIR "/home/kavin"
namespace 
{
	constexpr const char *AUTO_RUNNER = "autorunner";
	constexpr const char *ROS_MODULES = "rosModules";
	constexpr const char *PROTECTED	= "protected";
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

gloss::ConfigManager::ConfigManager()
{
	Init();
}

gloss::ConfigManager::~ConfigManager()
{
	Release();
}

std::vector<std::string> gloss::ConfigManager::GetAutoRunner()
{
	return GetArray(AUTO_RUNNER);
}

std::vector<std::string> gloss::ConfigManager::GetRosModules()
{
	return GetArray(ROS_MODULES);
}

std::vector<std::string> gloss::ConfigManager::GetProtectedProgram()
{
	return GetArray(PROTECTED);
}

std::vector<std::string> gloss::ConfigManager::GetLogArchived()
{
	return GetArray(LOG_ARCHIVED);
}

std::map<std::string, std::string> gloss::ConfigManager::GetKeepAliveMap()
{
	return GetMap(KEEP_ALIVE);
}

std::string gloss::ConfigManager::GetSqliteDBPath()
{
	return m_jsonConfiguration[SQLITE].get<std::string>();
}

std::string gloss::ConfigManager::GetCamelCfgPath()
{
	return m_jsonConfiguration[CAMEL_CONFIG].get<std::string>();
}

std::string gloss::ConfigManager::GetCamelServerEndpoint()
{
	return m_jsonConfiguration[CAMEL_ENDPOINT].get<std::string>();
}

std::string gloss::ConfigManager::GetRosPath()
{
	std::string path = m_jsonConfiguration[ROS_PATH].get<std::string>();
	if (path.back() != '\\' && path.back() != '/')
	{
		path += '/';
	}
	return path;
}

std::string gloss::ConfigManager::GetLocalizerDefaultNode()
{
	return m_jsonConfiguration[LOCALIZER_DEFAULT_NODE].get<std::string>();
}

std::string gloss::ConfigManager::GetNtpServer()
{
	return m_jsonConfiguration[NTP_SERVER].get<std::string>();
}

int gloss::ConfigManager::GetGrpcPort()
{
	return m_jsonConfiguration[GRPC_PROT].get<int>();
}

int gloss::ConfigManager::GetAsioContextsSize()
{
	return m_jsonConfiguration[ASIO_CONTEXTS_SIZE].get<int>();
}

gloss::RosMaster gloss::ConfigManager::GetRosMaster()
{
	std::string masterUri = m_jsonConfiguration[ROS_MASTER_URI].get<std::string>();
	std::string hostname = m_jsonConfiguration[ROS_HOSTNAME].get<std::string>();
	bool slave = m_jsonConfiguration[ROS_SLAVE].get<bool>();
	return RosMaster(slave, hostname, masterUri);
}

bool gloss::ConfigManager::IsCompoundMode()
{
	return m_jsonConfiguration[COMPOUND_MODE].get<bool>();
}

void gloss::ConfigManager::SetLocalizerDefaultNode(const std::string & node)
{
	m_jsonConfiguration[LOCALIZER_DEFAULT_NODE] = node;
	SaveConfig();
}

void gloss::ConfigManager::Init()
{
	Poco::File file(GetConfigPath());
	// CommonUtil::CreateDir(file.path());

	if(!file.createFile())
	{
		//当文件存在且为空的时候，解析会抛异常
		if(file.exists() && file.getSize() != 0)
		{
			std::ifstream ifs(GetConfigPath());
			m_jsonConfiguration = json::parse(ifs);
			// ifs >> m_jsonConfiguration;
			ifs.close();
		}
	}
	// 检查配置文件是否完整，如果有配置项缺失，以默认值补充完整
	CheckConfig();
}

void gloss::ConfigManager::Release()
{
	m_jsonConfiguration.clear();
}

std::string gloss::ConfigManager::GetConfigPath()
{
	std::string path;
#ifdef WIN32
	path = Poco::Path::current() + CONFIG_FILE;
#else
	path = CONFIG_FILE;
#endif // WIN32
	return path;
}

void gloss::ConfigManager::CheckConfig()
{
	#define M_CHECK_CONFIG(key, value)				\
    do {											\
        if (!m_jsonConfiguration.contains(key)) {	\
            m_jsonConfiguration[key] = value;		\
        }											\
    } while (0);

	if (!m_jsonConfiguration.contains(AUTO_RUNNER))
	{
		m_jsonConfiguration[AUTO_RUNNER]["1"] = "/opt/script/start.sh";
	}
	if (!m_jsonConfiguration.contains(ROS_MODULES))
	{
		m_jsonConfiguration[ROS_MODULES]["1"] = "localizer";
		m_jsonConfiguration[ROS_MODULES]["2"] = "mcu";
	}
	if (!m_jsonConfiguration.contains(PROTECTED))
	{
		m_jsonConfiguration[PROTECTED]["1"] = "";
	}

	//检查日志存档模块是否齐全，不全则以默认配置补全
	std::vector<std::string> defaultModules = { "camel", "controller", "defender", "plc_core", "nav", "ros_solver","season","IDoo","CamelMqtt" };
	std::unordered_set<std::string> VModuleNames;
	int index = 0;

	if (m_jsonConfiguration.contains(LOG_ARCHIVED))
	{
		for(auto module : GetLogArchived())
		{
			VModuleNames.emplace(module);
		}
		index = VModuleNames.size();
	}
	//遍历日志默认配置的模块，找出目前缺少的配置模块，并在后补齐。
	for (std::string defaultModule : defaultModules)
	{
		if (VModuleNames.find(defaultModule) == VModuleNames.end())
		{
			m_jsonConfiguration[LOG_ARCHIVED][std::to_string(++index)] = defaultModule;
		}
	}
	
	M_CHECK_CONFIG(ROS_PATH, "/opt/rospackage");
	M_CHECK_CONFIG(SQLITE, CONFIG_MAIN_DIR "sqlite.db");
	M_CHECK_CONFIG(CAMEL_CONFIG, CONFIG_MAIN_DIR "config.json");
	M_CHECK_CONFIG(GRPC_PROT, 5002);
	M_CHECK_CONFIG(CAMEL_ENDPOINT, "127.0.0.1:5001");
	M_CHECK_CONFIG(LOCALIZER_DEFAULT_NODE, "");
	M_CHECK_CONFIG(ASIO_CONTEXTS_SIZE, 1);
	M_CHECK_CONFIG(KEEP_ALIVE, "");
	M_CHECK_CONFIG(NTP_SERVER, "");
	M_CHECK_CONFIG(ROS_HOSTNAME, "127.0.0.1");
	M_CHECK_CONFIG(ROS_MASTER_URI, "http://192.168.0.100:11311 ");
	M_CHECK_CONFIG(ROS_SLAVE, false);
	M_CHECK_CONFIG(COMPOUND_MODE, false);

	//默认配置camel_ui的保活
	if(m_jsonConfiguration.contains(KEEP_ALIVE))
	{
		if(!m_jsonConfiguration.contains("/keepAlive/camel_ui"_json_pointer))
		{
			m_jsonConfiguration.erase(KEEP_ALIVE);
			m_jsonConfiguration[KEEP_ALIVE]["camel_ui"] = "/opt/camel_ui/start.sh";
		}
	}

	SaveConfig();
}

void gloss::ConfigManager::SaveConfig()
{
	std::ofstream ofs(GetConfigPath());
	ofs << m_jsonConfiguration.dump(4);
	ofs.close();
}

std::vector<std::string> gloss::ConfigManager::GetArray(const std::string & key)
{
	std::vector<std::string> vctRst;
	if(m_jsonConfiguration.contains(key))
	{
		std::map<std::string, std::string> m_subObject = m_jsonConfiguration.at(key).get<std::map<std::string, std::string>>();
		for(auto &[ky, value] : m_subObject)
		{
			vctRst.push_back(value);
		}
	}
	return vctRst;
}

std::map<std::string, std::string> gloss::ConfigManager::GetMap(const std::string & key)
{
	return m_jsonConfiguration.at(key).get<std::map<std::string, std::string>>();
}

/*test*/
int main()
{
	gloss::ConfigManager cfg;
}