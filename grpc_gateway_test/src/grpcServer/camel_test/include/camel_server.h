#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>

#include "protobuf/camel-grpc.grpc.pb.h"
#include "protobuf/camel-db.pb.h"
#include "protobuf/camel-common.pb.h"
#include "protobuf/camel-agvs.pb.h"
#include "protobuf/camel-grpc.pb.h"

using grpc::Server;
using grpc::ServerAsyncReader;
using grpc::ServerAsyncResponseWriter;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerCompletionQueue;
using grpc::Status;
using std::chrono::system_clock;

using namespace camel;
using namespace api;


class ICallData
{
public:
	virtual ~ICallData() {}
};

template<class Req, class Rsp>
class AbstractCallData : public ICallData {
public:
	AbstractCallData(ServerContext* ctx)
		: responder_(ctx)
	{};

	Req request;
	Rsp response;

	ServerAsyncResponseWriter<Rsp> responder_;
};

class GRPCServiceImpl final {
public:
	~GRPCServiceImpl();

	// 启动gRPC服务.
	void Run(int iGRPCPort);

private:
	// 处理接收到的请求的业务逻辑类
	class CallData {
	public:
		enum ServiceType {
			ST_Start,

			ST_UploadMap,
			ST_GetVersion,
			ST_GetAgvState,
			ST_GetAgvStateInAgvs,
			ST_SendToCamel,
			ST_SetCamelCfg,
			ST_GetCamelCfg,
			ST_GetCamelPathCollection,
			ST_RoutePlan,
			ST_ControlAgv,
			ST_GetRosNodeCfg,
			ST_SetRosNodeCfg,
			ST_GetRosoutMsg,
			ST_SetAvoidanceArea,
			ST_LogExport,
			ST_AlarmUpload,
			ST_RequestUIConfig,
			ST_StickControl,
			ST_ApplyStickControl,
			ST_UpdateStation,
			ST_TaskAllocation,
			ST_AssignAllocationTasks,
			ST_End
		};

		// Take in the "service" instance (in this case representing an asynchronous
		// server) and the completion queue "cq" used for asynchronous communication
		// with the gRPC runtime.
		CallData(AgvService::AsyncService* service, ServerCompletionQueue* cq, ServiceType type);
		~CallData();

		void Proceed();
		static void StartAllServices(AgvService::AsyncService* service, ServerCompletionQueue* cq);

	protected:
		template<class Req, class Rsp>
		void ProcessService(std::function<void(AbstractCallData<Req, Rsp> *)>);

	private:
		// 处理iSee推送的地图信息
		bool ProceedMapMsg(ISeeMap mapInfo, Result& result);

		// 处理地图信息中的region消息
		bool ProceedRegionMsg(ISeeMap_Region map_region, Result& result);

		// 处理地图信息中的area消息
		bool ProceedAreaMsg(ISeeMap mapInfo, Result& result);

		// 处理地图信息中的path消息
		bool ProceedPathMsg(ISeeMap mapInfo, Result& result);

		// 处理地图信息中的station消息
		bool ProceedStationMsg(ISeeMap mapInfo, Result& result);

		// 处理地图信息中的configuration消息
		bool ProceedCfgMsg(ISeeMap mapInfo);

		// 处理地图信息中的car management消息
		bool ProceedCarMngMsg(ISeeMap map_cfg, Result& result);

		// 处理地图信息中的coord offset消息
		bool ProceedCoordOffsetMsg(ISeeMap mapinfo, Result& result);

		// 收集小车中运行信息上传给Camel_ui
		bool ProcessAgvInfo(AgvInfo & agvInfo);

		// 收集小车在AGVS中运行信息
		bool ProcessCamelMessage(CamelSysInfo & msg);

		// 处理发送给Agvs的Msg
		bool ProcessSendToAgvsMsg(CamelMessage & msg, Result & result);
		// 处理地图信息中的task_action消息
		bool ProceedTaskActionMsg(ISeeMap mapInfo, Result& result);

		// 处理获取camel版本信息的rpc消息
		void ProceedGetVersionMsg(ISeeMap mapInfo, Version& version);

		// 处理iSee推送的camel配置信息
		void ProceedSetCamelCfgMsg(CamelCfg camelcfg, Result& result);

		// 处理获取camel配置信息的rpc消息
		void ProceedGetCamelCfgMsg(CamelCfg& camelcfg);

		// 处理发送给ui的所有路径信息
		void ProcessGetCamelPathCollection(PathCollection& paths);

		// 处理发送给ui的当前路径信息
		void ProcessGetCamelCurrentRoute(PathCollection & collection);

		// 收到isee的地图信息后，加载地图信息到内存中
		void ReloadDBToPrivateData();

		// 收到路径规划请求
		void ProcessRoutePlan(CamelMessage_MissonFromAgvs & msg);

		// 处理车体控制命令
		void ProcessCarControl(Operation & opt);

		void ProcessGetRosNodesCfg(RosNodesCfg & cfg);

		void ProcessSetRosNodeCfg(RosNode & cfg, Result	& result);

		void ProcessGetRosoutMsg(RosoutMsg & msg);

		void ProcessSetAvoidanceArea(AvoidanceAreaCollection & areas);

		void ProcessLogExport(LogRequest & log, LogResponse & rsp);
		
		void ProcessAlarmUpload(AlarmMsg & msg);

		void ProcessRequestUIConfig(UIConfig & cfg);

		void ProcessStickControl(Gamepad & gamepad, Result & result);

		void ProcessApplyStickControl(GamepadControl & control, Token & token);

		// 处理marker站点坐标更新消息
		void ProcessUpdateStation(UpdateStation& updateInfo, UpdatePose& newPose);

		// 处理小千斤任务命令
		void ProcessTaskAllocation(GrpcTaskOperation &operation, GrpcTaskAllocations &tasks);

		// 重置小千斤任务
		void ProcessAssignAllocationTasks(GrpcTaskAllocations &tasks, Result &result);

		// The means of communication with the gRPC runtime for an asynchronous
		// server.
		AgvService::AsyncService* service_;
		// The producer-consumer queue where for asynchronous server notifications.
		ServerCompletionQueue* cq_;
		// Context for the rpc, allowing to tweak aspects of it such as the use
		// of compression, authentication, as well as to send metadata back to the
		// client.
		ServerContext ctx_;

		ServiceType type_;

		ICallData *m_pCallData;

		// 处理iSee推送地图rpc消息使用的参数.
		ISeeMap mapInfo_;    //接收到的消息

		Result result_;      //回复的消息

		ServerAsyncResponseWriter<Result> result_responder_;  //发送回应消息的方法

		// 处理获取版本信息rpc消息使用的参数.

		Version Version_;

		ServerAsyncResponseWriter<Version> version_responder_;

		// 处理推送camel配置消息的rpc
		CamelCfg camelcfg_;

		// 处理获取camel配置消息的rpc
		google::protobuf::Empty empty_;

		ServerAsyncResponseWriter<CamelCfg> CamelCfg_responder_;
		// Let's implement a tiny state machine with the following states.
		enum CallStatus { CREATE, PROCESS, FINISH };
		CallStatus status_;  // The current serving state.
	};

	// This can be run in multiple threads if needed.
	void HandleRpcs();

	std::unique_ptr<ServerCompletionQueue> cq_;
	AgvService::AsyncService service_;
	std::unique_ptr<Server> server_;
};
