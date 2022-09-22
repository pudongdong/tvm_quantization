package log

import (
	"io"
	"log"
	"os"
)

var (
	Info  *log.Logger
	Debug *log.Logger
	Error *log.Logger
)

func init() {
	DebugFile, err := os.OpenFile("debug.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalln("Failed to open error log file: ", err)
		return
	}

	Infofile, err := os.OpenFile("info.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalln("Failed to open error log file: ", err)
		return
	}

	Errorfile, err := os.OpenFile("error.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalln("Failed to open error log file: ", err)
		return
	}

	Debug = log.New(io.MultiWriter(DebugFile, os.Stdout), "Debug: ", log.Ldate|log.Ltime|log.Lshortfile)
	Info = log.New(io.MultiWriter(Infofile, os.Stdout), "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)
	Error = log.New(io.MultiWriter(Errorfile, os.Stderr), "Error: ", log.Ldate|log.Ltime|log.Lshortfile)
}
