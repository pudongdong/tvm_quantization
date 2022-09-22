package main

import (
	"encoding/gob"
	"flag"
	"fmt"
	"os"

	"github.com/wxquare/entry_task/conf"
	"github.com/wxquare/entry_task/log"
	"github.com/wxquare/entry_task/proto/user/proto"
	"github.com/wxquare/entry_task/rpc"
)

var config conf.TCPConf

func init() {

	// parser config
	var confFile string
	flag.StringVar(&confFile, "c", "./tcpserver.yaml", "config file")
	flag.Parse()

	err := conf.ConfParser(confFile, &config)
	if err != nil {
		log.Error.Println("parser config failed:", err.Error())
		os.Exit(-1)
	}
	// init redis
	err = initRedisConn(&config)
	if err != nil {
		log.Error.Println("initRedisConn failed:", err.Error())
		os.Exit(-1)
	}

	// init db
	err = initDbConn(&config)
	if err != nil {
		log.Error.Println("initDbConn failed:", err.Error())
		os.Exit(-1)
	}
	log.Info.Println("init successfully!")
}

// cleanup
func finalize() {
	closeCache()
	closeDB()
}

func main() {
	defer finalize()

	gob.Register(proto.LoginRequest{})
	gob.Register(proto.LoginResponse{})
	gob.Register(proto.CommRequest{})
	gob.Register(proto.EditRequest{})
	gob.Register(proto.EditResponse{})

	addr := fmt.Sprintf(":%d", config.Server.Port)
	rpcServer := rpc.NewServer(addr)

	userServer := &UserServer{}
	rpcServer.Register("Login", Login)
	rpcServer.Register("Logout", userServer.Logout)
	rpcServer.Register("EditUserInfo", userServer.EditUserInfo)
	rpcServer.Register("GetUserInfo", userServer.GetUserInfo)

	log.Info.Printf("start to listen on localhost:%d \n", config.Server.Port)

	rpcServer.Run()
}
