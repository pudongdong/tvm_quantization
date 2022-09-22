package errorcode

const (
	// CodeSucc          succ code
	CodeSucc = 0

	// HTTP 2000 ~ 3000
	// CodeInternalErr   internel err
	CodeHttpInternalErr = 2101
	// CodeTokenNotFound missing token
	CodeHttpTokenNotFound = 2102
	// CodeInvalidToken  token format is invalid
	CodeHttpInvalidToken = 2103
	// CodeErrBackend    failed to comm with backend server
	CodeHttpErrBackend = 2201
	// CodeInvalidPasswd passwd format isn't right
	CodeHttpInvalidPasswd = 2301
	// CodeFormFileFailed formFile get error
	CodeHttpFormFileFailed = 2401
	// CodeFileSizeErr file size not match (too small or too large)
	CodeHttpFileSizeErr = 2402
	// CodeGetRPCClientErr get rpc client error.
	CodeHttpGetRPCClientErr = 2501
	// CodeHttpGetCookieTokenErr get token from cookie error.
	CodeHttpGetCookieTokenErr = 2601

	// tcp 1000 ~ 2000
	// CodeTCPFailedGetUserInfo code succ
	CodeTCPFailedGetUserInfo = 1101
	// CodeTCPPasswdErr password error
	CodeTCPPasswdErr = 1102
	// CodeTCPInvalidToken invalid token
	CodeTCPInvalidToken = 1200
	// CodeTCPTokenExpired token expired
	CodeTCPTokenExpired = 1201
	// CodeTCPUserInfoNotMatch token info not match userinfo
	CodeTCPUserInfoNotMatch = 1202
	// CodeTCPFailedUpdateUserInfo update userinfo failed
	CodeTCPFailedUpdateUserInfo = 1301
	// CodeTCPInternelErr internel error
	CodeTCPInternelErr = 1401
)

// CodeMsg code to msg description
var CodeMsg = map[int]string{
	// http
	CodeSucc:                  "succ",
	CodeHttpInternalErr:       "please try again!",
	CodeHttpTokenNotFound:     "param error: token not found",
	CodeHttpInvalidToken:      "invalid token",
	CodeHttpErrBackend:        "Error found!please try again!",
	CodeHttpInvalidPasswd:     "username/passwd error!",
	CodeHttpFormFileFailed:    "fetch file failed!",
	CodeHttpFileSizeErr:       "File size err (should less than 5MB)!",
	CodeHttpGetRPCClientErr:   "get rpc client faliled!",
	CodeHttpGetCookieTokenErr: "get token from cookie error!",

	// tcp
	CodeTCPFailedGetUserInfo:    "tcp server: failed to get userinfo",
	CodeTCPPasswdErr:            "tcp server: wrong passwd",
	CodeTCPInvalidToken:         "tcp server: invalid token format",
	CodeTCPTokenExpired:         "tcp server: token expired",
	CodeTCPUserInfoNotMatch:     "tcp server: token cache info not match",
	CodeTCPFailedUpdateUserInfo: "tcp server: failed to update userinfo",
	CodeTCPInternelErr:          "tcp server: internel error",
}
