# Performance testing
========================

## 工具、关键参数设置
- 测试机器：Macbook Pro-i7
- 测试工具[wrk](https://github.com/wg/wrk)
- sudo sysctl -w kern.ipc.somaxconn=2048
- sudo sysctl -w kern.maxfiles=12288
- ulimit -n 10000
- httpserver pool size 1024
- redis pool size 256
- mysql maxopen 256


## 测试 200并发，固定用户登录
    wrk -t8 -c200 -d30s --latency -s  ./scripts/fixed_user.lua http://localhost:8080/login
    
output:

    Running 30s test @ http://localhost:8080/login
    8 threads and 200 connections
    Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    35.72ms   12.81ms 113.53ms   69.18%
        Req/Sec   703.61     92.30     1.00k    69.38%
    Latency Distribution
        50%   35.60ms
        75%   44.00ms
        90%   51.64ms
        99%   67.67ms
    168223 requests in 30.03s, 60.80MB read
    Requests/sec:   5601.15
Transfer/sec:      2.02MB

## 测试 2000并发，固定用户登录
    wrk -t8 -c2000 -d30s --latency -s  ./scripts/fixed_user.lua http://localhost:8080/login

output:

    Running 30s test @ http://localhost:8080/login
    8 threads and 2000 connections
    Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency   348.44ms  121.90ms   1.03s    71.24%
        Req/Sec   726.35    134.36     1.37k    73.58%
    Latency Distribution
        50%  362.41ms
        75%  428.20ms
        90%  482.74ms
        99%  619.54ms
    171280 requests in 30.06s, 61.91MB read
    Requests/sec:   5698.29
    Transfer/sec:      2.06MB

## 测试 200并发，随机用户登录
    wrk -t8 -c200 -d30s --latency -s  ./scripts/random_user.lua http://localhost:8080/login

output:

    Running 30s test @ http://localhost:8080/login
    8 threads and 200 connections
    Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    40.17ms   14.07ms 145.39ms   73.39%
        Req/Sec   626.51    131.35     0.92k    66.79%
    Latency Distribution
        50%   38.97ms
        75%   47.43ms
        90%   57.15ms
        99%   82.33ms
    149842 requests in 30.05s, 44.55MB read
    Requests/sec:   4986.88
    Transfer/sec:      1.48MB


## 2000 并发，使用随机用户登录
    wrk -t8 -c2000 -d30s --latency -s  ./scripts/random_user.lua http://localhost:8080/login
output:

    wrk -t8 -c2000 -d30s --latency -s  ./scripts/random_user.lua http://localhost:8080/login
    Running 30s test @ http://localhost:8080/login
    8 threads and 2000 connections
    Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency   403.93ms  153.79ms 900.10ms   70.09%
        Req/Sec   623.06    178.60     1.08k    67.17%
    Latency Distribution
        50%  410.75ms
        75%  492.96ms
        90%  591.88ms
        99%  773.69ms
    147578 requests in 30.08s, 43.87MB read
    Requests/sec:   4906.07
    Transfer/sec:      1.46MB
