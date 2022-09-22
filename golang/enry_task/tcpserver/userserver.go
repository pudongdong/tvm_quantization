package main

import (
	errorcode "github.com/wxquare/entry_task/errorcode"
	"github.com/wxquare/entry_task/log"
	pb "github.com/wxquare/entry_task/proto/user/proto"
	"github.com/wxquare/entry_task/utils"
)

// UserServer for rcpclient
type UserServer struct {
}

// Login login handler
func Login(in pb.LoginRequest) (pb.LoginResponse, error) {
	// query userinfo
	log.Debug.Printf("req=%+v", in)
	user, err := getUserInfo(in.Username)
	if err != nil {
		log.Error.Println(" -- Failed to getUserInfo, ", in.Username, "@", in.Passwd, ", err:", err.Error())
		return pb.LoginResponse{Code: errorcode.CodeTCPFailedGetUserInfo, Msg: errorcode.CodeMsg[errorcode.CodeTCPFailedGetUserInfo]}, nil
	}

	// verify passwd
	if utils.Md5String(in.Passwd+user.Skey) != user.Passwd {
		log.Error.Println(" -- Failed to match passwd ", in.Username, "@", in.Passwd, " salt:", user.Skey, " realpwd:", user.Passwd)
		return pb.LoginResponse{Code: errorcode.CodeTCPPasswdErr, Msg: errorcode.CodeMsg[errorcode.CodeTCPPasswdErr]}, nil
	}

	// set cache
	token := utils.GenerateToken(user.Username)
	err = setTokenInfo(user, token)
	if err != nil {
		log.Error.Println(" -- Failed to set token for user:", user.Username, " err:", err.Error())
		return pb.LoginResponse{Code: errorcode.CodeTCPInternelErr, Msg: errorcode.CodeMsg[errorcode.CodeTCPInternelErr]}, nil
	}
	log.Debug.Println(" -- Login succesfully, ", in.Username, "@", in.Passwd, " with token:", token)
	return pb.LoginResponse{Username: user.Username, Nickname: user.Nickname, Headurl: user.Headurl, Token: token, Code: errorcode.CodeSucc}, nil
}

// GetUserInfo get user info
func (server *UserServer) GetUserInfo(in pb.CommRequest) (pb.LoginResponse, error) {
	log.Debug.Println(" -- GetUserInfo access from:", in.Username, " with token:", in.Token)
	// get and verify token

	if len(in.Token) != 32 {
		log.Error.Println(" -- Error: invalid token,need to login again.", in.Token)
		return pb.LoginResponse{Code: errorcode.CodeTCPInvalidToken, Msg: errorcode.CodeMsg[errorcode.CodeTCPInvalidToken]}, nil
	}
	// get userinfo and compare username
	user, err := getTokenInfo(in.Token)
	if err != nil {
		log.Error.Println(" -- Failed to get token,need to login again", in.Token, " with err:", err.Error())
		return pb.LoginResponse{Code: errorcode.CodeTCPTokenExpired, Msg: errorcode.CodeMsg[errorcode.CodeTCPTokenExpired]}, nil
	}

	// check if username is the same
	if user.Username != in.Username {
		log.Error.Println(" -- Error: token info not match:", in.Username, " while cache:", user.Username)
		return pb.LoginResponse{Code: errorcode.CodeTCPUserInfoNotMatch, Msg: errorcode.CodeMsg[errorcode.CodeTCPUserInfoNotMatch]}, nil
	}
	log.Debug.Println(" -- Succ to GetUserInfo :", in.Username, " with token:", in.Token)
	return pb.LoginResponse{Username: user.Username, Nickname: user.Nickname, Headurl: user.Headurl, Token: in.Token, Code: errorcode.CodeSucc}, nil
}

// EditUserInfo edit userinfo (nickname, headurl or both)
func (server *UserServer) EditUserInfo(in pb.EditRequest) (pb.EditResponse, error) {
	log.Debug.Println(" -- EditUserInfo access from:", in.Username, " with token:", in.Token)
	token := in.Token
	if len(token) != 32 {
		log.Error.Println(" -- Error: invalid token:", in.Token)
		return pb.EditResponse{Code: errorcode.CodeTCPInvalidToken, Msg: errorcode.CodeMsg[errorcode.CodeTCPInvalidToken]}, nil
	}
	// get userinfo and compare username
	user, err := getTokenInfo(token)
	if err != nil {
		log.Error.Println(" -- Failed to get token:", in.Token, " with err:", err.Error())
		return pb.EditResponse{Code: errorcode.CodeTCPTokenExpired, Msg: errorcode.CodeMsg[errorcode.CodeTCPTokenExpired]}, nil
	}
	// check if username is the same
	if user.Username != in.Username {
		log.Error.Println(" -- Error: token info not match:", in.Username, " while cache:", user.Username)
		return pb.EditResponse{Code: errorcode.CodeTCPUserInfoNotMatch, Msg: errorcode.CodeMsg[errorcode.CodeTCPUserInfoNotMatch]}, nil
	}

	affectRows := editUserInfo(in.Username, in.Nickname, in.Headurl, in.Token, in.Mode)
	log.Debug.Println(" -- Succ to edit userinfo, affected rows is:", affectRows)
	return pb.EditResponse{Code: errorcode.CodeSucc, Msg: errorcode.CodeMsg[errorcode.CodeSucc]}, nil
}

// Logout logout
func (server *UserServer) Logout(in pb.CommRequest) (pb.EditResponse, error) {
	log.Debug.Println(" -- Logout access from:", in.Token)
	err := delTokenInfo(in.Token)
	if err != nil {
		log.Error.Println(" -- Failed to delTokenInfo :", err.Error())
	}
	log.Debug.Println(" -- Succ to logout:", in.Token)
	return pb.EditResponse{Code: errorcode.CodeSucc, Msg: errorcode.CodeMsg[errorcode.CodeSucc]}, nil
}
