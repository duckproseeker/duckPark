package main

import (
	"flag"
	"fmt"
	"net/http"
    "log"
	"context"
	"camel/config"
	gw1 "camel/protobuf/gen/go/camel"
	gw2 "camel/protobuf/gen/go/defender"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	//"golang.org/x/net/context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var (
	ConfigPath = "./config.json"
	CamelIp string
	DefenderIp string
	CamelGatewayIp string
	DefenderGatewayIp string
)

var (
	ctx = context.Background()
)

func LoadConfig(){
	err := config.InitConfig(ConfigPath)
	if err != nil {
		fmt.Println(err)
		return
	}

	CamelIp = config.CamelConfig.Host + ":" + config.CamelConfig.Port
	DefenderIp = config.DefenderConfig.Host + ":" + config.DefenderConfig.Port
	CamelGatewayIp = config.CamelGatewayConfig.Host + ":" + config.CamelGatewayConfig.Port
	DefenderGatewayIp = config.DefenderGatewayConfig.Host + ":" + config.DefenderGatewayConfig.Port

}


func CamelGatewayRun() error {

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	mux := runtime.NewServeMux()
	//opts := []grpc.DialOption{grpc.WithInsecure()}
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	CamelEndpoint := flag.String("camel_endpoint", CamelIp, "endpoint of camel")
	err := gw1.RegisterAgvServiceHandlerFromEndpoint(ctx, mux, *CamelEndpoint, opts)

	if err != nil {
		return err
	}
	
	log.Println("proxy camel on Ip:", CamelGatewayIp)	
	return http.ListenAndServe(CamelGatewayIp, mux)
}


func DefenderGatewayRun() error {

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	mux := runtime.NewServeMux()
	//opts := []grpc.DialOption{grpc.WithInsecure()}
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	DefenderEndPoint := flag.String("Defender_endpoint", DefenderIp, "endpoint of defender")
	err := gw2.RegisterDefenderServiceHandlerFromEndpoint(ctx, mux, *DefenderEndPoint, opts)

	if err != nil {
		return err
	}

	log.Println("proxy defender on Ip:" ,DefenderGatewayIp)	
	return http.ListenAndServe(DefenderGatewayIp, mux)
}

func Run(){
	
	if err := DefenderGatewayRun(); err != nil {
		fmt.Print(err.Error())
	}
}

func main() {
	LoadConfig()

	go Run()
	if err := CamelGatewayRun(); err != nil {
		fmt.Print(err.Error())
	}
}
