package gateway

import (
	log "gateway/log"

	"net/http"
	"github.com/gin-gonic/gin"
)

var RequestNeedInfo = []string{
	"/camel/v1/SendToAgvs",
	"/camel/v1/RoutePlan",
	"/camel/v1/SetAvoidanceArea",
	"/camel/v1/CarRestart",
	"/camel/v1/UpdateStationPose",
	"/camel/v1/TaskAllocationOperation",
	"/camel/v1/AssignAllocationTasks",
	"/defender/v1/SoftwareUpgrade",
	"/defender/v1/SoftwareBackup",
	"/defender/v1/SoftwareRollback",
	"/defender/v1/SoftwareDowngrade",
}

func logInfo(c *gin.Context) {
	log.Info("HTTP request from", c.Request.RemoteAddr, ":", c.Request.Method, c.Request.URL)
}

func logDebug(c *gin.Context) {
	log.Debug("HTTP request from", c.Request.RemoteAddr, ":", c.Request.Method, c.Request.URL)
}

func record(c *gin.Context) {
	var need = false
	for _, r := range RequestNeedInfo {
		if c.Request.RequestURI == r {
			need = true
		}
	}

	if need {
		logInfo(c)
	} else {
		logDebug(c)
	}
}

//自定义路由中间件
func WrapH(h http.Handler) gin.HandlerFunc {
	return func(c *gin.Context) {
		go record(c.Copy())
		h.ServeHTTP(c.Writer, c.Request)
	}
}

func ginStart(mux http.Handler,addr string) error{
	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()

	//将所有请求绑定到grpc路由上
	router.Use(WrapH(mux))
	return router.Run(addr)
}