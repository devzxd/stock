# -*- coding:utf-8 -*-

# 百度股票地址
import threading
import time

import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import logging

from util.util import getStockCode

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

baseUrl = 'https://gupiao.baidu.com/stock/'


def _getBaiduStockHtml(url):
    r = requests.get(url)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def _parserBaiduStockInfo(text, path):
    content = {}
    soup = BeautifulSoup(text, 'html.parser')
    # 股票信息
    div = soup.find('div', attrs={'class': 'stock-bets'})
    # 股票名字
    name = div.find('a', attrs={'class': 'bets-name'}).text.split()[0]
    content['股票名称'] = name
    # 其他信息
    titleList = div.find_all('dt')
    valueList = div.find_all('dd')
    for i in range(len(titleList)):
        content[titleList[i].text.split()[0]] = valueList[i].text.split()[0]
    print(str(content) + '\n')
    with open(path, 'a', encoding='utf-8') as f:
        f.write(str(content) + '\n')


def baiduStockInfo(lts, path):
    threadName = threading.current_thread().name
    logging.info('thread %s 正在运行,股票数量为：%s' % (threadName, len(lts)))
    count = 0
    for l in lts:
        try:
            url = baseUrl + l + '.html'
            text = _getBaiduStockHtml(url)
            if not text:
                continue
            _parserBaiduStockInfo(text, path)
            count += 1
            logging.info('线程%s已处理%s条数据' % (threadName, count))
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    start = time.time()
    path = os.path.abspath('../')
    logging.info("当前目录:%s" % path)
    now = datetime.now()
    logging.info("当前日期:%s" % now.strftime("%Y-%m-%d"))
    fileName = 'stock'+now.strftime("%Y-%m-%d")+'.txt'
    targetPath = os.path.join(path, fileName)
    logging.info(targetPath)
    stockList = getStockCode()
    if not stockList:
        logging.info("没有获取到股票代码列表")
    # 创建线程数量
    size = len(stockList)
    logging.info("股票代码数量：%s" % size)
    # 每个线程处理数量
    step = 100
    i = 1
    while i <= size // step:
        l = stockList[0:step]
        stockList = stockList[len(l):size]
        t = threading.Thread(target=baiduStockInfo, name='t' + str(i), args=(l, targetPath))
        t.start()
        i += 1
    if size % step != 0:
        t = threading.Thread(target=baiduStockInfo, name='tlast', args=(stockList, targetPath))
        t.start()
    end = time.time()
    print("耗时%ss" % (end - start))
