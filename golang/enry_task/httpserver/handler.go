package main

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path"
	"strings"
	"time"

	"github.com/wxquare/entry_task/errorcode"
	"github.com/wxquare/entry_task/log"
	"github.com/wxquare/entry_task/utils"
)

// generate upload image file name
func generateImgName(fname, postfix string) string {
	ext := path.Ext(fname)
	fileName := strings.TrimSuffix(fname, ext)
	fileName = utils.Md5String(fileName + postfix)
	return fileName + ext
}

func handleRespnse(w http.ResponseWriter, httpCode int, data map[string]interface{}) {
	w.WriteHeader(httpCode)
	jsondata, err := json.Marshal(data)
	if err != nil {
		log.Error.Println("json marshal error!")
		return
	}
	w.Write(jsondata)
}

// login
func loginHandler(w http.ResponseWriter, r *http.Request) {
	log.Debug.Printf("req = %+v", r)
	// note: default no parse.
	r.ParseForm() // ????
	// no check params
	log.Debug.Printf("%+v\n", r.Form)
	username := r.Form["username"][0]
	passwd := r.Form["passwd"][0]
	if len(passwd) > 32 {
		log.Error.Println("Invalid passwd:", passwd)
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpInvalidPasswd, "", nil))
		return
	}
	log.Debug.Println(" loginHandler access from:", username, "@", passwd)
	ret, token, rsp := Login(map[string]string{"username": username, "passwd": passwd})
	// set cookie
	if ret == http.StatusOK && token != "" {
		http.SetCookie(w, &http.Cookie{
			Name:    "token",
			Value:   token,
			Expires: time.Now().Add(time.Duration(config.Logic.Tokenexpire) * time.Second),
		})
		log.Debug.Println(" -- Set token ", token, "with expire:", config.Logic.Tokenexpire)
	}
	log.Debug.Println(" -- Succ get response from backend with", rsp["code"], " and msg:", rsp["msg"], token)
	if rsp["code"] != errorcode.CodeSucc {
		log.Error.Printf("%+v\v", rsp)
	}
	handleRespnse(w, ret, rsp)
}

// logout
func logoutHandler(w http.ResponseWriter, r *http.Request) {
	log.Debug.Printf("req = %+v", r)
	// check params
	r.ParseForm()
	username := r.Form["username"][0]
	token, err := r.Cookie("token")
	if err != nil {
		log.Error.Println("Failed to get token from cookie, err:", err.Error())
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpTokenNotFound, "", nil))
		return
	}
	if len(token.Value) != 32 {
		log.Error.Println("Invalid token :", token)
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpInvalidToken, "", nil))
		return
	}
	log.Debug.Println(" -- logoutHandler access from:", username, " with token:", token.Value)
	ret, rsp := Logout(map[string]string{"username": username, "token": token.Value})
	log.Debug.Println(" -- Succ to get response from backend with ", rsp["code"], " and msg:", rsp["msg"])
	handleRespnse(w, ret, rsp)
}

// edit nickname
func editNicknameHandler(w http.ResponseWriter, r *http.Request) {
	log.Debug.Printf("req = %+v", r)
	// note: default no parse.
	r.ParseForm()
	// no check
	log.Debug.Printf("r=%+v\n", r)
	username := r.Form["username"][0]
	nickname := r.Form["newnickname"][0]
	token, err := r.Cookie("token")
	log.Debug.Println("access from:", username, " with token:", token, " and newname:", nickname)
	if err != nil {
		log.Error.Println("Failed to get token from cookie, err:", err.Error())
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpGetCookieTokenErr, "", nil))
		return
	}
	if len(token.Value) != 32 {
		log.Error.Println("Invalid token :", token)
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpInvalidToken, "", nil))
		return
	}
	log.Debug.Println(" -- editNicknameHandler access from:", username, " with token:", token, " new nickname:", nickname)
	// communicate with rcp server
	ret, rsp := EditUserinfo(map[string]string{"username": username, "token": token.Value, "nickname": nickname, "headurl": "", "mode": "1"})
	log.Debug.Println(" -- Succ to get response from backend with ", rsp["code"], " and msg:", rsp["msg"])
	handleRespnse(w, ret, rsp)
}

// uploadHeadurlHandle
func uploadHeadurlHandler(w http.ResponseWriter, r *http.Request) {
	// check params
	log.Debug.Printf("req = %+v", r)
	r.ParseForm()
	username := r.Form["username"][0]
	token, err := r.Cookie("token")
	log.Debug.Println("access from:", username, " with token:", token.Value)
	if err != nil {
		log.Error.Println("Failed to get token from cookie, err:", err.Error())
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpGetCookieTokenErr, "", nil))
		return
	}

	log.Debug.Println(" -- uploadHeadurlHandler access from:", username, " with token:", token.Value)
	// step 1 : auth
	httpCode, tcpCode, msg := Auth(map[string]string{"username": username, "token": token.Value})
	if httpCode != http.StatusOK || tcpCode != 0 {
		log.Error.Println(" -- uploadHeadurlHandler Auth failed, msg:", msg)
		handleRespnse(w, httpCode, ResponseHandler(tcpCode, msg, nil))
		return
	}
	log.Debug.Println(" -- uploadHeadurlHandler Auth succ")
	// step 2 : save upload picture into file
	// save picture
	file, image, err := r.FormFile("picture")
	if err != nil {
		log.Error.Println(" -- Failed to FormFile, err:", err.Error())
		handleRespnse(w, http.StatusOK, ResponseHandler(errorcode.CodeHttpFormFileFailed, "", nil))
		return
	}
	//// check image
	if image == nil {
		log.Error.Println(" -- Failed to get image from formfile!")
		handleRespnse(w, http.StatusOK, ResponseHandler(errorcode.CodeHttpFormFileFailed, "", nil))
		return
	}

	if image.Size == 0 || int(image.Size) > config.Image.Maxsize*1024*1024 {
		log.Error.Println(" -- Filesize illegal, size:", image.Size)
		handleRespnse(w, http.StatusOK, ResponseHandler(errorcode.CodeHttpFileSizeErr, "", nil))
		return
	}
	log.Debug.Println(" -- uploadHeadurlHandler CheckImage succ")
	//// save
	imageName := generateImgName(image.Filename, username)
	fullPath := config.Image.Savepath + imageName
	saveFile, err := os.OpenFile(fullPath, os.O_WRONLY|os.O_CREATE, os.ModePerm)
	if err != nil {
		log.Error.Println(" open file err:", err)
		handleRespnse(w, http.StatusInternalServerError, ResponseHandler(errorcode.CodeHttpInternalErr, "", nil))
		return
	}
	len, err := io.Copy(saveFile, file)
	log.Debug.Println(" Save file, err:", err, len)
	if err != nil {
		log.Error.Println(" Failed to save file, err:", err)
		handleRespnse(w, http.StatusInternalServerError, ResponseHandler(errorcode.CodeHttpInternalErr, "", nil))
		return
	}
	log.Debug.Println(" Succ to save upload image, path:", fullPath)

	// step 3 : update picture info
	imageURL := config.Image.Prefixurl + "/" + fullPath
	ret, editRsp := EditUserinfo(map[string]string{"username": username, "token": token.Value, "nickname": "", "headurl": imageURL, "mode": "2"})
	log.Debug.Println(" -- editUserInfo response:", ret, editRsp)

	defer file.Close()
	defer saveFile.Close()

	handleRespnse(w, ret, editRsp)
}

// get user info
func getUserinfoHandler(w http.ResponseWriter, r *http.Request) {
	log.Debug.Printf("req = %+v", r)
	r.ParseForm()
	username := r.Form["username"][0]
	token, err := r.Cookie("token")
	if err != nil {
		log.Error.Println("Failed to get token from cookie, err:", err.Error())
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpTokenNotFound, "", nil))
		return
	}
	log.Debug.Println("access from:", username, " with token:", token.Value)
	if len(token.Value) != 32 {
		log.Error.Println("Invalid token :", token)
		handleRespnse(w, http.StatusBadRequest, ResponseHandler(errorcode.CodeHttpInvalidToken, "", nil))
		return
	}

	log.Debug.Println(" -- getUserinfoHandler access from:", username, " with token:", token.Value)
	// communicate with rcp server
	ret, rsp := GetUserinfo(map[string]string{"username": username, "token": token.Value})
	log.Debug.Println(" -- Succ to get response from backend with ", rsp)
	handleRespnse(w, ret, rsp)
}
