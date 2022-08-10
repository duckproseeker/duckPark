#include<iostream>
#include<memory>
#include<string>

#include<grpcpp/grpcpp.h>

#include"proto/gen/c++/echo_service.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using echo_service::EchoService;
using echo_service::SimpleMessage;

class echoServiceImpl final : public EchoService::Service
{

    virtual Status Echo(ServerContext* context, const SimpleMessage* request, SimpleMessage* response) override
    {
        std::cout << request->
    }

    virtual Status EchoBody(ServerContext* context, const SimpleMessage* request, SimpleMessage* response) override
    {

    }

    virtual Status EchoDelete(ServerContext* context, const SimpleMessage* request, SimpleMessage* response) override
    {

    }

    virtual Status EchoUnauthorized(ServerContext* context, const SimpleMessage* request, SimpleMessage* response)
    {

    }


};


void runServer()
{

}

int main(int argc, char** argv)
{

}

