# -*- coding:utf-8 -*-
import json
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

pinyin = PinYin(dict_file=os.path.join(os.path.abspath('../'), 'util/word.data'))
pinyin.load_word()

now = datetime.now()
today = now.strftime("%Y-%m-%d")
# 数据存储地址
post_url = "http://10.156.26.17:8080/combinedInsert"


def _getBaiduStockHtml(url):
    r = requests.get(url)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def _parserBaiduStockInfo(text, content):
    baseInfo = {}
    content['gpMain'] = baseInfo
    soup = BeautifulSoup(text, 'html.parser')
    baseInfo['execute_date'] = today
    # 股票信息
    div = soup.find('div', attrs={'class': 'stock-bets'})
    # 股票名字
    detail = div.find('a', attrs={'class': 'bets-name'})
    name = detail.text.split()[0]
    baseInfo['name'] = name
    content['name'] = name
    code = detail.find('span').text
    baseInfo['code'] = code
    content['code'] = code
    # 涨跌、涨幅、今收
    priceSpan = div.find('div', attrs={'class': 'price'}).findAll('span')
    zhang_die = priceSpan[0].text
    zhang_fu = priceSpan[1].text
    jin_shou = div.find('div', attrs={'class': 'price'}).find('strong').text
    baseInfo['zhang_die'] = str2float(zhang_die)
    baseInfo['zhang_fu'] = str2float(zhang_fu)
    baseInfo['jin_shou'] = str2float(jin_shou)
    # 其他信息
    titleList = div.find_all('dt')
    valueList = div.find_all('dd')
    for i in range(len(titleList)):
        baseInfo[
            pinyin.hanzi2pinyin_split(string=titleList[i].text.split()[0], split="_", firstcode=False)] = str2float(
            valueList[i].text.split()[0])


# 解析资金流向
def _parserBaiduStockJzlx(text, gpMain):
    soup = BeautifulSoup(text, 'html.parser')
    table = soup.find('table', attrs={'class': '_dailyFunds'})
    if not table:
        pass
    else:
        td = table.findAll('td', attrs={'class': 'ta-right'})
        if not td:
            pass
        else:
            # 资金流入
            gpMain['zjlr'] = str2float(td[1].text)
            # 主力资金流入
            gpMain['zl_zjlr'] = str2float(td[3].text)
            # 散户资金流入
            gpMain['sh_zjlr'] = str2float(td[4].text)
            # 主力参与度
            gpMain['zl_cyd'] = str2float(td[5].text.split()[0])


# 解析龙虎榜
def _parserBaiduStockLhb(text, content):
    lhb = {}
    content['longHuBang'] = lhb
    soup = BeautifulSoup(text, 'html.parser')
    # 获取所有table
    table = soup.findAll('table')
    if not table:
        return

    # 获取最近上榜信息table
    baseTable = table[0]
    lhbBase = {}
    lhbBase['name'] = content['name']
    lhbBase['code'] = content['code']
    baseTd = baseTable.find('tbody').findAll('td')
    _buildLhbBase(baseTd, lhbBase)
    lhb['lhbBase'] = lhbBase
    inTopTable = table[1].find('tbody')
    inTop = []
    _buildLhbTop(inTop, inTopTable, lhbBase['sb_date'], content['name'], content['code'], 'in')
    lhb['lhbInTops'] = inTop
    outTopTable = table[2].find('tbody')
    outTop = []
    _buildLhbTop(outTop, outTopTable, lhbBase['sb_date'], content['name'], content['code'], 'out')
    lhb['lhbOutTops'] = outTop


def _buildLhbTop(inTop, inTopTable, sb_date, name, code, type):
    trs = inTopTable.findAll('tr')
    trs = trs[1:len(trs)-1]
    for tr in trs:
        temp = {}
        tds = tr.findAll('td')
        temp['name'] = name
        temp['code'] = code
        temp['yyb_name'] = tds[0].text
        temp['in_amount'] = str2float(tds[1].text)
        temp['out_amount'] = str2float(tds[2].text)
        temp['sb_date'] = sb_date
        temp['inOrOut'] = type
        inTop.append(temp)


def _buildLhbBase(baseTd, lhbBase):
    # 上榜日期
    lhbBase['sb_date'] = baseTd[0].text
    # 上榜原因
    lhbBase['sb_reason'] = baseTd[1].text
    # 净买入额
    lhbBase['jmre'] = str2float(baseTd[2].text)
    # 总成交额
    lhbBase['zcje'] = str2float(baseTd[3].text)
    # 总成交量
    lhbBase['zcjl'] = str2float(baseTd[4].text)


def baiduStockInfo(lts, path):
    threadName = threading.current_thread().name
    logging.info('thread %s 正在运行,股票数量为：%s' % (threadName, len(lts)))
    data = []
    count = 0
    for l in lts:
        try:
            content = {}
            # 股票基本信息
            base_info_url = baseUrl + l
            text = _getBaiduStockHtml(base_info_url)
            if not text:
                continue
            _parserBaiduStockInfo(text, content)
            try:
                # 股票资金流向
                jzlx_url = baseUrl + 'zjlx/' + l
                jzlx_text = _getBaiduStockHtml(jzlx_url)
                # 如果资金流向为空，直接组装数据返回
                if not jzlx_text:
                    pass
                else:
                    _parserBaiduStockJzlx(jzlx_text, content['gpMain'])
                # 龙虎榜
                lhb_url = baseUrl + 'lhb/' + l
                lhb_text = _getBaiduStockHtml(lhb_url)
                if not lhb_text:
                    pass
                else:
                    _parserBaiduStockLhb(lhb_text, content)
            except Exception as e:
                logging.exception(e)
            count = _buildData(content, count, data, threadName, path)
        except Exception as e:
            logging.exception(e)

            continue
    # 数据不为空，就发送http请求
    if data:
        try:
            requests.post(post_url, data=str(data).encode())
        except Exception as e:
            logging.error("%s执行数据存储错误" % threadName, e)


def _buildData(content, count, data, threadName, path):
    data.append(content)
    print(json.dumps(content, ensure_ascii=False) + '\n')
    count += 1
    logging.info('线程%s已处理%s条数据' % (threadName, count))
    # if count == 2:
    #     if data:
    #         try:
    #             requests.post(post_url, data=str(data).encode())
    #         except Exception as e:
    #             logging.error("%s执行数据存储错误" % threadName, e)

    # with open(path, 'a', encoding='utf-8') as f:
    #     f.write(json.dumps(content, ensure_ascii=False) + '\n')
    return count


if __name__ == '__main__':
    start = time.time()
    path = os.path.abspath('../')
    logging.info("当前目录:%s" % path)
    now = datetime.now()
    logging.info("当前日期:%s" % today)
    fileName = 'stock' + today + '.txt'
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
