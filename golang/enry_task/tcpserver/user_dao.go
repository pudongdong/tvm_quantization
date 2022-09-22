package main

import (
	"github.com/wxquare/entry_task/log"
)

const (
	editUsername = 1
	editHeadurl  = 2
)

func getUserInfo(username string) (User, error) {
	log.Debug.Printf("username=%s\n", username)
	// try cache
	user, err := getUserCacheInfo(username)
	if err == nil && user.Username == username {
		return user, err
	}

	// get from db
	user, err = getDbUserInfo(username)
	if err != nil {
		return user, err
	}

	// update cache
	serr := setUserCacheInfo(user)
	if serr != nil {
		log.Error.Println("cache userinfo failed for user:", user.Username, " with err:", serr.Error())
	}

	return user, err
}

// edit userinfo
func editUserInfo(username, nickname, headurl, token string, mode uint32) int64 {
	// update db info
	var affectedRows int64
	switch mode {
	case editUsername:
		affectedRows = updateDbNickname(username, nickname)
	case editHeadurl:
		affectedRows = updateDbHeadurl(username, headurl)
	default:
		// do nothing
		break
	}

	if affectedRows == 1 {
		user, err := getDbUserInfo(username)
		if err == nil {
			updateCachedUserinfo(user)
			if token != "" {
				err = setTokenInfo(user, token)
				if err != nil {
					log.Error.Println("update token failed:", err.Error())
					delTokenInfo(token)
				}
			}
		} else {
			log.Error.Println("Failed to get dbUserInfo for cache, username:", username, " with err:", err.Error())
		}
	}
	return affectedRows
}
