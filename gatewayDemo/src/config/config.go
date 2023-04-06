package config

import (
	"encoding/json"
	"os"
	"strings"

	log "gateway/log"
)

type baseConfig struct {
	CamelIp           string `json:"camelIp"`
	DefenderIp        string `json:"defenderIp"`
	CamelGatewayIp    string `json:"camelGatewayIp"`
	DefenderGatewayIp string `json:"defenderGatewayIp"`
	Loglevel          string `json:"logLevel"`
}

var (
	configPath = "./config.json"
	conf       baseConfig
)

func parseJson(filePath string) (err error) {
	var (
		context []byte
	)

	if context, err = os.ReadFile(filePath); err != nil {
		log.Error(err.Error())
		return
	}

	if err = json.Unmarshal(context, &conf); err != nil {
		log.Error(err.Error())
		return
	}

	log.Info("init config successfully")
	return
}

func Init() {
	parseJson(configPath)
}

func GetCamelIp() string {
	if len(strings.TrimSpace(conf.CamelIp)) == 0 {
		return "127.0.0.1:5001"
	}

	return conf.CamelIp
}

func GetDefenderIp() string {
	if len(strings.TrimSpace(conf.DefenderIp)) == 0 {
		return "127.0.0.1:5002"
	}

	return conf.DefenderIp
}

func GetCamelGatewayIp() string {
	if len(strings.TrimSpace(conf.CamelGatewayIp)) == 0 {
		return "0.0.0.0:5101"
	}

	return conf.CamelGatewayIp
}

func GetDefenderGatewayIp() string {
	if len(strings.TrimSpace(conf.DefenderGatewayIp)) == 0 {
		return "0.0.0.0:5102"
	}

	return conf.DefenderGatewayIp
}

func GetLogLevel() string {
	if len(strings.TrimSpace(conf.Loglevel)) == 0 {
		return "INFO"
	}

	return conf.Loglevel
}
