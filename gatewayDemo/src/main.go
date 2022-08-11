package main

import (
	"flag"
	"fmt"
	"net/http"
	gw "test/proto/responseBody"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
)

var (
	echoEndpoint = flag.String("echo_endpoint", "localhost:8080", "endpoint of YourService")
)

func run() error {

	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	mux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithInsecure()}
	err := gw.RegisterResponseBodyServiceHandlerFromEndpoint(ctx, mux, *echoEndpoint, opts)

	if err != nil {
		return err
	}

	return http.ListenAndServe(":9090", mux)
}

func main() {
	if err := run(); err != nil {
		fmt.Print(err.Error())
	}
}
