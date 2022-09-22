request = function()
    uid = math.random(1, 10000000)
    body = "passwd=e10adc3949ba59abbe56e057f20f883e&username=username" .. uid
    wrk.headers["Content-Type"] = "application/x-www-form-urlencoded"
    return wrk.format("POST", nil,headers,body)
 end