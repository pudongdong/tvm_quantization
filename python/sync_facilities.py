

# 将数据导入'rkqy_wwsj'库，其中的'scs_rk_qc_all'表
##
import os
from elasticsearch import helpers
from elasticsearch import Elasticsearch
import json
from pymysql import connect
import pandas as pd
import pymysql.cursors
import logging
import traceback

# 线上环境
# pymsql：0.10.1
# elasticsearch==6.8.2
# apt-get install python3-pandas

env = os.getenv('env')
cid = os.getenv('cid')


log_file_name = "sync_facility_{}_{}.log".format(env, cid)


logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                    filename=log_file_name,
                    filemode='w',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )

db_config = {
    "staging": {
        "host": 'host',
        "port": 6606,
        "user_name": 'user_name',
        "user_password": 'user_password'
    },
    'test': {
        "host": 'host',
        "port": 6606,
        "user_name": 'user_name',
        "user_password": 'user_password'
    },
    "uat": {
        "host": 'host',
        "port": 6606,
        "user_name": 'user_name',
        "user_password": 'password'
    },
    "live": {
        "host": 'host',
        "port": 6606,
        "user_name": 'user_name',
        "user_password": 'use_password'
    }
}

es_config = {
    "staging": {
        "host": "host",
    },
    "test": {
        "host": "host",
    },
    "uat": {
        "host": "host",
    },
    "live": {
        "host":	"host",
    }
}


db_user_name = db_config[env]['user_name']
db_password = db_config[env]['user_password']
db_host = db_config[env]['host']
dp_port = db_config[env]['port']
database = 'company_dp_hotel_{}_db'.format(cid)
table_name = 'city_info_tab'


languages = {"en": 'value_in_english',
             "zh-Hans": 'value_in_chinese',
             "zh-Hant": 'value_in_tw_chinese',
             "ms-my": 'value_in_malay',
             "th": 'value_in_thai',
             "vi": 'value_in_vietnamese',
             "id": 'value_in_indonesian',
             "tl-ph": 'value_in_filipino'}


def read_facilities():
    logging.info("%s,%d", database, dp_port)
    conn = connect(host=db_host, port=dp_port,
                   user=db_user_name, passwd=db_password, db=database)
    cursor = conn.cursor()
    hotel_id_facilities = {}
    for i in range(20):
        tab = "company_hotel_multilingual_info_tab_{:08d}".format(i)
        stmt = "select hotel_id,facilities from {} where language_id = 'en'".format(
            tab)
        cursor.execute(stmt)
        while True:
            row = cursor.fetchone()
            if not row:
                break
            try:
                hotel_id = row[0]
                if len(row[1]) < 1:
                    logging.info("facility is none %s", hotel_id)
                    continue
                facilities = json.loads(row[1])
                if facilities is None:
                    logging.info("facility is none %s", hotel_id)
                    continue
                if hotel_id not in hotel_id_facilities:
                    hotel_id_facilities[hotel_id] = set()
                for f in facilities:
                    hotel_id_facilities[hotel_id].add(f['id'])
            except Exception as ex:
                s = traceback.format_exc()
                logging.info("Exception %s", s)
    for k, v in hotel_id_facilities.items():
        hotel_id_facilities[k] = list(v)
    with open("hotel_facilities_{}_{}.json".format(env, cid), "w", encoding="utf8") as f:
        f.write(json.dumps(hotel_id_facilities, indent=2, ensure_ascii=False))


def write_es():
    es_cli = Elasticsearch(
        [es_config[env]['host']]
    )

    with open("hotel_facilities_{}_{}.json".format(env, cid), "r") as f:
        hotel_facilities = json.loads(f.read())

    actions = []
    total = 0
    for hotel_id, facilities in hotel_facilities.items():
        action = {
            "_index": "company_department_hotel_basic_info_v2_{}_{}".format(env, cid),
            "_type": "_doc",
            "_id": hotel_id,
            "doc_as_upsert": True,
            "_op_type": 'update',
            "doc": {
                "hotel_id": int(hotel_id),
                "facility_codes": facilities
            },
        }
        total += 1
        actions.append(action)
        if len(actions) == 10000:
            n = helpers.bulk(es_cli, actions)
            actions = []

    if len(actions) > 0:
        n = helpers.bulk(es_cli, actions)


read_facilities()
write_es()
