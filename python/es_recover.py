# -*- coding:utf8 -*-

from asyncio.log import logger
from elasticsearch import Elasticsearch, helpers
import json
import pdb

import os
import time
import sys

import logging

env = os.getenv('env')
cid = os.getenv('cid')

log_file_name = "{}_{}.log".format(env, cid)

print(log_file_name)

logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                    filename=log_file_name,
                    filemode='a',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )


logging.info("abc")
logging.info("bcd")


es_config = {
    "staging": {
        "host": "host1",
    },
    "test": {
        "host": "host1",
    },
    "uat": {
        "host": "host2",
    },
    "live": {
        "host":	"host2",
    }
}


es_v1 = "index_{}_{}".format(env, cid)
es_v2 = "index_v2_{}_{}".format(env, cid)

query_json = {
    "query": {
        "match_all": {}  # 获取所有数据
    }
}

if __name__ == '__main__':
    es_hosts = es_config[env]["host"]

    es_cli = Elasticsearch(
        [es_config[env]['host']]
    )

    res = es_cli.search(es_v1, doc_type="_doc",
                        body=query_json, scroll='30m', size=2000)

    total = 1
    actions = []
    hits = res.get('hits')
    if hits.get('total') > 0:
        for hit in hits.get("hits"):
            logging.info(hit.get('_id'))
            logging.info(total)
            total += 1
            action = {
                "_index": es_v2,
                "_type": "_doc",
                "_id": hit.get('_id'),
                "doc_as_upsert": True,
                "_op_type": 'update',
                "doc": {
                },
            }

            if "hotel_id" in hit.get('_source'):
                action['doc']['hotel_id'] = hit.get(
                    '_source').get('hotel_id')

                action['doc']['guest_view_score'] = hit.get(
                    '_source').get('guest_view_score')

                action['doc']['number_of_reviews'] = hit.get(
                    '_source').get('number_of_reviews')

                action['doc']['hotel_name'] = hit.get(
                    '_source').get('hotel_name')

                action['doc']['picture'] = hit.get(
                    '_source').get('picture')

                action['doc']['star_rating'] = hit.get(
                    '_source').get('star_rating')

                action['doc']['picture'] = hit.get(
                    '_source').get('picture')

                action['doc']['accommodation'] = hit.get(
                    '_source').get('accommodation')

                action['doc']['location'] = hit.get(
                    '_source').get('location')

                action['doc']['popularity_score'] = hit.get(
                    '_source').get('popularity_score')

            if "is_offline" in hit.get('_source'):
                action['doc']['is_offline'] = hit.get(
                    '_source').get('is_offline')

            if "feature" in hit.get('_source'):
                action['doc']['feature'] = hit.get(
                    '_source').get('feature')

            if hit.get('_source').get('area_name') != None:
                action['doc']['area_name'] = hit.get(
                    '_source').get('area_name')

            if hit.get('_source').get('city_name') != None:
                action['doc']['city_name'] = hit.get(
                    '_source').get('city_name')

            if hit.get('_source').get('country_name') != None:
                action['doc']['country_name'] = hit.get(
                    '_source').get('country_name')

            if hit.get('_source').get('near_by_places"') != None:
                action['doc']['near_by_places'] = hit.get(
                    '_source').get('near_by_places"')

            if hit.get('_source').get('provider_hotel_id') != None:
                action['doc']['providers'] = [{
                    "provider_hotel_id": hit.get('_source').get('provider_hotel_id'),
                    "provider_code": hit.get('_source').get('provider_code')
                }]
            actions.append(action)
        logger.info(len(actions))
        n = helpers.bulk(es_cli, actions)

    while res.get('_scroll_id') and hits.get('total') > 0:
        # 后续的每次查询都需要带上上一次查询结果中得到的scroll_id参数
        res = es_cli.scroll(scroll_id=res.get(
            '_scroll_id'), scroll='30m')
        hits = res.get('hits')
        if hits.get('total') > 0:
            for hit in hits.get("hits"):
                logging.info(hit.get('_id'))
                logging.info(total)
                total += 1
                action = {
                    "_index": es_v2,
                    "_type": "_doc",
                    "_id": hit.get('_id'),
                    "doc_as_upsert": True,
                    "_op_type": 'update',
                    "doc": {
                    },
                }
                if "hotel_id" in hit.get('_source'):
                    action['doc']['hotel_id'] = hit.get(
                        '_source').get('hotel_id')

                    action['doc']['guest_view_score'] = hit.get(
                        '_source').get('guest_view_score')

                    action['doc']['number_of_reviews'] = hit.get(
                        '_source').get('number_of_reviews')

                    action['doc']['hotel_name'] = hit.get(
                        '_source').get('hotel_name')

                    action['doc']['picture'] = hit.get(
                        '_source').get('picture')

                    action['doc']['star_rating'] = hit.get(
                        '_source').get('star_rating')

                    action['doc']['picture'] = hit.get(
                        '_source').get('picture')

                    action['doc']['accommodation'] = hit.get(
                        '_source').get('accommodation')

                    action['doc']['location'] = hit.get(
                        '_source').get('location')

                    action['doc']['popularity_score'] = hit.get(
                        '_source').get('popularity_score')

                if "is_offline" in hit.get('_source'):
                    action['doc']['is_offline'] = hit.get(
                        '_source').get('is_offline')

                if "feature" in hit.get('_source'):
                    action['doc']['feature'] = hit.get(
                        '_source').get('feature')

                if hit.get('_source').get('area_name') != None:
                    action['doc']['area_name'] = hit.get(
                        '_source').get('area_name')

                if hit.get('_source').get('city_name') != None:
                    action['doc']['city_name'] = hit.get(
                        '_source').get('city_name')

                if hit.get('_source').get('country_name') != None:
                    action['doc']['country_name'] = hit.get(
                        '_source').get('country_name')

                if hit.get('_source').get('near_by_places') != None:
                    action['doc']['near_by_places'] = hit.get(
                        '_source').get('near_by_places')

                if hit.get('_source').get('provider_hotel_id') != None:
                    action['doc']['providers'] = [{
                        "provider_hotel_id": hit.get('_source').get('provider_hotel_id'),
                        "provider_code": hit.get('_source').get('provider_code')
                    }]
                actions.append(action)
            logger.info(len(actions))
            n = helpers.bulk(es_cli, actions)
            logger.info(n)
