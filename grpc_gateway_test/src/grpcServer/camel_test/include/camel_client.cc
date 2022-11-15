
#include <iostream>
#include <memory>
#include <string>

#include <grpcpp/grpcpp.h>

#include "protobuf/camel-grpc.grpc.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using camel::api::AgvService;
using camel::api::GamepadControl;
using camel::api::Token;

class AgvServiceClient {
 public:
  AgvServiceClient(std::shared_ptr<Channel> channel)
      : stub_(AgvService::NewStub(channel)) {}

  // Assembles the client's payload, sends it and presents the response back
  // from the server.
  std::string ApplyStickControl(const bool& flag) {
    // Data we are sending to the server.
    GamepadControl request;
    request.set_force(flag);

    // Container for the data we expect from the server.
    Token reply;

    // Context for the client. It could be used to convey extra information to
    // the server and/or tweak certain RPC behaviors.
    ClientContext context;

    // The actual RPC.
    Status status = stub_->ApplyStickControl(&context, request, &reply);

    // Act upon its status.
    if (status.ok()) {
      std::string res = "{\"key:\" " + reply.key() + ",\"result\":{\"code\": " + std::to_string(reply.result().errorcode()) + \
                         "\"message\": "  + reply.result().message() + "}}"; 
      return res;
    } else {
      std::cout << status.error_code() << ": " << status.error_message()
                << std::endl;
      return "RPC failed";
    }
  }

 private:
  std::unique_ptr<AgvService::Stub> stub_;
};

int main(int argc, char** argv) {
  // Instantiate the client. It requires a channel, out of which the actual RPCs
  // are created. This channel models a connection to an endpoint specified by
  // the argument "--target=" which is the only expected argument.
  // We indicate that the channel isn't authenticated (use of
  // InsecureChannelCredentials()).
  std::string target_str;
  std::string arg_str("--target");
  if (argc > 1) {
    std::string arg_val = argv[1];
    size_t start_pos = arg_val.find(arg_str);
    if (start_pos != std::string::npos) {
      start_pos += arg_str.size();
      if (arg_val[start_pos] == '=') {
        target_str = arg_val.substr(start_pos + 1);
      } else {
        std::cout << "The only correct argument syntax is --target="
                  << std::endl;
        return 0;
      }
    } else {
      std::cout << "The only acceptable argument is --target=" << std::endl;
      return 0;
    }
  } else {
    target_str = "localhost:8090";
  }
  AgvServiceClient AgvService(
      grpc::CreateChannel(target_str, grpc::InsecureChannelCredentials()));
  //std::string user("world");
  bool flag = true;
  std::string reply = AgvService.ApplyStickControl(true);
  std::cout << "Greeter received: " << reply << std::endl;

  return 0;
}
