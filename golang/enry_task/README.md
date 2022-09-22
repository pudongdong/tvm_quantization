# entry-task 简单用户管理系统


## 一、背景及目的


- 熟悉简单的Web API后台架构
- 熟悉使用Go实现HTTP API（JSON、文件）
- 熟悉使用Go实现基于TCP的RPC框架（设计和实现通信协议）
- 熟悉基于Auth Token的鉴权机制和流程
- 熟悉使用Go对MySQL、Redis进行基本操作
- 对任务进度和时间有所意识
- 对代码规范、测试、文档、性能调优需要有所意识


## 二、逻辑架构设计
![系统框架图](https://github.com/wxquare/enry_task/blob/master/doc/images/1.png)

### 主要模块功能:
- 用户通过浏览器向web server发送http请求，登录请求，查看用户信息、编辑用户信息
- Webserver 接收请求，解析参数，然后构造rpc请求tcpserver
- tcpserver 中系统的主要逻辑，负责查询db、cache鉴权，查询和写用户的信息
- mysql 存储用户的信息，redis 缓存用户信息以及token信息

## 三、主要接口：
- http://localhost:8080/login：登录接口
- http://localhost:8080/logout：退出登录
- http://localhost:8080/getuserinfo：获取用户信息
- http://localhost:8080/editnickname：编辑用户昵称
- http://localhost:8080/uploadpic：上传用户图像


## 四、核心逻辑详细设计

### 1、用户登录时序图
![用户登录时序图](https://github.com/wxquare/enry_task/blob/master/doc/images/2.png)

### 2、RPC 框架的设计
![rpc框架设计](https://github.com/wxquare/enry_task/blob/master/doc/images/3.png)

#### RPC 通用协议
``` 
   // RPCdata 表示rpcclient和server之间的通用协议
  type RPCdata struct {
    Name string        // 函数名称
    Args []interface{} // 请求或者返回参数
    Err  string        // 执行过程中的错误信息
  }
```
#### RPC 数据编解码

```
  func Encode(data RPCdata) ([]byte, error) {
    // serialize
    var serial bytes.Buffer
    encoder := gob.NewEncoder(&serial)
    if err := encoder.Encode(data); err != nil {
      return nil, err
    }
    // encode
    encodeData := make([]byte, 4+len(serial.Bytes()))
    binary.BigEndian.PutUint32(encodeData[:4], uint32(len(serial.Bytes())))
    copy(encodeData[4:], serial.Bytes())
    return encodeData, nil
  }
```
### 3、池化设计
   为减少资源的消耗httpserver和tcpserver之间采用连接池来实现链接的复用，提高系统的性能

```
  type GPool struct {
    factory  Factory       // factory method to create connection
    conns    chan Conn     // connections' chan
    init     uint32        // init pool size
    capacity uint32        // max pool size
    maxIdle  time.Duration // how long an idle connection remains open
    rwl      sync.RWMutex  // read-write mutex
}
```
- 系统启动时，tcpserver需要先启动，使其处于监听状态
- httpserver初始化连接池，创建与tcpserver的连接conn
- 链接conn存储在channel中
- httpserver请求tcpserver时，从连接池获取有效链接conn，通过该conn与tcpserver数据传输
- 一次请求结束后，将该conn放回连接池conns
- 为每个链接设置空闲时间maxIdle
- 限制连接池的容量capacity

## 五、存储设计

用户登录时，从缓存查询用户信息，若成功，返回用户信息；若失败，再从db中查询用户的信息，若成功，写cache，然后返回用户信息。

### mysql数据库
```
  CREATE TABLE IF NOT EXISTS userinfo_tab_0 (
    id INT(11) NOT NULL AUTO_INCREMENT COMMENT 'primary key',
    username VARCHAR(64) NOT NULL COMMENT 'unique id',
    nickname VARCHAR(128) NOT NULL DEFAULT '' COMMENT 'user nickname, can be empty',
    passwd VARCHAR(32) NOT NULL COMMENT 'md5 result of real password and key',
    skey VARCHAR(16) NOT NULL COMMENT 'secure key of each user',
    headurl VARCHAR(128) NOT NULL DEFAULT '' COMMENT 'user headurl, can be empty',
    uptime int(64) NOT NULL DEFAULT 0 COMMENT 'update time: unix timestamp',
    PRIMARY KEY (id),
    UNIQUE username_unique (username)
  ) ENGINE = InnoDB CHARSET = utf8 COMMENT 'user info table';
```
- 用户信息表结构。
- 分表设计。一共创建20张表，根据用户username来取模来决定将用户信息存储在哪张表中

### redis缓存
- redis 缓存用户的信息和token信息
- key 为username或者token
- redis 过期时间设置为2分钟

### 存储和缓存一致性
用户信息存储在redis和mysql中，用户编辑修改信息，如何保证存储和缓存的一致性

采用的方案：

- 用户编辑信息会先修改mysql表中的信息
- 然后更新redis中的缓存信息，若失败，则删除cache中原有的信息


## 六、部署方案与环境要求
- 开发机器Mac book pro-i7
- 安装mysql并启动
- 安装redis并启动
- 生成测试数据写入db
- 下载源码，编译tcpserver和rpcserver
- 先启动tcpserver，再启动rpcserver
- 浏览器访问localhost:8080 

## 七、性能测试

- https://github.com/wxquare/enry_task/blob/master/doc/performance_testing.md

参考：

- 1、 https://golang.org/doc/code
- 2、 https://golang.org/doc/tutorial/create-module
- 3、 https://golang.org/doc/articles/wiki/



