package main

import (
	config "gateway/config"
	gw "gateway/grpcGateway"
	log "gateway/log"
)

/*
TODO:
	1.优化代码整体框架
	2.实现对客户端访问接口的日志输出
	3.根据不同接口设置日志级别
*/

func init() {

	//初始化配置文件和日志格式
	log.Init()
	config.Init()

	log.SetLevel(config.GetLogLevel())
}

func main() {

	camelIp := config.GetCamelIp()
	defenderIp := config.GetDefenderIp()
	log.Info("camel gateway serve:", camelIp)
	log.Info("defender gateway serve:", defenderIp)

	//创建协程监听defender的request
	go func() {
		err := gw.RunDefenderGateway(defenderIp, config.GetDefenderGatewayIp())
		if err != nil {
			log.Error("defender gateway start failed,", err)
		}
	}()

	err := gw.RunCamelGateway(camelIp, config.GetCamelGatewayIp())
	if err != nil {
		log.Error("camel gateway start failed,", err)
	}
}
