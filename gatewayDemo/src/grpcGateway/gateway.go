package gateway

import (
	"context"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	gwCamel "gateway/protobuf/gen/go/camel"
	gwDefender "gateway/protobuf/gen/go/defender"
)

var (
	baseCtx = context.Background()
	opts    = []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
)

func RunCamelGateway(addr, gwaddr string) error {
	ctx, cancel := context.WithCancel(baseCtx)
	defer cancel()
	mux := runtime.NewServeMux()
	err := gwCamel.RegisterAgvServiceHandlerFromEndpoint(ctx, mux, addr, opts)
	if err != nil {
		return err
	}

	return ginStart(mux, gwaddr)
}

func RunDefenderGateway(addr, gwaddr string) error {
	ctx, cancel := context.WithCancel(baseCtx)
	defer cancel()
	mux := runtime.NewServeMux()
	err := gwDefender.RegisterDefenderServiceHandlerFromEndpoint(ctx, mux, addr, opts)
	if err != nil {
		return err
	}

	return ginStart(mux, gwaddr)
}
