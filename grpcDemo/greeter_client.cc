#include<iostream>
#include<memory>
#include<string>

#include<grpcpp/grpcpp.h>

#include"helloWorld.grpc.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using test::Greeter;
using test::HelloReplay;
using test::HelloRequest;

class GreeterClient
{
public:
    GreeterClient(std::shared_ptr<Channel> channel)
    : stub_(Greeter::NewStub(channel)){}

    std::string SayHello(const std::string &user)
    {
        //发送给服务端的数据
        HelloRequest request;
        request.set_name(user);

        //从服务端接收的数据
        HelloReplay replay;
        //保存传递客户端的一些额外信息
        ClientContext context;
        Status status = stub_->SayHello(&context, request, &replay);

        if(status.ok())
        {
            return replay.message();
        }
        else
        {
            std::cout << status.error_code() << ": " << status.error_message() << std::endl;
            return "RPC failed";
        }

    }

private:
    std::unique_ptr<Greeter::Stub> stub_;
};

int main(int argc, char **argv)
{
    std::string target_str;
    std::string arg_str("--target");
    if(argc > 1)
    {
        std::string arg_val = argv[1];
        size_t start_pos = arg_val.find(arg_str);
        if(start_pos != std::string::npos)
        {
            start_pos += arg_str.size();
            if(arg_val[start_pos] == '=')
            {
                target_str = arg_val.substr(start_pos + 1);
            }
            else
            {
                std::cout << "The only correct argument syntax is --target=" << std::endl;
                return 0;
            }
        }
        else
        {
            std::cout << "The only acceptable argument is --target=" << std::endl;
            return 0;
        }
    }
    else
    {
        target_str = "localhost:50051";
    }

    GreeterClient greeter(grpc::CreateChannel(target_str, grpc::InsecureChannelCredentials()));
    std::string user("world");
    std::string replay = greeter.SayHello(user);
    std::cout << "Greeter received: " << replay << std::endl;

    return 0;
}
