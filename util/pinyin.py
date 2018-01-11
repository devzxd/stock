# !/usr/bin/env python
# -*- coding:utf-8 -*-

"""
原版代码：https://github.com/cleverdeng/pinyin.py

新增功能：
    1、可以传入参数firstcode：如果为true，只取汉子的第一个拼音字母；如果为false，则会输出全部拼音；
    2、修复：如果为英文字母，则直接输出；
    3、修复：如果分隔符为空字符串，仍然能正常输出；
    4、升级：可以指定词典的文件路径
"""

__version__ = '0.9'
__all__ = ["PinYin"]

import os.path


class PinYin(object):
    def __init__(self, dict_file='word.data'):
        self.word_dict = {}
        self.dict_file = dict_file

    def load_word(self):
        if not os.path.exists(self.dict_file):
            raise IOError("NotFoundFile")

        with open(self.dict_file) as f_obj:
            for f_line in f_obj.readlines():
                try:
                    line = f_line.split('    ')
                    self.word_dict[line[0]] = line[1]
                except:
                    line = f_line.split('   ')
                    self.word_dict[line[0]] = line[1]

    def hanzi2pinyin(self, string="", firstcode=False):
        result = []
        if not isinstance(string, str):
            string = string.decode("utf-8")

        for char in string:
            key = '%X' % ord(char)
            value = self.word_dict.get(key, char)
            outpinyin = str(value).split()[0][:-1].lower()
            if not outpinyin:
                outpinyin = char
            if firstcode:
                result.append(outpinyin[0])
            else:
                result.append(outpinyin)

        return result

    def hanzi2pinyin_split(self, string="", split="", firstcode=False):
        """提取中文的拼音
        @param string:要提取的中文
        @param split:分隔符
        @param firstcode: 提取的是全拼还是首字母？如果为true表示提取首字母，默认为False提取全拼
        """
        result = self.hanzi2pinyin(string=string, firstcode=firstcode)
        return split.join(result)

#
# if __name__ == "__main__":
#     test = PinYin()
#     test.load_word()
#     string = "市盈率MRQ"
#     print("in: %s" % string)
#
#     print("out: %s" % str(test.hanzi2pinyin(string=string)))
#
#     print("out: %s" % test.hanzi2pinyin_split(string=string, split="", firstcode=True))
#
#     print("out: %s" % test.hanzi2pinyin_split(string=string, split="-", firstcode=False))