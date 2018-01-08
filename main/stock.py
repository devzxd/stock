# -*- coding:utf-8 -*-


import threading
import time

import os
from datetime import datetime
from queue import Queue

import requests
from bs4 import BeautifulSoup
import logging

from util.pinyin import PinYin
from util.util import getStockCode, str2float

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# 百度股票地址
baseUrl = 'https://gupiao.baidu.com/stock/'

pinyin = PinYin(dict_file=os.path.join(os.path.abspath('../'),'util/word.data'))
pinyin.load_word()


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
    detail = div.find('a', attrs={'class': 'bets-name'})
    name = detail.text.split()[0]
    content['name'] = name
    code = detail.find('span').text
    content['code'] = code
    # 其他信息
    titleList = div.find_all('dt')
    valueList = div.find_all('dd')
    for i in range(len(titleList)):
        content[pinyin.hanzi2pinyin_split(string=titleList[i].text.split()[0], split="-", firstcode=False)] = str2float(
            valueList[i].text.split()[0])
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
    fileName = 'stock' + now.strftime("%Y-%m-%d") + '.txt'
    targetPath = os.path.join(path, fileName)
    logging.info(targetPath)
    stockList = getStockCode()
    if not stockList:
        logging.info("没有获取到股票代码列表")
    else:
        # 创建线程数量
        size = len(stockList)
        logging.info("股票代码数量：%s" % size)
        # 每个线程处理数量
        step = 100
        i = 1
        threads = Queue()
        while i <= size // step:
            l = stockList[0:step]
            stockList = stockList[len(l):size]
            t = threading.Thread(target=baiduStockInfo, name='t' + str(i), args=(l, targetPath))
            t.start()
            threads.put(t)
            i += 1
        if size % step != 0:
            t = threading.Thread(target=baiduStockInfo, name='tlast', args=(stockList, targetPath))
            t.start()
            threads.put(t)
        # for thread in threads:
        #     thread.join()
        threads.join()
        print("耗时%ss" % (time.time() - start))
