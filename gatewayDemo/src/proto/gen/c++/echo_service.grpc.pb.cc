// Generated by the gRPC C++ plugin.
// If you make any local change, they will be lost.
// source: echo_service.proto

#include "echo_service.pb.h"
#include "echo_service.grpc.pb.h"

#include <functional>
#include <grpcpp/impl/codegen/async_stream.h>
#include <grpcpp/impl/codegen/async_unary_call.h>
#include <grpcpp/impl/codegen/channel_interface.h>
#include <grpcpp/impl/codegen/client_unary_call.h>
#include <grpcpp/impl/codegen/client_callback.h>
#include <grpcpp/impl/codegen/message_allocator.h>
#include <grpcpp/impl/codegen/method_handler.h>
#include <grpcpp/impl/codegen/rpc_service_method.h>
#include <grpcpp/impl/codegen/server_callback.h>
#include <grpcpp/impl/codegen/server_callback_handlers.h>
#include <grpcpp/impl/codegen/server_context.h>
#include <grpcpp/impl/codegen/service_type.h>
#include <grpcpp/impl/codegen/sync_stream.h>
namespace echo_service {

static const char* EchoService_method_names[] = {
  "/echo_service.EchoService/Echo",
  "/echo_service.EchoService/EchoBody",
  "/echo_service.EchoService/EchoDelete",
  "/echo_service.EchoService/EchoUnauthorized",
};

std::unique_ptr< EchoService::Stub> EchoService::NewStub(const std::shared_ptr< ::grpc::ChannelInterface>& channel, const ::grpc::StubOptions& options) {
  (void)options;
  std::unique_ptr< EchoService::Stub> stub(new EchoService::Stub(channel, options));
  return stub;
}

EchoService::Stub::Stub(const std::shared_ptr< ::grpc::ChannelInterface>& channel, const ::grpc::StubOptions& options)
  : channel_(channel), rpcmethod_Echo_(EchoService_method_names[0], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_EchoBody_(EchoService_method_names[1], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_EchoDelete_(EchoService_method_names[2], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_EchoUnauthorized_(EchoService_method_names[3], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  {}

::grpc::Status EchoService::Stub::Echo(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::echo_service::SimpleMessage* response) {
  return ::grpc::internal::BlockingUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_Echo_, context, request, response);
}

void EchoService::Stub::async::Echo(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_Echo_, context, request, response, std::move(f));
}

void EchoService::Stub::async::Echo(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_Echo_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::PrepareAsyncEchoRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_Echo_, context, request);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::AsyncEchoRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncEchoRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::Status EchoService::Stub::EchoBody(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::echo_service::SimpleMessage* response) {
  return ::grpc::internal::BlockingUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_EchoBody_, context, request, response);
}

void EchoService::Stub::async::EchoBody(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoBody_, context, request, response, std::move(f));
}

void EchoService::Stub::async::EchoBody(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoBody_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::PrepareAsyncEchoBodyRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_EchoBody_, context, request);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::AsyncEchoBodyRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncEchoBodyRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::Status EchoService::Stub::EchoDelete(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::echo_service::SimpleMessage* response) {
  return ::grpc::internal::BlockingUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_EchoDelete_, context, request, response);
}

void EchoService::Stub::async::EchoDelete(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoDelete_, context, request, response, std::move(f));
}

void EchoService::Stub::async::EchoDelete(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoDelete_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::PrepareAsyncEchoDeleteRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_EchoDelete_, context, request);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::AsyncEchoDeleteRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncEchoDeleteRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::Status EchoService::Stub::EchoUnauthorized(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::echo_service::SimpleMessage* response) {
  return ::grpc::internal::BlockingUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_EchoUnauthorized_, context, request, response);
}

void EchoService::Stub::async::EchoUnauthorized(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoUnauthorized_, context, request, response, std::move(f));
}

void EchoService::Stub::async::EchoUnauthorized(::grpc::ClientContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_EchoUnauthorized_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::PrepareAsyncEchoUnauthorizedRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_EchoUnauthorized_, context, request);
}

::grpc::ClientAsyncResponseReader< ::echo_service::SimpleMessage>* EchoService::Stub::AsyncEchoUnauthorizedRaw(::grpc::ClientContext* context, const ::echo_service::SimpleMessage& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncEchoUnauthorizedRaw(context, request, cq);
  result->StartCall();
  return result;
}

EchoService::Service::Service() {
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      EchoService_method_names[0],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< EchoService::Service, ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](EchoService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::echo_service::SimpleMessage* req,
             ::echo_service::SimpleMessage* resp) {
               return service->Echo(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      EchoService_method_names[1],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< EchoService::Service, ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](EchoService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::echo_service::SimpleMessage* req,
             ::echo_service::SimpleMessage* resp) {
               return service->EchoBody(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      EchoService_method_names[2],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< EchoService::Service, ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](EchoService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::echo_service::SimpleMessage* req,
             ::echo_service::SimpleMessage* resp) {
               return service->EchoDelete(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      EchoService_method_names[3],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< EchoService::Service, ::echo_service::SimpleMessage, ::echo_service::SimpleMessage, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](EchoService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::echo_service::SimpleMessage* req,
             ::echo_service::SimpleMessage* resp) {
               return service->EchoUnauthorized(ctx, req, resp);
             }, this)));
}

EchoService::Service::~Service() {
}

::grpc::Status EchoService::Service::Echo(::grpc::ServerContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status EchoService::Service::EchoBody(::grpc::ServerContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status EchoService::Service::EchoDelete(::grpc::ServerContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status EchoService::Service::EchoUnauthorized(::grpc::ServerContext* context, const ::echo_service::SimpleMessage* request, ::echo_service::SimpleMessage* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}


}  // namespace echo_service

