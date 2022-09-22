# -*- coding: utf-8

# 获取输入参数的值


import sys
import time
import os
import json
import threading
import re
import time
import requests
import socket
from string import Template

SRC_ADDR = job_get_param("src_addr")
DEST_ADDR = job_get_param("dest_addr")

INDEX_PATTERN = job_get_param("index_pattern")


# logstash .conf template
conf_template_str = 'input {\
  elasticsearch {\
      hosts => $src_cluster\
      index => "$index_name"\
      size => 500\
      scroll => "5m"\
      codec => "json"\
      docinfo => true\
      docinfo_fields => ["_index", "_type", "_id", "_routing"]\
  }\
}\
filter {\
  mutate {\
    remove_field => [ "@version" ]\
    remove_field => ["@timestamp"]\
    }\
}\
output {\
  if [@metadata][_routing] {\
    elasticsearch {\
      hosts => $dest_cluster\
      index => "$index_name"\
      pipeline=> "_none"\
      document_type => "%{[@metadata][_type]}"\
      document_id => "%{[@metadata][_id]}"\
      routing => "%{[@metadata][_routing]}"\
    }\
  } else {\
    elasticsearch {\
      hosts => $dest_cluster\
      index => "$index_name"\
      pipeline=> "_none"\
      document_type => "%{[@metadata][_type]}"\
      document_id => "%{[@metadata][_id]}"\
    }\
  }\
}'


# used for move data

def copy_pipeline_metadata(src_addr, dest_addr):
    os.system("rm pipeline.json")
    pipeline_file = "pipeline.json"
    os.system("curl '"+src_addr+"/_ingest/pipeline?pretty' > "+pipeline_file)
    tmp_file_info = open(pipeline_file, "r")
    tmp_file_dict = json.load(tmp_file_info)
    real_dict = {}
    tmp_file_info.close()
    for key, value in tmp_file_dict.iteritems():
        if not key.startswith("xpack"):
            real_dict[key] = value

    for key, value in real_dict.iteritems():
        print '''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' '''+json.dumps(real_dict[key])+"'   "+dest_addr+'''/_ingest/pipeline/'''+key
        os.system('''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' ''' +
                  json.dumps(real_dict[key])+"'   "+dest_addr+'''/_ingest/pipeline/'''+key)
        print key+" finish"
    print "all pipeline finish"
    os.system("rm pipeline.json")


def copy_template(src_addr, dest_addr):
    template_file = "template.json"
    os.system("rm "+template_file)
    os.system("curl "+src_addr+"/_template?pretty > "+template_file)
    tmp_file_info = open(template_file, "r")
    tmp_file_dict = json.load(tmp_file_info)
    real_dict = {}
    tmp_file_info.close()
    for key, value in tmp_file_dict.iteritems():
        if not key.startswith(".") and key not in filter_template:
            real_dict[key] = value
    for key, value in real_dict.iteritems():
        print '''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' '''+json.dumps(real_dict[key])+"'   "+dest_addr+'''/_ingest/pipeline/'''+key
        os.system('''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' ''' +
                  json.dumps(real_dict[key])+"'   "+dest_addr+'''/_template/'''+key)
        print key+" finish"
    print "all template finish"
    os.system("rm "+template_file)


def copy_ilm(src_addr, dest_addr, ilm_list):
    ilm_file = "ilm_policy.json"
    os.system("rm "+ilm_file)
    os.system("curl "+src_addr+"/_ilm/policy?pretty > "+ilm_file)
    tmp_file_info = open(ilm_file, "r")
    tmp_file_dict = json.load(tmp_file_info)
    real_dict = {}
    tmp_file_info.close()
    for key, value in tmp_file_dict.iteritems():
        if key in ilm_list:
            real_dict[key] = value
    for key, value in real_dict.iteritems():
        print '''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' '''+json.dumps(real_dict[key])+"'   "+dest_addr+'''/_ingest/pipeline/'''+key
        os.system('''curl -H "Content-Type: application/json" -v -XPUT --data-raw ' ''' +
                  json.dumps(real_dict[key])+"'   "+dest_addr+'''/_ilm/policy/'''+key)
        print key+" finish"
    print "all ilm finish"
    os.system("rm "+ilm_file)


def download_index_settings_and_mappings(src_addr):
    index_set_file = "index_set.json"
    #os.system("curl "+ '"' + src_addr+'/_cat/indices?s=pri.store.size:desc&bytes=gb&h=index,pri.store.size,status" > '+index_set_file)
    os.system("curl " + '"' + src_addr +
              '/_cat/indices?s=index:desc&bytes=gb&h=index,pri.store.size,status" > '+index_set_file)
    print "download index info finish"


def index_regex(index, *patterns):
    if patterns:
        for pattern in patterns:
            if re.match(pattern, index):
                return True
    return False


def copy_index_settings_and_mappings(src_addr, dest_addr, *patterns):
    os.system("index_set.json")
    index_set_file = "index_set.json"
    index_list = open(index_set_file, "r").readlines()
    for one_line in index_list:
        one_index_info = one_line.split()
        one_index = one_index_info[0]
        # if not settings_mappings_copy_list and not patterns,copy all except start with "."
        if settings_mappings_copy_list or patterns:
            # if want to copy index should in list or match patterns
            if (one_index not in settings_mappings_copy_list and not index_regex(one_index, *patterns)):
                print "settings mappings not copy: " + one_index
                continue
        if one_index and not one_index.startswith("."):
            print "copy index settings mappings: " + one_index
            os.system("curl "+src_addr+"/"+one_index +
                      "?pretty > "+one_index+".json")
            tmp_file_info = open(one_index+".json", "r")
            tmp_file_dict = json.load(tmp_file_info)
            tmp_file_dict = tmp_file_dict[one_index]
            del tmp_file_dict["settings"]["index"]["creation_date"]
            del tmp_file_dict["settings"]["index"]["uuid"]
            del tmp_file_dict["settings"]["index"]["version"]
            del tmp_file_dict["settings"]["index"]["provided_name"]
            if tmp_file_dict["settings"]["index"].has_key("resize"):
                del tmp_file_dict["settings"]["index"]["resize"]
            if tmp_file_dict["settings"]["index"].has_key("blocks"):
                del tmp_file_dict["settings"]["index"]["blocks"]
            if tmp_file_dict["settings"]["index"].has_key("routing") and tmp_file_dict["settings"]["index"]["routing"].has_key("allocation") and tmp_file_dict["settings"]["index"]["routing"]["allocation"].has_key("initial_recovery"):
                del tmp_file_dict["settings"]["index"]["routing"]["allocation"]["initial_recovery"]
            tmp_file_info.close()
            tmp_file_info = open(one_index+".json", "w")
            tmp_file_info.write(json.dumps(tmp_file_dict))
            tmp_file_info.close()
            os.system("curl  -H 'Content-Type: application/json' -v -XPUT -d @" +
                      one_index+".json "+dest_addr+"/"+one_index+" > "+one_index+"_finish.json")
            os.system("rm "+one_index+".json")
    print "copy index info finish"


def generatePipelineFile(data_size_in_pipeline, src_addr, dest_addr, *patterns):
    os.system("rm pipelines-*")
    os.system("rm total_files")
    conf_template = Template(conf_template_str)
    index_set_file = "index_set.json"
    index_list = open(index_set_file, "r").readlines()
    data_size = 0
    file_num = 0
    file_now = open("pipelines" + "-" + str(file_num)+".yml", 'a')
    worker_sum = 0
    for one_index_info in index_list:
        one_index_info = one_index_info.split()
        # if not data_copy_list and not patterns,copy all except start with "."
        if data_copy_list or patterns:
            # if want to copy index should in list or match patterns
            if (one_index_info[0] not in data_copy_list) and not index_regex(one_index_info[0], *patterns):
                # print "data not copy " + one_index_info[0]
                continue
        if one_index_info[0] and not one_index_info[0].startswith(".") and len(one_index_info) > 2:
            dict = {
                'index_name': one_index_info[0], 'src_cluster': src_addr, 'dest_cluster': dest_addr}
            if data_size < data_size_in_pipeline and worker_sum < 32:
                round_num = int(
                    round((float(one_index_info[1])/data_size_in_pipeline)*32))
                worker_num = round_num if round_num > 4 else 4
                worker_num = 32 if worker_num > 32 else worker_num
                worker_sum = worker_sum + worker_num

                if worker_sum > 32:
                    file_now.flush()
                    file_now.close()
                    worker_sum = worker_num
                    data_size = 0
                    file_num = file_num + 1

                    print one_index_info[0] + " pipelines" + "-" + str(file_num)+".yml"

                    file_now = open("pipelines" + "-" +
                                    str(file_num)+".yml", 'a')
                    file_now.write("- pipeline.id: " + one_index_info[0])
                    file_now.write("\n")
                    file_now.write("  pipeline.workers: " +
                                   str(int(worker_num*1.5)))
                    file_now.write("\n")
                    # file_now.write("  path.config: " + path + "/" + one_index_info[0] + ".conf")
                    # file_now.write("\n")
                    file_now.write("  config.string: " +
                                   conf_template.substitute(dict))
                    file_now.write("\n")

                    # file_index = open(one_index_info[0]+".conf",'w')
                    # file_index.write(conf_template.substitute(dict))
                    # file_index.flush()
                    # file_index.close()

                    data_size = data_size + int(one_index_info[1])
                else:
                    file_now.write("- pipeline.id: " + one_index_info[0])
                    file_now.write("\n")
                    file_now.write("  pipeline.workers: " +
                                   str(int(worker_num*1.5)))
                    file_now.write("\n")
                    # file_now.write("  path.config: " + path + "/" + one_index_info[0] + ".conf")
                    # file_now.write("\n")
                    file_now.write("  config.string: " +
                                   conf_template.substitute(dict))
                    file_now.write("\n")

                    # file_index = open(one_index_info[0]+".conf",'w')
                    # file_index.write(conf_template.substitute(dict))
                    # file_index.flush()
                    # file_index.close()

                    data_size = data_size + int(one_index_info[1])
            else:
                file_now.flush()
                file_now.close()

                worker_sum = 0
                data_size = 0
                file_num = file_num + 1

                print one_index_info[0] + " pipelines" + "-" + str(file_num)+".yml"

                file_now = open("pipelines" + "-" + str(file_num)+".yml", 'a')
                file_now.write("- pipeline.id: " + one_index_info[0])
                file_now.write("\n")
                round_num = int(
                    round((float(one_index_info[1])/data_size_in_pipeline)*32))
                worker_num = round_num if round_num > 4 else 4
                worker_num = 32 if worker_num > 32 else worker_num
                file_now.write("  pipeline.workers: " + str(worker_num))
                file_now.write("\n")
                # file_now.write("  path.config: " + path + "/" + one_index_info[0] + ".conf")
                # file_now.write("\n")
                file_now.write("  config.string: " +
                               conf_template.substitute(dict))
                file_now.write("\n")

                # file_index = open(one_index_info[0]+".conf",'w')
                # file_index.write(conf_template.substitute(dict))
                # file_index.flush()
                # file_index.close()

                worker_sum = worker_sum + worker_num
                data_size = data_size + int(one_index_info[1])
    os.system("echo " + str(file_num+1) + " > total_files")
    file_now.flush()
    file_now.close()

    print "Generate pipelines.yml finish! Total " + str(file_num+1) + " files."

# TODO http proxy should be add


def logstashExistsOrWget(path="/etc/logstash", version="7.14.0"):
    if os.path.exists(path+"/logstash-"+version) != True:
        os.system("wget https://artifacts.elastic.co/downloads/logstash/logstash-" +
                  version+"-linux-x86_64.tar.gz")
        os.system("mkdir /etc/logstash")
        os.system("tar zxf logstash-"+version +
                  "-linux-x86_64.tar.gz -C /etc/logstash/")
        f = open(path+"/logstash-"+version+"/"
                 + "vendor/bundle/jruby/2.5.0/gems/logstash-input-elasticsearch-4.9.1/lib/logstash/inputs/elasticsearch.rb", "r")
        lines = f.readlines()

        i = lines.index("      scroll_id = r['_scroll_id']\n")
        lines.insert(
            i+1, "      if r['hits']['total'].instance_of?(Integer)\n")
        lines.insert(
            i+2, "        logger.info('Scroll has hits', index: @index, scroll_value: r['hits']['total'])\n")
        lines.insert(i+3, "      else\n")
        lines.insert(
            i+4, "        logger.info('Scroll has hits', index: @index, scroll_value: r['hits']['total']['value'])\n")
        lines.insert(i+5, "      end\n")

        f.close()
        f = open(path+"/logstash-"+version+"/"
                 + "vendor/bundle/jruby/2.5.0/gems/logstash-input-elasticsearch-4.9.1/lib/logstash/inputs/elasticsearch.rb", "w")
        f.writelines(lines)
        f.close()

        f = open(path+"/logstash-"+version+"/"+"config/jvm.options", "r")
        lines = f.readlines()
        i = lines.index("-Xms1g\n")
        lines[i] = "-Xms8g\n"
        lines[i+1] = "-Xmx8g\n"
        f.close()
        f = open(path+"/logstash-"+version+"/"+"config/jvm.options", "w")
        f.writelines(lines)
        f.close()


def detectLogstash():
    try:
        response = requests.get("http://127.0.0.1:9600")
        if response.status_code == 200:
            return True
        else:
            return False
    except:
        return False


def logstahForCopyData(path="/etc/logstash", version="7.14.0"):
    total_files = "total_files"
    total_num = int(open(total_files, "r").read().strip())
    if total_num:
        for num in range(0, total_num):
            os.system("rm "+path+"/logstash-"+version+"/config/pipelines.yml")
            os.system("cp " + "pipelines" + "-" + str(num)+".yml " +
                      path+"/logstash-"+version+"/config/pipelines.yml")
            if not detectLogstash():
                os.system("echo " + time.ctime()+" " + str(time.time()) +
                          " started " + "pipelines" + "-" + str(num)+".yml " + " >> copy_time")
                os.system("nohup "+path+"/logstash-"+version +
                          "/bin/logstash >/dev/null 2>&1 &")
                time.sleep(60)
                print "sleep 60s"
                while(detectLogstash()):
                    time.sleep(1)
                    # print "sleep 1s"

            os.system("echo " + time.ctime() + " " + str(time.time()) +
                      " finished " + "pipelines" + "-" + str(num)+".yml " + " >> copy_time")


def verifyData(src_addr, dest_addr, *patterns):
    index_set_file = "index_set.json"
    index_list = open(index_set_file, "r").readlines()
    for one_index_info in index_list:
        one_index_info = one_index_info.split()
        # if not data_copy_list and not patterns,copy all except start with "."
        if data_copy_list or patterns:
            # if want to copy index should in list or match patterns
            if (one_index_info[0] not in data_copy_list) and not index_regex(one_index_info[0], *patterns):
                continue
        if one_index_info[0] and not one_index_info[0].startswith("."):
            try:
                response_src = requests.get(
                    "http://" + src_addr + "/" + one_index_info[0] + "/_count?pretty").json()

                response_dest = requests.get(
                    "http://" + dest_addr + "/" + one_index_info[0] + "/_count?pretty").json()

                if response_src.has_key('count') and response_dest.has_key('count'):
                    if response_src["count"] == response_dest["count"]:

                        print one_index_info[0] + " equal"
                        job_stdout(one_index_info[0], " equal")
                    else:
                        print one_index_info[0] + " not equal"
                        job_stdout(one_index_info[0], " not equal")
                else:
                    print one_index_info[0] + " not equal"
                    job_stdout(one_index_info[0], " not equal")
            except Exception as e:
                job_stdout(one_index_info[0], " not equal")
                print e


def getIpList(domain):
    ip_list = []
    try:
        addrs = socket.getaddrinfo(domain, None)
        for item in addrs:
            if item[4][0] not in ip_list:
                ip_list.append(item[4][0])
                # print item[4][0]
    except Exception as e:
        print(str(e))
        pass
    return ip_list


def getIpPort(url, port="9201"):
    noHttp = re.sub(r'http[s]?://', "", url)
    if noHttp.find(":") != -1:
        res = noHttp.split(":", 1)
        domain = res[0]
        port = res[1]
        ipList = getIpList(domain)
        # print ipList
        for i in range(len(ipList)):
            ipList[i] = ipList[i] + ":" + port
        return ipList
    else:
        ipList = getIpList(noHttp)
        # print ipList
        for i in range(len(ipList)):
            ipList[i] = ipList[i] + ":" + port
        return ipList


if __name__ == "__main__":
    #     src_addr = "10.60.144.*:9204" or "http://es.sg2.i.toc-feed.test.sz.shopee.io:9206"
    #     dest_addr = "10.60.17.*:9204" or "http://es.sg2.i.toc-feed-dr.test.sz.shopee.io:9206"
    src_addr = re.sub(r'http[s]?://', "", SRC_ADDR)
    dest_addr = re.sub(r'http[s]?://', "", DEST_ADDR)
    src_addr_array = getIpPort(src_addr)
    dest_addr_array = getIpPort(dest_addr)
    # index setting and mapping want to copy.
    settings_mappings_copy_list = []
    # index want to copy
    data_copy_list = []
    # template which not to copy
    filter_template = ["logstash-index-template", "kibana_index_template:.kibana",
                       "security-index-template", "security_audit_log"]
    # ilm which want to copy
    ilm_list = []
    # advised order to move data
    # copy_pipeline_metadata(src_addr,dest_addr)
    # copy_ilm(src_addr,dest_addr,ilm_list)
    download_index_settings_and_mappings(src_addr)
    # patterns is regex pattern,can be nil
    copy_index_settings_and_mappings(src_addr, dest_addr, INDEX_PATTERN)
    logstashExistsOrWget()
    generatePipelineFile(100, src_addr_array, dest_addr_array, INDEX_PATTERN)
    logstahForCopyData()
    verifyData(src_addr, dest_addr, INDEX_PATTERN)
    copy_template(src_addr, dest_addr)
    job_success()
