package main

import (
	"net/http"
	"strconv"

	"github.com/wxquare/entry_task/errorcode"
	"github.com/wxquare/entry_task/log"
	pb "github.com/wxquare/entry_task/proto/user/proto"
)

func ResponseHandler(code int, msg string, data map[string]string) map[string]interface{} {
	if msg == "" {
		msg = errorcode.CodeMsg[code]
	}
	res := make(map[string]interface{})
	res["code"] = code
	res["msg"] = msg
	res["data"] = data
	return res
}

// Login : userlogin handler
func Login(args map[string]string) (int, string, map[string]interface{}) {

	//communicate with rcp server
	client, err := getRPCClient()
	if err != nil {
		log.Error.Println(" Failed to getRPCClient, err:", err.Error())
		return http.StatusInternalServerError, "", ResponseHandler(errorcode.CodeHttpGetRPCClientErr, "", nil)
	}
	defer freeRPCClient(client)

	var Login func(pb.LoginRequest) (pb.LoginResponse, error)
	client.client.CallRPC("Login", &Login)
	rsp, err := Login(pb.LoginRequest{Username: args["username"], Passwd: args["passwd"]})
	if err != nil {
		log.Error.Println(" -- Failed to communicate with TCP server, err:", err.Error())
		return http.StatusOK, "", ResponseHandler(errorcode.CodeHttpErrBackend, "", nil)
	}

	var token string
	log.Debug.Println(" -- Succ get token:", rsp.Token, " code:", rsp.Code)
	if rsp.Code == errorcode.CodeSucc && rsp.Token != "" {
		token = rsp.Token
	}
	return http.StatusOK, token, ResponseHandler(int(rsp.Code), rsp.Msg, map[string]string{"username": rsp.Username, "nickname": rsp.Nickname, "headurl": rsp.Headurl})
}

// Logout : user logout
func Logout(args map[string]string) (int, map[string]interface{}) {

	client, err := getRPCClient()
	if err != nil {
		log.Error.Println(" -- Failed to getRPCClient, err:", err.Error())
		return http.StatusInternalServerError, ResponseHandler(errorcode.CodeHttpGetRPCClientErr, "", nil)
	}
	defer freeRPCClient(client)

	var Logout func(pb.CommRequest) (pb.EditResponse, error)
	client.client.CallRPC("Logout", &Logout)
	rsp, err := Logout(pb.CommRequest{Token: args["token"], Username: args["username"]})
	if err != nil {
		log.Error.Println(" -- Failed to communicate with TCP server, err:", err.Error())
		return http.StatusOK, ResponseHandler(errorcode.CodeHttpErrBackend, "", nil)
	}
	log.Debug.Println("Succ to get response from backend with ", rsp.Code, " and msg:", rsp.Msg)
	return http.StatusOK, ResponseHandler(int(rsp.Code), rsp.Msg, nil)
}

// EditUserinfo  edit user nickname/headurl
func EditUserinfo(args map[string]string) (int, map[string]interface{}) {
	headurl := args["headurl"]
	// get connection
	client, err := getRPCClient()
	if err != nil {
		log.Error.Println(" -- Failed to getRPCClient, err:", err.Error())
		return http.StatusInternalServerError, ResponseHandler(errorcode.CodeHttpGetRPCClientErr, "", nil)
	}
	defer freeRPCClient(client)

	var EditUserInfo func(pb.EditRequest) (pb.EditResponse, error)
	client.client.CallRPC("EditUserInfo", &EditUserInfo)

	// update userinfo
	mode, _ := strconv.Atoi(args["mode"])
	editRsp, err := EditUserInfo(pb.EditRequest{Username: args["username"], Token: args["token"], Nickname: args["nickname"], Headurl: headurl, Mode: uint32(mode)})
	if err != nil {
		log.Error.Println(" -- Failed to communicate with TCP server, err:", err.Error())
		return http.StatusOK, ResponseHandler(errorcode.CodeHttpErrBackend, "", nil)
	}
	data := map[string]string{}
	if editRsp.Code == 0 && headurl != "" {
		data["headurl"] = headurl
	}
	return http.StatusOK, ResponseHandler(int(editRsp.Code), editRsp.Msg, data)
}

// GetUserinfo get userinfo handler
func GetUserinfo(args map[string]string) (int, map[string]interface{}) {
	// communicate with rcp server
	client, err := getRPCClient()
	if err != nil {
		log.Error.Println(" -- Failed to getRPCClient, err:", err.Error())
		return http.StatusInternalServerError, ResponseHandler(errorcode.CodeHttpGetRPCClientErr, "", nil)
	}
	defer freeRPCClient(client)

	var GetUserInfo func(pb.CommRequest) (pb.LoginResponse, error)
	client.client.CallRPC("GetUserInfo", &GetUserInfo)

	rsp, err := GetUserInfo(pb.CommRequest{Token: args["token"], Username: args["username"]})
	if err != nil {
		log.Error.Println(" -- Failed to communicate with TCP server, err:", err.Error())
		return http.StatusOK, ResponseHandler(errorcode.CodeHttpErrBackend, "", nil)
	}
	response := ResponseHandler(int(rsp.Code), rsp.Msg, map[string]string{"username": rsp.Username, "nickname": rsp.Nickname, "headurl": rsp.Headurl})
	return http.StatusOK, response
}

// Auth user getUserInfo to auth
func Auth(args map[string]string) (int, int, string) {
	// communicate with rcp server
	client, err := getRPCClient()
	if err != nil {
		log.Error.Println(" -- Failed to getRPCClient, err:", err.Error())
		return http.StatusInternalServerError, errorcode.CodeHttpGetRPCClientErr, errorcode.CodeMsg[errorcode.CodeHttpGetRPCClientErr]
	}
	defer freeRPCClient(client)

	var GetUserInfo func(pb.CommRequest) (pb.LoginResponse, error)
	client.client.CallRPC("GetUserInfo", &GetUserInfo)

	rsp, err := GetUserInfo(pb.CommRequest{Token: args["token"], Username: args["username"]})
	if err != nil {
		log.Error.Println("Failed to communicate with TCP server, err:", err.Error())
		return http.StatusOK, errorcode.CodeHttpErrBackend, errorcode.CodeMsg[errorcode.CodeHttpErrBackend]
	}
	if rsp.Code == 0 {
		return http.StatusOK, errorcode.CodeSucc, errorcode.CodeMsg[errorcode.CodeSucc]
	}
	return http.StatusOK, int(rsp.Code), rsp.Msg
}
