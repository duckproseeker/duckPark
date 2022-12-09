package config

import (
	"encoding/json"
	"io/ioutil"
)

type camel struct {
	Host string `json:"host"`
	Port string `json:"port"`
}

type defender struct {
	Host string `json:"host"`
	Port string `json:"port"`
}

type camel_gateway struct {
	Host string `json:"host"`
	Port string `json:"port"`
}

type defender_gateway struct {
	Host string `json:"host"`
	Port string `json:"port"`
}

type baseConfig struct {
	camel `json:"camel"`
	defender `json:"defender"`
	camel_gateway `json:"camel_gateway"`
	defender_gateway `json:"defender_gateway"`
}

var (
	CamelConfig *camel
	DefenderConfig *defender
	CamelGatewayConfig *camel_gateway
	DefenderGatewayConfig *defender_gateway
)

func InitConfig(filePath string) (err error){
	var (
		context []byte
		conf baseConfig
	)

	if context, err = ioutil.ReadFile(filePath); err != nil {
		//TODO 日志
		return
	}

	if err = json.Unmarshal(context, &conf); err != nil {
		//TODO 日志
		return
	}

	CamelConfig = &conf.camel
	DefenderConfig = &conf.defender
	CamelGatewayConfig = &conf.camel_gateway
	DefenderGatewayConfig = &conf.defender_gateway

	return
}