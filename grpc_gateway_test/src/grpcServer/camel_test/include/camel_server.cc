#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <chrono>

#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>

#include "camel_server.h"

using google::protobuf::Empty;

enum gRPC_Process_ErrorCode {
	ERR_GRPC_OK = 0,
	ERR_SameMapVersion = 1,
	ERR_AddRegionRecordFail,
	ERR_AddAreaRecordFail,
	ERR_AddPathRecordFail,
	ERR_AddStationRecordFail,
	ERR_AddCfgRecordFail,
	ERR_AddTaskActionFail,
	ERR_SetCamelCfgFail,
	ERR_AddCarManagementFail,
	ERR_AddCoordOffsetFail,
	ERR_NoValidCamelCfg,
	ERR_UpdateMapFail,
};

enum MarkerType {
	MT_Start,

	MT_Laser,  //以车体运动中心的位姿作为站点坐标
	MT_QRCode, //以二维码中心的激光坐标，作为站点坐标
};

//static Poco::UUID s_GamepadControlKey;
// typedef Poco::ExpirationDecorator<std::string> ExpString;
// static Poco::UniqueExpireCache<std::string, ExpString> s_cacheManager;
constexpr const char *KEY_GAMEPADCONTROL = "GamepadControlKey";

// camel作为gRPC的server端，异步处理grpc消息
GRPCServiceImpl::~GRPCServiceImpl() {
	server_->Shutdown();
	// 在关闭server之后再关闭队列
	cq_->Shutdown();
}

void GRPCServiceImpl::Run(int iGRPCPort) {
	std::string server_address = "0.0.0.0:" + std::to_string(iGRPCPort);

	ServerBuilder builder;
	// 监听指定地址和端口，不使用认证机制
	builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());

	// 注册service_作为与客户端通信的实例
	builder.RegisterService(&service_);
	builder.SetMaxReceiveMessageSize(48 * 1024 * 1024);	//48MB

	// 用于异步通信的队列
	cq_ = builder.AddCompletionQueue();

	// 构建和启动server.
	server_ = builder.BuildAndStart();

	printf("%s:%d start gRPC service, listening on %s ", __FUNCTION__, __LINE__, server_address.c_str());

	// server处理的主循环.
	HandleRpcs();
}

//处理具体一个rpc请求的实例
GRPCServiceImpl::CallData::CallData(AgvService::AsyncService* service, ServerCompletionQueue* cq, ServiceType type)
	: service_(service), cq_(cq), result_responder_(&ctx_), version_responder_(&ctx_), 
	CamelCfg_responder_(&ctx_), type_(type), status_(CREATE), m_pCallData(nullptr) {
	Proceed();
}

GRPCServiceImpl::CallData::~CallData()
{
	if (nullptr != m_pCallData)
	{
		delete m_pCallData;
		m_pCallData = nullptr;
	}
}

template<class Req, class Rsp>
void GRPCServiceImpl::CallData::ProcessService(std::function<void(AbstractCallData<Req, Rsp> *)> func)
{
	AbstractCallData<Req, Rsp> *pData = static_cast<AbstractCallData<Req, Rsp>*>(m_pCallData);
	if (nullptr != pData)
	{
		func(pData);

		status_ = FINISH;
		pData->responder_.Finish(pData->response, Status::OK, this);
	}
}

//处理rpc请求，包含了一个简单的状态机
// create状态：实例初始化时的初始值，注册响应处理的rpc消息类型，并转入process状态
// process状态：收到对应的rpc消息并处理，处理完后转入finish状态
// finish状态：结束处理，释放资源
void GRPCServiceImpl::CallData::Proceed()
{
	printf("%s:%d received a rpc message, type=%d, status=%d", __FUNCTION__, __LINE__, type_, status_);
	if (status_ == CREATE) {
		// 这个实例的状态转为process.
		status_ = PROCESS;

		// 注册处理对应的rpc消息。 this是calldata实例的地址

		switch (type_)
		{
		case GRPCServiceImpl::CallData::ST_UploadMap:
			service_->RequestUploadMapData(&ctx_, &mapInfo_, &result_responder_, cq_, cq_, this);
			break;
		case GRPCServiceImpl::CallData::ST_GetVersion:
			service_->RequestGetVersion(&ctx_, &mapInfo_, &version_responder_, cq_, cq_, this);
			break;
		case GRPCServiceImpl::CallData::ST_GetAgvState:
		{
			AbstractCallData<Empty, AgvInfo> *p = new AbstractCallData<Empty, AgvInfo>(&ctx_);
			service_->RequestGetAgvState(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_GetAgvStateInAgvs:
		{
			AbstractCallData<Empty, CamelSysInfo> *p = new AbstractCallData<Empty, CamelSysInfo>(&ctx_);
			service_->RequestGetAgvStateInAgvs(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_SendToCamel:
		{
			AbstractCallData<CamelMessage, Result> *p = new AbstractCallData<CamelMessage, Result>(&ctx_);
			service_->RequestSendToAgvs(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_SetCamelCfg:
			service_->RequestSetCamelCfg(&ctx_, &camelcfg_, &result_responder_, cq_, cq_, this);
			break;
		case GRPCServiceImpl::CallData::ST_GetCamelCfg:
			service_->RequestGetCamelCfg(&ctx_, &empty_, &CamelCfg_responder_, cq_, cq_, this);
			break;
		case GRPCServiceImpl::CallData::ST_GetCamelPathCollection:
		{
			AbstractCallData<Empty, PathCollection> *p = new AbstractCallData<Empty, PathCollection>(&ctx_);
			service_->RequestGetCamelPathCollection(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_RoutePlan:
		{
			AbstractCallData<CamelMessage_MissonFromAgvs, Empty> *p = new AbstractCallData<CamelMessage_MissonFromAgvs, Empty>(&ctx_);
			service_->RequestRoutePlan(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_ControlAgv:
		{
			AbstractCallData<Operation, Result> *p = new AbstractCallData<Operation, Result>(&ctx_);
			service_->RequestControlAgv(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_GetRosNodeCfg:
		{
			AbstractCallData<Empty, RosNodesCfg> *p = new AbstractCallData<Empty, RosNodesCfg>(&ctx_);
			service_->RequestGetRosNodeCfg(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_SetRosNodeCfg:
		{
			AbstractCallData<RosNode, Result> *p = new AbstractCallData<RosNode, Result>(&ctx_);
			service_->RequestSetRosNodeCfg(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_GetRosoutMsg:
		{
			AbstractCallData<Empty, RosoutMsg> *p = new AbstractCallData<Empty, RosoutMsg>(&ctx_);
			service_->RequestGetRosoutMsg(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_SetAvoidanceArea:
		{
			AbstractCallData<AvoidanceAreaCollection, Empty> *p = new AbstractCallData<AvoidanceAreaCollection, Empty>(&ctx_);
			service_->RequestSetAvoidanceArea(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_LogExport:
		{
			AbstractCallData<LogRequest, LogResponse> *p = new AbstractCallData<LogRequest, LogResponse>(&ctx_);
			service_->RequestLogExport(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_AlarmUpload:
		{
			AbstractCallData<AlarmMsg, Empty> *p = new AbstractCallData<AlarmMsg, Empty>(&ctx_);
			service_->RequestAlarmUpload(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_RequestUIConfig:
		{
			AbstractCallData<Empty, UIConfig> *p = new AbstractCallData<Empty, UIConfig>(&ctx_);
			service_->RequestRequestUIConfig(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_StickControl:
		{
			AbstractCallData<Gamepad, Result> *p = new AbstractCallData<Gamepad, Result>(&ctx_);
			service_->RequestStickControl(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_ApplyStickControl:
		{
			AbstractCallData<GamepadControl, Token> *p = new AbstractCallData<GamepadControl, Token>(&ctx_);
			service_->RequestApplyStickControl(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}

		case GRPCServiceImpl::CallData::ST_UpdateStation:
		{
			AbstractCallData<UpdateStation, UpdatePose> *p = new AbstractCallData<UpdateStation, UpdatePose>(&ctx_);
			service_->RequestUpdateStationPose(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_TaskAllocation:
		{
			AbstractCallData<GrpcTaskOperation, GrpcTaskAllocations> *p = new AbstractCallData<GrpcTaskOperation, GrpcTaskAllocations>(&ctx_);
			service_->RequestTaskAllocationOperation(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		case GRPCServiceImpl::CallData::ST_AssignAllocationTasks:
		{
			AbstractCallData<GrpcTaskAllocations, Result> *p = new AbstractCallData<GrpcTaskAllocations, Result>(&ctx_);
			service_->RequestAssignAllocationTasks(&ctx_, &p->request, &p->responder_, cq_, cq_, this);
			m_pCallData = p;
			break;
		}
		default:
			break;
		}
	}
	else if (status_ == PROCESS) {
		system_clock::time_point start_time = system_clock::now();
		// 处理该消息时，新创建一个实例来服务新的客户端
		new CallData(service_, cq_, this->type_);

		switch (type_)
		{
		case GRPCServiceImpl::CallData::ST_UploadMap:
		{
			printf("%s:%d start to process uploadmap rpc msg", __FUNCTION__, __LINE__);
			// 处理接收到的地图信息，并设置返回值
			ProceedMapMsg(mapInfo_, result_);

			// 回复消息给iSee
			status_ = FINISH;
			result_responder_.Finish(result_, Status::OK, this);
			system_clock::time_point end_time = system_clock::now();
			auto milisecs = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
			printf("%s:%d finish to process uploadmap rpc msg, reply msg is errorcode:%d, errormsg: %s, process time: %d ms", __FUNCTION__, __LINE__, result_.errorcode(), result_.message().c_str(), milisecs);
		}
		break;
		case GRPCServiceImpl::CallData::ST_GetVersion:
		{
			ProceedGetVersionMsg(mapInfo_, Version_);

			status_ = FINISH;
			version_responder_.Finish(Version_, Status::OK, this);
			printf("%s:%d finish to process getversion rpc msg, reply msg is camelversion:%s, dbversion: %s", __FUNCTION__, __LINE__, Version_.camelversion().c_str(), Version_.dbversion().c_str());
		}
		break;
		case GRPCServiceImpl::CallData::ST_GetAgvState:
			ProcessService<Empty, AgvInfo>([this](AbstractCallData<Empty, AgvInfo> *pData)
			{
				ProcessAgvInfo(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_GetAgvStateInAgvs:
			ProcessService<Empty, CamelSysInfo>([this](AbstractCallData<Empty, CamelSysInfo> *pData)
			{
				ProcessCamelMessage(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_SendToCamel:
		{
			ProcessService<CamelMessage, Result>([this](AbstractCallData<CamelMessage, Result> *pData)
			{
				ProcessSendToAgvsMsg(pData->request, pData->response);
			});
			break;
		}
		case GRPCServiceImpl::CallData::ST_SetCamelCfg:
		{
			ProceedSetCamelCfgMsg(camelcfg_, result_);

			status_ = FINISH;

			result_responder_.Finish(result_, Status::OK, this);
		}
		break;

		case GRPCServiceImpl::CallData::ST_GetCamelCfg:
		{
			ProceedGetCamelCfgMsg(camelcfg_);

			status_ = FINISH;
			CamelCfg_responder_.Finish(camelcfg_, Status::OK, this);

			printf("%s:%d finish to process getcamelcfg rpc msg, reply msg is %s", __FUNCTION__, __LINE__, camelcfg_.jsonstring().c_str());
		}
		break;
		case GRPCServiceImpl::CallData::ST_GetCamelPathCollection:
			ProcessService<Empty, PathCollection>([this](AbstractCallData<Empty, PathCollection> *pData)
			{
				ProcessGetCamelPathCollection(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_RoutePlan:
			ProcessService<CamelMessage_MissonFromAgvs, Empty>([this](AbstractCallData<CamelMessage_MissonFromAgvs, Empty> *pData)
			{
				ProcessRoutePlan(pData->request);
			});
			break;
		case GRPCServiceImpl::CallData::ST_ControlAgv:
			ProcessService<Operation, Result>([this](AbstractCallData<Operation, Result> *pData)
			{
				ProcessCarControl(pData->request);
			});
			break;
		case GRPCServiceImpl::CallData::ST_GetRosNodeCfg:
			ProcessService<Empty, RosNodesCfg>([this](AbstractCallData<Empty, RosNodesCfg> *pData)
			{
				ProcessGetRosNodesCfg(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_SetRosNodeCfg:
			ProcessService<RosNode, Result>([this](AbstractCallData<RosNode, Result> *pData)
			{
				ProcessSetRosNodeCfg(pData->request, pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_GetRosoutMsg:
			ProcessService<Empty, RosoutMsg>([this](AbstractCallData<Empty, RosoutMsg> *pData)
			{
				ProcessGetRosoutMsg(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_SetAvoidanceArea:
			ProcessService<AvoidanceAreaCollection, Empty>([this](AbstractCallData<AvoidanceAreaCollection, Empty> *pData)
			{
				ProcessSetAvoidanceArea(pData->request);
			});
			break;
		case GRPCServiceImpl::CallData::ST_LogExport:
			ProcessService<LogRequest, LogResponse>([this](AbstractCallData<LogRequest, LogResponse> *pData)
			{
				ProcessLogExport(pData->request, pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_AlarmUpload:
			ProcessService<AlarmMsg, Empty>([this](AbstractCallData<AlarmMsg, Empty> *pData)
			{
				ProcessAlarmUpload(pData->request);
			});
			break;
		case GRPCServiceImpl::CallData::ST_RequestUIConfig:
			ProcessService<Empty, UIConfig>([this](AbstractCallData<Empty, UIConfig> *pData)
			{
				ProcessRequestUIConfig(pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_StickControl:
			ProcessService<Gamepad, Result>([this](AbstractCallData<Gamepad, Result> *pData)
			{
				ProcessStickControl(pData->request, pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_ApplyStickControl:
			ProcessService<GamepadControl, Token>([this](AbstractCallData<GamepadControl, Token> *pData)
			{
				ProcessApplyStickControl(pData->request, pData->response);
			});
			break;

		case GRPCServiceImpl::CallData::ST_UpdateStation:
			ProcessService<UpdateStation, UpdatePose>([this](AbstractCallData<UpdateStation, UpdatePose> *pData)
			{
				ProcessUpdateStation(pData->request, pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_TaskAllocation:
			ProcessService<GrpcTaskOperation, GrpcTaskAllocations>([this](AbstractCallData<GrpcTaskOperation, GrpcTaskAllocations> *pData)
			{
				ProcessTaskAllocation(pData->request, pData->response);
			});
			break;
		case GRPCServiceImpl::CallData::ST_AssignAllocationTasks:
			ProcessService<GrpcTaskAllocations, Result>([this](AbstractCallData<GrpcTaskAllocations, Result> *pData)
			{
				ProcessAssignAllocationTasks(pData->request, pData->response);
			});
			break;
		default:
			break;
		}
	}
	else {
		GPR_ASSERT(status_ == FINISH);
		// 在finish状态，释放资源(CallData).
		printf("%s:%d finish to process rpc msg, delete calldata", __FUNCTION__, __LINE__);
		delete this;
	}
}

void GRPCServiceImpl::CallData::StartAllServices(AgvService::AsyncService* service, ServerCompletionQueue* cq)
{
	int type = ServiceType::ST_Start + 1;
	for (; type != ServiceType::ST_End; type++)
	{
		new CallData(service, cq, (ServiceType)type);
	}
}

bool GRPCServiceImpl::CallData::ProceedMapMsg(ISeeMap mapInfo, Result& result)
{
	printf("%s:%d received map info, include region[%d], area[%d], path[%d], station[%d], cfg[%d]",
		__FUNCTION__, __LINE__, mapInfo.has_region(), mapInfo_.arealist_size(), mapInfo_.pathlist_size(),
		mapInfo_.stationlist_size(), mapInfo_.configurationlist_size());

	// 更新中时不重复更新
	//if (AfxGetApp()->GetPrivateData()->Updating())
	{
		result_.set_errorcode(ERR_UpdateMapFail);
		//result_.set_message(CommonUtil::UnicodeToUtf8(L"更新尚未完成，请不要重复推送").c_str());
        result_.set_message("更新尚未完成，请不要重复推送");
		return false;
	}


}



void GRPCServiceImpl::CallData::ProcessRoutePlan(CamelMessage_MissonFromAgvs & msg)
{
	// if (AfxGetApp() != nullptr && AfxGetApp()->GetRouteMgr() != nullptr)
	{
		// 用路径中的站点时，一旦把车拉到其他站点希望重新开始时就不行了
		const std::string &data = msg.route();
		printf("%s:%d, route plan data is [%s]", __FUNCTION__, __LINE__, data.c_str());
		// route=0000100002(10位表示起点和终点)
		if (data.length() == 10)
		{
			std::string from = data.substr(0, 5);
			std::string to = data.substr(5, 5);
			//std::string route = AfxGetApp()->GetPathPlanner()->GetShortestRoute(from, to);
			printf("%s:%d, route plan from[%s] to[%s] route[%s]", __FUNCTION__, __LINE__, from.c_str(), to.c_str(), route.c_str());
			// if (route.empty())
			// {
			// 	AlarmShow(ALMID_ROUTE_MANUAL_PLAN_FAIL, true);
			// 	return;
			// }
			// AfxGetApp()->GetRouteMgr()->OnSrvTaskUpdate(msg.contexttask(), route);
			// AfxGetApp()->GetRouteMgr()->OnTrafficPointUpdate(CStationId(to));
		}
		// route=00002(5位表示通行点)
		else if (data.length() == 5)
		{
			printf("%s:%d, route plan traffic[%s]", __FUNCTION__, __LINE__, data.c_str());
			// AfxGetApp()->GetRouteMgr()->OnTrafficPointUpdate(CStationId(data));
		}
		else
		{
			printf("%s:%d, route plan data is invalid", __FUNCTION__, __LINE__);
		}
	}
}

void GRPCServiceImpl::CallData::ProcessCarControl(Operation & opt)
{
	
	if (opt.iscontinue())		//继续运行
	{
		// if (nullptr != mgr)
		{
			printf("%s:%d, receive continue run command.", __FUNCTION__, __LINE__);
			// mgr->ContinueRun();
		}
	}
	else if (opt.clearpath())	//清除路径
	{
	
	}
	else if (opt.clearaction())	//清除动作
	{
		// if ((AfxGetApp() != nullptr) && (AfxGetApp()->GetRouteMgr() != nullptr))
		// {
			printf("%s:%d, receive clear action command.", __FUNCTION__, __LINE__);
			// AfxGetApp()->GetRouteMgr()->ActionSender()->Clear();
		// }
	}
	else if (opt.disablecargo())  // 屏蔽货物检查
	{
	
	}
}

void GRPCServiceImpl::CallData::ProcessGetRosNodesCfg(RosNodesCfg & cfg)
{

}

void GRPCServiceImpl::CallData::ProcessSetRosNodeCfg(RosNode & cfg, Result	& result)
{

}

void GRPCServiceImpl::CallData::ProcessGetRosoutMsg(RosoutMsg & msg)
{


}

void GRPCServiceImpl::CallData::ProcessSetAvoidanceArea(AvoidanceAreaCollection & areas)
{
}

void GRPCServiceImpl::CallData::ProcessLogExport(LogRequest & log, LogResponse & rsp)
{
	if (!log.car().empty())
	{
		std::vector<std::string> modules(log.modules().begin(), log.modules().end());
		std::vector<std::string> times(log.time().begin(), log.time().end());

		// std::string path = LogMgr::LogExport(log.car(), modules, times);
		std::string path = "/usr/local/camel";
        rsp.set_path(path);
	}
}

void GRPCServiceImpl::CallData::ProcessAlarmUpload(AlarmMsg & msg)
{

}

void GRPCServiceImpl::CallData::ProcessRequestUIConfig(UIConfig & cfg)
{

}
void GRPCServiceImpl::CallData::ProcessStickControl(Gamepad & gamepad, Result & result)
{
	const std::string &token = gamepad.token().key();
	if (token.empty()) return;

	// auto value = s_cacheManager.get(KEY_GAMEPADCONTROL);
	// if (value.isNull())
	// {
		result.set_errorcode(2);
		result.set_message("Token expired.");
	// }
// 	else if (gamepad.token().key() != value->value())
// 	{
// 		result.set_errorcode(1);
// 		result.set_message("Key already occupied.");
// 	}
// 	else
// 	{
// 		/* 有操作时刷新过期时间 */
// 		s_cacheManager.update(KEY_GAMEPADCONTROL, ExpString(token, 30 * 1000));

// #ifdef _LINUX64
// 		PLCCore::PROTOCOL_V2::PLC_2_UI_SPEED speed;
// 		speed.fVx = gamepad.vx();
// 		speed.fW = gamepad.vy();
// 		AfxGetApp()->GetServices()->GetPlcServiceLP()->OnRecvStickData(speed);
// #endif
	// }
}
void GRPCServiceImpl::CallData::ProcessApplyStickControl(GamepadControl & control, Token & token)
{
	/* 第一次申请或是强制申请的 */
	if (control.force() /*|| !s_cacheManager.has(KEY_GAMEPADCONTROL)*/)
	{
		/* 创建新的token，放入缓存中并设置过期时间 */
		//std::string newToken = Poco::UUIDGenerator().create().toString();
        std::string newToken = "abcdefg";
		//s_cacheManager.add(KEY_GAMEPADCONTROL, ExpString(newToken, 30 * 1000));
		token.set_key(newToken);
	}
	else
	{
		token.mutable_result()->set_errorcode(1);
		token.mutable_result()->set_message("Key already occupied.");
	}
}
// 处理地图信息中的region消息
bool GRPCServiceImpl::CallData::ProceedRegionMsg(ISeeMap_Region map_region, Result& result)
{

}

// 处理地图信息中的area消息
bool GRPCServiceImpl::CallData::ProceedAreaMsg(ISeeMap mapInfo, Result& result)
{

}

// 处理地图信息中的path消息
bool GRPCServiceImpl::CallData::ProceedPathMsg(ISeeMap mapInfo, Result& result)
{

}

// 处理地图信息中的station消息
bool GRPCServiceImpl::CallData::ProceedStationMsg(ISeeMap mapInfo, Result& result)
{
}

// 处理地图信息中的configuration消息
bool GRPCServiceImpl::CallData::ProceedCfgMsg(ISeeMap mapInfo)
{
	bool ret = true;
	for (int i = 0; i < mapInfo.configurationlist_size(); i++)
	{
		std::stringstream ss;
		ss << "area name:" << mapInfo.configurationlist(i).area_name() << ", "
			<< "task_type:" << mapInfo.configurationlist(i).task_type() << ", "
			<< "section:" << mapInfo.configurationlist(i).section() << ", "
			<< "laser_head_height:" << mapInfo.configurationlist(i).laser_head_height() << ", "
			<< "dedect_zone1:" << mapInfo.configurationlist(i).dedect_zone1() << ", "
			<< "dedect_zone2:" << mapInfo.configurationlist(i).dedect_zone2() << ", "
			<< "distance_zone_interchange:" << mapInfo.configurationlist(i).distance_zone_interchange() << ", "
			<< "destination_range:" << mapInfo.configurationlist(i).destination_range() << ", "
			<< "height_step:" << mapInfo.configurationlist(i).height_step() << ", "
			<< "cargo:" << mapInfo.configurationlist(i).cargo();
		printf("%s:%d received configuration[%d] info [%s}", __FUNCTION__, __LINE__, i, ss.str().c_str());

	
			result_.set_errorcode(ERR_AddCfgRecordFail);
			result_.set_message(CommonUtil::UnicodeToUtf8(L"添加配置信息失败").c_str());
	}
	return ret;
}

bool GRPCServiceImpl::CallData::ProceedTaskActionMsg(ISeeMap mapInfo, Result& result)
{

}

bool GRPCServiceImpl::CallData::ProceedCarMngMsg(ISeeMap mapInfo, Result& result)
{

}

bool GRPCServiceImpl::CallData::ProceedCoordOffsetMsg(ISeeMap mapinfo, Result & result)
{

}

bool GRPCServiceImpl::CallData::ProcessAgvInfo(AgvInfo & agvInfo)
{
}

bool GRPCServiceImpl::CallData::ProcessCamelMessage(CamelSysInfo & msg)
{

}

bool GRPCServiceImpl::CallData::ProcessSendToAgvsMsg(CamelMessage & msg, Result & result)
{
	if (msg.has_requesttoagvs())
	{
		auto request = msg.requesttoagvs();
		std::string station = request.manualstation();
		if (!station.empty())
		{
			//设置发送点
			// if (AfxGetApp() != nullptr && AfxGetApp()->GetRouteMgr() != nullptr)
			// {
				printf("%s:%d, Manually set the current station[%s]", __FUNCTION__, __LINE__, station.c_str());
				// AfxGetApp()->GetRouteMgr()->GetReportStationIns().SetCurrentStation(station);
			// }
		}
		DoAction charging = request.requestcharging();
		if (charging != kNoAction)
		{
			//ChargeCommand *charge = static_cast<ChargeCommand *>(CommandFactory::Single("ChargeCommand"));
			//ChargeCommand *charge = camel::ChargeCommandIns();
			// if (nullptr != charge)
			// {
				// printf("%s:%d, received client charging cmd[%d] channel[%s]", __FUNCTION__, __LINE__, charging, msg.requesttoagvs().strparam().c_str());
				// // 如果没有连接agvs时，充电请求直接响应
				// if (charging == kDoAction1 && (!AfxGetApp()->GetServices()->GetAGVSChannel() || (AfxGetApp()->PlcRunStat().IsRemoved())))
				// {
				// 	charge->RequestCharge(true, std::atoi(msg.requesttoagvs().strparam().c_str()));
				// }
				// else if (charging == kDoAction2)
				// {
				// 	charge->RequestCharge(false, 1);
				// }
			// }
		}
		// 如果有一键拉车指令
		DoAction action = request.initialtraffic();
		printf("%s:%d, received client remove car cmd[%d]", __FUNCTION__, __LINE__, action);
		// if (action == kDoAction1)
		// {
		// 	AbnormalRecovery::RecoveryByOffline();
		// }
		// else if (action == kDoAction2) // 恢复运行
		// {
		// 	AbnormalRecovery::RecoveryByResumeRun();
		// }

		// 接收到解除刹车指令
		DoAction brake = request.liftemergency();
		if (brake == kDoAction1)
		{
			printf("%s:%d, received release brake", __FUNCTION__, __LINE__);
			// if ((!AfxGetApp()->GetServices()->GetAGVSChannel()) || (AfxGetApp()->PlcRunStat().IsRemoved()))
			// {
			// 	AfxGetApp()->BrakeManager().ReleaseBrake();
			// }
		}

		// 发送给agvs
		// AfxGetApp()->GetServices()->GetAgvMsgServicesLP()->SendToAGVS(msg);

		// 如果有完成任务或者进入下一流程时，清除路径并重置站点
		if (request.complishtask() == kDoAction1 || request.nexttaskflow() == kDoAction1)
		{
			printf("%s:%d, received complish task or next task flow", __FUNCTION__, __LINE__);
			// AbnormalRecovery::RecoveryByResumeRun();
		}
	}

	return true;
}
// 处理获取camel版本信息的rpc消息
void GRPCServiceImpl::CallData::ProceedGetVersionMsg(ISeeMap mapInfo, Version& version)
{
	string mapversion;
	// if (mapInfo.has_region())
	// {
	// 	AGVS::REGION region = AfxGetApp()->GetPrivateData()->GetRegionRecordbyName(mapInfo_.region().name());
	// 	mapversion = region.mapVersion;
	// }
	version.set_camelversion("11.17.2222");
	version.set_dbversion("11.17");
}

// 处理iSee推送的camel配置信息
void GRPCServiceImpl::CallData::ProceedSetCamelCfgMsg(CamelCfg camelcfg, Result& result)
{
	// int ret = AfxGetApp()->GetCfgMgr()->HandleISEEConfigFile(camelcfg_.jsonstring());

	// if (ret == 1) 
	// {
		// result_.set_errorcode(ERR_SetCamelCfgFail);
		// result_.set_message("the json string is not valid.");
		
	// }
	// else if (ret == 2)
	// {
		result_.set_errorcode(ERR_NoValidCamelCfg);
		result_.set_message("the message doesn't has valid cfg.");
		printf("%s:%d received setcamelcfg rpc, but no valid cfg. the rpc message is \r%s", __FUNCTION__, __LINE__, camelcfg_.jsonstring().c_str());
	// }
}

void GRPCServiceImpl::CallData::ProceedGetCamelCfgMsg(CamelCfg& camelcfg)
{

}
// 处理发送给ui的所有路径信息
void GRPCServiceImpl::CallData::ProcessGetCamelPathCollection(PathCollection & paths)
{
}
// 处理发送给ui的当前路径信息
void GRPCServiceImpl::CallData::ProcessGetCamelCurrentRoute(PathCollection & collection)
{
}

// 处理marker站点坐标更新消息
void GRPCServiceImpl::CallData::ProcessUpdateStation(UpdateStation& updateInfo, UpdatePose& newPose)
{

		newPose.mutable_pose()->set_x(1);
		newPose.mutable_pose()->set_y(2);
		newPose.mutable_pose()->set_theta(3);
		newPose.mutable_pose()->set_confidence(1.0);

	printf("%s:%d update station pose x[%f] y[%f] theta[%f] cer[%f]", __FUNCTION__, __LINE__, 
		newPose.pose().x(), newPose.pose().y(), newPose.pose().theta(), newPose.pose().confidence());
	newPose.mutable_error_info()->set_errorcode(0);
	newPose.mutable_error_info()->set_message("Set position successfully.");
}

void GRPCServiceImpl::CallData::ProcessTaskAllocation(GrpcTaskOperation & operation, GrpcTaskAllocations & tasks)
{
}

void GRPCServiceImpl::CallData::ProcessAssignAllocationTasks(GrpcTaskAllocations & tasks, Result & result)
{
}

void GRPCServiceImpl::HandleRpcs()
{
	// 创建实例去服务客户端.
	//new CallData(&service_, cq_.get(), GRPCServiceImpl::CallData::ST_UploadMap);
	//new CallData(&service_, cq_.get(), GRPCServiceImpl::CallData::ST_GetVersion);
	//new CallData(&service_, cq_.get(), GRPCServiceImpl::CallData::ST_GetAgvState);
	CallData::StartAllServices(&service_, cq_.get());
	void* tag;  // 一个rpc请求唯一的标识 uniquely identifies a request.
	bool ok;
	while (true) {
		// Block waiting to read the next event from the completion queue. The
		// event is uniquely identified by its tag, which in this case is the
		// memory address of a CallData instance.
		// The return value of Next should always be checked. This return value
		// tells us whether there is any kind of event or cq_ is shutting down.
		// 阻塞式等待从队列中获取下一个事件，每个事件都唯一的用tag标识，tag就是CallData实例的地址
		GPR_ASSERT(cq_->Next(&tag, &ok));
		if(ok) static_cast<CallData*>(tag)->Proceed();
	}
}

int main()
{
    int port = 5001;
    auto GrpcServer = new GRPCServiceImpl;
    GrpcServer->Run();
}
