# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup


def getStockCode():
    '''
         获取股票代码
        :return: list
        '''
    # 股票列表页
    url = 'http://quote.eastmoney.com/stocklist.html'

    # 获取网页内容
    text = _getHtmlText(url)
    if not text:
        return None
    # 获取股票代码列表
    return _parseHtml(text)


def _getHtmlText(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return None


def _parseHtml(text):
    soup = BeautifulSoup(text, 'html.parser')
    a = soup.find_all('a')
    l = []
    for i in a:

        try:
            href = i.attrs['href']
            l.append(re.findall(r'[s][hz]\d{6}', href)[0])
        except:
            continue
    return l


