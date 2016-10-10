# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 14:34:06 2016
@author: Administrator
"""

import re
import os

# content should be iterable
def punc(content):
    f = []
    phraseone = re.compile('(嗯|啊|哈|哦对|噢对|唉|哎|哦|噢|诶|喂)')
    phrasetwo = re.compile('^(好的|好|对)+$')

    start = re.compile(r'^(所以|因此|然后|但是|当|那|如果|同时|与此同时|'
                       '目前来说|接下来|也就是说|其实)')
    endone = re.compile('(吗|对不对|是不是|行不行)$')
    endtwo = re.compile('^.*(怎么|什么|多少|哪|谁).*呢$')

    for sen in content:
        s = re.sub(phraseone, '', sen)
        s = re.sub(phrasetwo, '', s)
        if s:
            f.append([s, '，'])

            now_pos = len(f) - 1 if (len(f) - 1) > 0  else 0
            last_pos = now_pos - 1

            if re.search(start, s):
                if last_pos + 1:
                    if f[last_pos][1] != '？':
                        f[last_pos][1] = '。'

            if last_pos + 1 and f[last_pos][1] in '，。':
                f[last_pos][0] = f[last_pos][0].replace('呢', '')

            if re.search(endone, s) or re.search(endtwo, s):
                f[now_pos][1] = '？'

    if f[-1][1] in '，':
        f[-1][1] = '。'

    return f

# def delword(content):
# word=re.compile()
if __name__ == '__main__':
    import sys

    if sys.version > '3':
        PY3 = True
    else:
        PY3 = False

    base_dir = os.path.dirname(os.path.realpath(__file__))
    fname = r'gongzhonghao2.txt'

    raw_file = os.path.join(base_dir, fname)
    dst_file = os.path.join(base_dir, 'dst', fname)

    if not PY3:
        fr = open(raw_file, 'r')
        fw = open(dst_file, 'w+')
        text = fr.read()
        print type(text)
        content = text.split('，')

    else:
        import codecs

        fr = codecs.open(raw_file, 'r',encoding='utf-8')
        fw = codecs.open(dst_file, 'w+',encoding='utf-8')
        text=fr.read()
        content = text.split('，')

    for k, v in punc(content):
        fw.write(k + v)
        os.write(1,'%s ---->%s\n' % (k, v))

    fr.close()
    fw.close()


