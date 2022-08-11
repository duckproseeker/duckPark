#include "proto/gen/c++/responseBody.grpc.pb.h"

#include <iostream>
#include <memory>
#include <string>

#include<grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using grpc::ServerWriter;
using responseBody::ResponseBodyService;
using responseBody::ResponseBodyIn;
using responseBody::ResponseBodyOut;
using responseBody::RepeatedResponseBodyOut;
using responseBody::RepeatedResponseStrings;

class ServiceImpl : public ResponseBodyService::Service {
public:

    virtual Status GetResponseBody(ServerContext* context, const ResponseBodyIn* request, ResponseBodyOut* response)
    {
        std::string data = request->data();
        response->mutable_response()->set_data(data);

        return Status::OK;
    }

    virtual Status ListResponseBodies(ServerContext* context, const ResponseBodyIn* request, RepeatedResponseBodyOut* response)
    {
        std::string data = request->data();
        response->add_response()->set_data(data);

        return Status::OK;
    }

    virtual Status ListResponseStrings(ServerContext* context, const ResponseBodyIn* request, RepeatedResponseStrings* response)
    {
        if(request->data() == "empty")
        {
            response->add_values("");

            return Status::OK;
        }

        response->add_values("hello");
        response->add_values(request->data());

        return Status::OK;

    }

    virtual Status GetResponseBodyStream(ServerContext* context, const ResponseBodyIn* request, ServerWriter< ResponseBodyOut>* writer)
    {
        

    }

  };


void RunServer()
{
    std::string server_address("0.0.0.0:8080");
    ServiceImpl service;

    // //启用默认健康检查服务
    // grpc::EnableDefaultHealthCheckService(true);
    // grpc::reflection::InitProtoReflectionServerBuilderPlugin();

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

