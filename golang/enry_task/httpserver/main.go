package main

import (
	"context"
	"encoding/gob"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/wxquare/entry_task/conf"
	"github.com/wxquare/entry_task/log"
	gpool "github.com/wxquare/entry_task/pool"
	pb "github.com/wxquare/entry_task/proto/user/proto"
	"github.com/wxquare/entry_task/rpc"
)

var config conf.HTTPConf
var pool *gpool.GPool

func init() {
	var confFile string
	flag.StringVar(&confFile, "c", "./httpserver.yaml", "config file")
	flag.Parse()

	err := conf.ConfParser(confFile, &config)
	if err != nil {
		log.Error.Println("Parser config failed, err:", err.Error())
		os.Exit(-1)
	}

	// initialize connection pool
	pool, err = gpool.NewPool(func() (*net.Conn, error) {
		conn, err := net.Dial("tcp", config.Rpcserver.Addr)
		if err != nil {
			return nil, err
		}
		return &conn, nil
	},
		config.Pool.Initsize,
		config.Pool.Capacity,
		time.Duration(config.Pool.Maxidle)*time.Second)

	if err != nil {
		log.Debug.Println("InitPool failed, err:", err.Error())
		os.Exit(-2)
	}
}

// DestoryPool destroy connection pool
func DestoryPool() {
	pool.Close()
}

// clientWrap
type clientWrap struct {
	conn   *gpool.Conn
	client rpc.RPCClient
}

// get client
func getRPCClient() (*clientWrap, error) {
	ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(30*time.Millisecond))
	conn, err := pool.Get(ctx)
	// call cancel to avoid leak
	cancel()
	if err != nil {
		return nil, err
	}
	client := rpc.NewRPCClient(*conn.C)
	return &clientWrap{conn: conn, client: *client}, nil
}

// free client
func freeRPCClient(wrap *clientWrap) {
	err := pool.Put(wrap.conn)
	if err != nil {
		log.Error.Println("Failed to reclaime conn, err:", err.Error())
	}
}

// cleanup global objects
func finalize() {
	DestoryPool()
}

func main() {
	defer finalize()

	gob.Register(pb.LoginRequest{})
	gob.Register(pb.LoginResponse{})
	gob.Register(pb.CommRequest{})
	gob.Register(pb.EditRequest{})
	gob.Register(pb.EditResponse{})

	fs := http.FileServer(http.Dir("./static/"))
	http.Handle("/static/", http.StripPrefix("/static/", fs))
	// better code ???
	fs1 := http.FileServer(http.Dir("./upload/images/"))
	http.Handle("/upload/images/", http.StripPrefix("/upload/images/", fs1))

	http.HandleFunc("/login", loginHandler)
	http.HandleFunc("/logout", logoutHandler)
	http.HandleFunc("/getuserinfo", getUserinfoHandler)
	http.HandleFunc("/editnickname", editNicknameHandler)
	http.HandleFunc("/uploadpic", uploadHeadurlHandler)

	log.Info.Println("http server run ...")
	err := http.ListenAndServe(fmt.Sprintf("%s:%d", config.Server.IP, config.Server.Port), nil)
	if err != nil {
		log.Error.Println("http server startup error", err)
		os.Exit(-1)
	}
}
