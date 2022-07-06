#include<iostream>
#include<memory>
#include<string>


#include<grpcpp/ext/proto_server_reflection_plugin.h>
#include<grpcpp/grpcpp.h>
#include<grpcpp/health_check_service_interface.h>

#include"helloWorld.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using test::Greeter;
using test::HelloReplay;
using test::HelloRequest;

class GreeterServiceImpl final : public Greeter::Service
{
    Status SayHello(ServerContext *context,  HelloRequest *request,  HelloReplay *replay)
    {
        std::string prefix("Hello ");
        replay->set_message(prefix + request->name());
        return Status::OK;
    }
};

void RunServer()
{
    std::string server_address("0.0.0.0:50051");
    GreeterServiceImpl service;

    //启用默认健康检查服务
    grpc::EnableDefaultHealthCheckService(true);
    grpc::reflection::InitProtoReflectionServerBuilderPlugin();

    ServerBuilder builder;
    //不需要认证监听端口（不安全）
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    //以这种方式创建的服务端实例与客户端之间的通信是同步的
    builder.RegisterService(&service);
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;
    //阻塞，等待其他线程关闭
    server->Wait();
}

int main(int argc, char **argv)
{
    RunServer();

    return 0;
}

