// Generated by the gRPC C++ plugin.
// If you make any local change, they will be lost.
// source: responseBody.proto

#include "responseBody.pb.h"
#include "responseBody.grpc.pb.h"

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
namespace responseBody {

static const char* ResponseBodyService_method_names[] = {
  "/responseBody.ResponseBodyService/GetResponseBody",
  "/responseBody.ResponseBodyService/ListResponseBodies",
  "/responseBody.ResponseBodyService/ListResponseStrings",
  "/responseBody.ResponseBodyService/GetResponseBodyStream",
};

std::unique_ptr< ResponseBodyService::Stub> ResponseBodyService::NewStub(const std::shared_ptr< ::grpc::ChannelInterface>& channel, const ::grpc::StubOptions& options) {
  (void)options;
  std::unique_ptr< ResponseBodyService::Stub> stub(new ResponseBodyService::Stub(channel, options));
  return stub;
}

ResponseBodyService::Stub::Stub(const std::shared_ptr< ::grpc::ChannelInterface>& channel, const ::grpc::StubOptions& options)
  : channel_(channel), rpcmethod_GetResponseBody_(ResponseBodyService_method_names[0], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_ListResponseBodies_(ResponseBodyService_method_names[1], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_ListResponseStrings_(ResponseBodyService_method_names[2], options.suffix_for_stats(),::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_GetResponseBodyStream_(ResponseBodyService_method_names[3], options.suffix_for_stats(),::grpc::internal::RpcMethod::SERVER_STREAMING, channel)
  {}

::grpc::Status ResponseBodyService::Stub::GetResponseBody(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::responseBody::ResponseBodyOut* response) {
  return ::grpc::internal::BlockingUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::ResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_GetResponseBody_, context, request, response);
}

void ResponseBodyService::Stub::async::GetResponseBody(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::ResponseBodyOut* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::ResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_GetResponseBody_, context, request, response, std::move(f));
}

void ResponseBodyService::Stub::async::GetResponseBody(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::ResponseBodyOut* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_GetResponseBody_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::responseBody::ResponseBodyOut>* ResponseBodyService::Stub::PrepareAsyncGetResponseBodyRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::responseBody::ResponseBodyOut, ::responseBody::ResponseBodyIn, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_GetResponseBody_, context, request);
}

::grpc::ClientAsyncResponseReader< ::responseBody::ResponseBodyOut>* ResponseBodyService::Stub::AsyncGetResponseBodyRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncGetResponseBodyRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::Status ResponseBodyService::Stub::ListResponseBodies(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::responseBody::RepeatedResponseBodyOut* response) {
  return ::grpc::internal::BlockingUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_ListResponseBodies_, context, request, response);
}

void ResponseBodyService::Stub::async::ListResponseBodies(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseBodyOut* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_ListResponseBodies_, context, request, response, std::move(f));
}

void ResponseBodyService::Stub::async::ListResponseBodies(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseBodyOut* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_ListResponseBodies_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::responseBody::RepeatedResponseBodyOut>* ResponseBodyService::Stub::PrepareAsyncListResponseBodiesRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::responseBody::RepeatedResponseBodyOut, ::responseBody::ResponseBodyIn, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_ListResponseBodies_, context, request);
}

::grpc::ClientAsyncResponseReader< ::responseBody::RepeatedResponseBodyOut>* ResponseBodyService::Stub::AsyncListResponseBodiesRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncListResponseBodiesRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::Status ResponseBodyService::Stub::ListResponseStrings(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::responseBody::RepeatedResponseStrings* response) {
  return ::grpc::internal::BlockingUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseStrings, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), rpcmethod_ListResponseStrings_, context, request, response);
}

void ResponseBodyService::Stub::async::ListResponseStrings(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseStrings* response, std::function<void(::grpc::Status)> f) {
  ::grpc::internal::CallbackUnaryCall< ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseStrings, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_ListResponseStrings_, context, request, response, std::move(f));
}

void ResponseBodyService::Stub::async::ListResponseStrings(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseStrings* response, ::grpc::ClientUnaryReactor* reactor) {
  ::grpc::internal::ClientCallbackUnaryFactory::Create< ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(stub_->channel_.get(), stub_->rpcmethod_ListResponseStrings_, context, request, response, reactor);
}

::grpc::ClientAsyncResponseReader< ::responseBody::RepeatedResponseStrings>* ResponseBodyService::Stub::PrepareAsyncListResponseStringsRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderHelper::Create< ::responseBody::RepeatedResponseStrings, ::responseBody::ResponseBodyIn, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(channel_.get(), cq, rpcmethod_ListResponseStrings_, context, request);
}

::grpc::ClientAsyncResponseReader< ::responseBody::RepeatedResponseStrings>* ResponseBodyService::Stub::AsyncListResponseStringsRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  auto* result =
    this->PrepareAsyncListResponseStringsRaw(context, request, cq);
  result->StartCall();
  return result;
}

::grpc::ClientReader< ::responseBody::ResponseBodyOut>* ResponseBodyService::Stub::GetResponseBodyStreamRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request) {
  return ::grpc::internal::ClientReaderFactory< ::responseBody::ResponseBodyOut>::Create(channel_.get(), rpcmethod_GetResponseBodyStream_, context, request);
}

void ResponseBodyService::Stub::async::GetResponseBodyStream(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn* request, ::grpc::ClientReadReactor< ::responseBody::ResponseBodyOut>* reactor) {
  ::grpc::internal::ClientCallbackReaderFactory< ::responseBody::ResponseBodyOut>::Create(stub_->channel_.get(), stub_->rpcmethod_GetResponseBodyStream_, context, request, reactor);
}

::grpc::ClientAsyncReader< ::responseBody::ResponseBodyOut>* ResponseBodyService::Stub::AsyncGetResponseBodyStreamRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq, void* tag) {
  return ::grpc::internal::ClientAsyncReaderFactory< ::responseBody::ResponseBodyOut>::Create(channel_.get(), cq, rpcmethod_GetResponseBodyStream_, context, request, true, tag);
}

::grpc::ClientAsyncReader< ::responseBody::ResponseBodyOut>* ResponseBodyService::Stub::PrepareAsyncGetResponseBodyStreamRaw(::grpc::ClientContext* context, const ::responseBody::ResponseBodyIn& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncReaderFactory< ::responseBody::ResponseBodyOut>::Create(channel_.get(), cq, rpcmethod_GetResponseBodyStream_, context, request, false, nullptr);
}

ResponseBodyService::Service::Service() {
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      ResponseBodyService_method_names[0],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< ResponseBodyService::Service, ::responseBody::ResponseBodyIn, ::responseBody::ResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](ResponseBodyService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::responseBody::ResponseBodyIn* req,
             ::responseBody::ResponseBodyOut* resp) {
               return service->GetResponseBody(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      ResponseBodyService_method_names[1],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< ResponseBodyService::Service, ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseBodyOut, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](ResponseBodyService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::responseBody::ResponseBodyIn* req,
             ::responseBody::RepeatedResponseBodyOut* resp) {
               return service->ListResponseBodies(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      ResponseBodyService_method_names[2],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< ResponseBodyService::Service, ::responseBody::ResponseBodyIn, ::responseBody::RepeatedResponseStrings, ::grpc::protobuf::MessageLite, ::grpc::protobuf::MessageLite>(
          [](ResponseBodyService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::responseBody::ResponseBodyIn* req,
             ::responseBody::RepeatedResponseStrings* resp) {
               return service->ListResponseStrings(ctx, req, resp);
             }, this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      ResponseBodyService_method_names[3],
      ::grpc::internal::RpcMethod::SERVER_STREAMING,
      new ::grpc::internal::ServerStreamingHandler< ResponseBodyService::Service, ::responseBody::ResponseBodyIn, ::responseBody::ResponseBodyOut>(
          [](ResponseBodyService::Service* service,
             ::grpc::ServerContext* ctx,
             const ::responseBody::ResponseBodyIn* req,
             ::grpc::ServerWriter<::responseBody::ResponseBodyOut>* writer) {
               return service->GetResponseBodyStream(ctx, req, writer);
             }, this)));
}

ResponseBodyService::Service::~Service() {
}

::grpc::Status ResponseBodyService::Service::GetResponseBody(::grpc::ServerContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::ResponseBodyOut* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status ResponseBodyService::Service::ListResponseBodies(::grpc::ServerContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseBodyOut* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status ResponseBodyService::Service::ListResponseStrings(::grpc::ServerContext* context, const ::responseBody::ResponseBodyIn* request, ::responseBody::RepeatedResponseStrings* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status ResponseBodyService::Service::GetResponseBodyStream(::grpc::ServerContext* context, const ::responseBody::ResponseBodyIn* request, ::grpc::ServerWriter< ::responseBody::ResponseBodyOut>* writer) {
  (void) context;
  (void) request;
  (void) writer;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}


}  // namespace responseBody

