#!/bin/bash

protoc -I proto/echoService/ --cpp_out=proto/gen/c++/ proto/echoService/echo_service.proto
protoc -I proto/echoService/ --grpc_out=proto/gen/c++ --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` proto/echoService/echo_service.proto
