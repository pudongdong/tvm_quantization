package conf

import (
	"errors"
	"fmt"
	"io/ioutil"

	"gopkg.in/yaml.v2"
)

// TCPConf go object to tcpserver.yaml
type TCPConf struct {
	Server struct {
		Port int `yaml:"port"`
	}
	Db struct {
		Host   string `yaml:"host"`
		User   string `yaml:"user"`
		Passwd string `yaml:"passwd"`
		Db     string `yaml:"db"`
		Conn   struct {
			Maxidle int `yaml:"maxidle"`
			Maxopen int `yaml:"maxopen"`
		}
	}
	Redis struct {
		Addr     string `yaml:"addr"`
		Db       int    `yaml:"db"`
		Passwd   string `yaml:"passwd"`
		Poolsize int    `yaml:"poolsize"`
		Cache    struct {
			Tokenexpired int `yaml:"tokenexpired"`
			Userexpired  int `yaml:"userexpired"`
		}
	}
}

// HTTPConf conf object for httpserver
type HTTPConf struct {
	Server struct {
		Port int    `yaml:"port"`
		IP   string `yaml:"ip"`
	}
	Rpcserver struct {
		Addr string `yaml:"addr"`
	}
	Image struct {
		Prefixurl string `yaml:"prefixurl"`
		Savepath  string `yaml:"savepath"`
		Maxsize   int    `yaml:"maxsize"`
	}
	Logic struct {
		Tokenexpire int `yaml:"tokenexpire"`
	}

	Pool struct {
		Initsize   uint32 `yaml:"initsize"`
		Capacity   uint32 `yaml:"capacity"`
		Maxidle    uint8  `yaml:"maxidle"`
		Gettimeout uint8  `yaml:"gettimeout"`
	}
}

// ConfigParser  parser yaml config file into config struct
func ConfParser(file string, in interface{}) error {
	yamlFile, err := ioutil.ReadFile(file)
	if err != nil {
		msg := fmt.Sprintf("failed to read '%s' with err: %s", file, err.Error())
		return errors.New(msg)
	}
	err = yaml.UnmarshalStrict(yamlFile, in)
	if err != nil {
		msg := fmt.Sprintf("failed to unmarshal '%s' with err: %s", file, err.Error())
		return errors.New(msg)
	}
	return nil
}
