package gatewaylog

import (
	"io"
	"strings"

	nested "github.com/antonfisher/nested-logrus-formatter"
	"github.com/sirupsen/logrus"
	"gopkg.in/natefinch/lumberjack.v2"
)

var (
	logPath = "D:\\dwk\\go\\log.txt"
)

func Trace(args ...interface{}) {
	//setform()
	logrus.Trace(args)
}
func Debug(args ...interface{}) {
	//setform()
	logrus.Debug(args)
}

func Info(args ...interface{}) {
	//setform()
	logrus.Info(args)
}

func Warn(args ...interface{}) {
	//setform()
	logrus.Warn(args)
}

func Error(args ...interface{}) {
	//setform()
	logrus.Error(args)
}

func Fatal(args ...interface{}) {
	//setform()
	logrus.Fatal(args)
}

func setform() {
	logrus.SetFormatter(&nested.Formatter{
		HideKeys:        true,
		FieldsOrder:     []string{"component", "category"},
		TimestampFormat: "2006-01-02 15:04:05",
		NoColors:        true,
	})
}

func setOutput(out io.Writer) {
	logrus.SetOutput(out)
}

func SetLevel(level string) {
	switch strings.ToLower(level) {
	case "panic":
		logrus.SetLevel(logrus.PanicLevel)
	case "fatal":
		logrus.SetLevel(logrus.FatalLevel)
	case "error":
		logrus.SetLevel(logrus.ErrorLevel)
	case "info":
		logrus.SetLevel(logrus.InfoLevel)
	case "debug":
		logrus.SetLevel(logrus.DebugLevel)
	case "trace":
		logrus.SetLevel(logrus.TraceLevel)
	default:
		Info("not a vaild Log Level: %s", level)
	}

}

func Init() {
	setform()
	//out, err := os.OpenFile(logPath, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0755)
	out := &lumberjack.Logger{
		Filename:   logPath,
		MaxSize:    20,
		MaxBackups: 3,
		MaxAge:     7,
		LocalTime:  true,
		Compress:   true,
	}
	setOutput(out)

}
