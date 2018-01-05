# -*- coding:utf-8 -*-

# 百度股票地址

import time

import requests
from bs4 import BeautifulSoup

from util.util import getStockCode

baseUrl = 'https://gupiao.baidu.com/stock/'

count = 0


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
    global count
    count += 1
    print("已处理%s条数据"%count)


def baiduStockInfo(lts, path):
    for l in lts:
        try:
            url = baseUrl + l
            text = _getBaiduStockHtml(url)
            if not text:
                continue
            _parserBaiduStockInfo(text, path)
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    start = time.time()
    path = 'D:/stockinfo.txt'
    baiduStockInfo(getStockCode(), path)
    end = time.time()
    print("耗时%sm,爬取%s条数据" % (end - start, count))
