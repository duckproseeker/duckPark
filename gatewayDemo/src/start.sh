#!/bin/bash

g++  server.cpp proto/gen/c++/*.cc -o server -L/usr/local/lib `pkg-config --libs protobuf grpc++` -pthread -ldl -lgrpc++_reflection
