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
            # 只获取股票代码
            l.append(re.findall(r'[s][hz][603]\d{5}', href)[0])
        except:
            continue
    return l

# 将带单位的数字转为正常数字
def str2float(str):
    if not str or str =='--':
        return 0.0
    str = str.replace(' ', '').replace(',','')
    pattern = r'[\u4E00-\u9FA5]'
    r = re.findall(pattern, str)
    f = re.findall(r'%', str)
    # 不包含汉字，不包含%，直接返回
    if not r and not f:
        return float(str)
    # 包含%直接替换，返回
    if f:
        return float(_replaceStr(f, str))
    # 包含汉字，先将汉字替换为''，然后进行单位换算
    if '万' in r and '亿' in r:
        str = _replaceStr(r, str)
        str = float(str) * 10000 * 100000000
        return str
    if '万' in r:
        str = _replaceStr(r, str)
        str = float(str) * 10000
        return str
    if '亿' in r:
        str = _replaceStr(r, str)
        str = float(str) * 100000000
        return str
    # 其他汉字直接返回
    str = _replaceStr(r, str)
    return float(str)


def _replaceStr(r, str):
    for i in r:
        str = str.replace(i, '')
    return str