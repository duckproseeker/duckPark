package main

import (
	"flag"
	"fmt"
	"net/http"
    "log"
	gw "hello/protobuf/gen/go"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
)

var (
	echoEndpoint = flag.String("echo_endpoint", "localhost:50051", "endpoint of YourService")
)

func run() error {

	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	mux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithInsecure()}
	err := gw.RegisterGreeterHandlerFromEndpoint(ctx, mux, *echoEndpoint, opts)

	if err != nil {
		return err
	}

	return http.ListenAndServe(":5001", mux)
}

func main() {
    log.Println("Serving gRPC-Gateway on http://0.0.0.0:5001")

	if err := run(); err != nil {
		fmt.Print(err.Error())
	}
}