#!/bin/bash

protoc -I proto/responseBody/ --cpp_out=proto/gen/c++/ proto/responseBody/responseBody.proto
protoc -I proto/responseBody/ --grpc_out=proto/gen/c++ --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` proto/responseBody/responseBody.proto
