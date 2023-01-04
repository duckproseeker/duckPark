#include "json.hpp"

#include <tuple>
#include <vector>
#include <map>
#include <unordered_set>

namespace gloss
{
	typedef std::tuple<bool, std::string, std::string> RosMaster;
	class ConfigManager
	{
	public:
		ConfigManager();
		~ConfigManager();

		/* interface */
		std::vector<std::string> GetAutoRunner();
		std::vector<std::string> GetRosModules();
		std::vector<std::string> GetProtectedProgram();
		std::vector<std::string> GetLogArchived();
		std::map<std::string, std::string> GetKeepAliveMap();
		std::string GetSqliteDBPath();
		std::string GetCamelCfgPath();
		std::string GetCamelServerEndpoint();
		std::string GetRosPath();
		std::string GetLocalizerDefaultNode();
		std::string GetNtpServer();
		int GetGrpcPort();
		int GetAsioContextsSize();
		RosMaster GetRosMaster();
		bool IsCompoundMode();

		void SetLocalizerDefaultNode(const std::string &node);

	private:
		void Init();
		void Release();

		std::string GetConfigPath();
		void CheckConfig();
		void SaveConfig();

		std::vector<std::string> GetArray(const std::string & key);
		std::map<std::string, std::string> GetMap(const std::string & key);

	private:
        nlohmann::json m_jsonConfiguration;
	};
}
