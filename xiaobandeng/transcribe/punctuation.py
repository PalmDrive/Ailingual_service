# -*- coding: utf-8 -*-
import re
import os

# content should be iterable
def punc(content):
    f = []
    phraseone = re.compile(u'(嗯|啊|哈|哦对|噢对|唉|哎|哦|噢|诶|喂)')
    phrasetwo = re.compile(u'^(好的|好|对)+$')

    start = re.compile(ur'^(所以|因此|然后|但是|当|那|如果|同时|与此同时|'
                       ur'目前来说|接下来|也就是说|其实)')
    endone = re.compile(u'(吗|对不对|是不是|行不行)$')
    endtwo = re.compile(u'^.*(怎么|什么|多少|哪|谁).*呢$')

    for index, sen in enumerate(content):

        s = re.sub(phraseone, u'', sen)
        s = re.sub(phrasetwo, u'', s)
        f.append([s, u'，'])

        if s:
            cur_index = len(f) - 1 if (len(f) - 1) > 0  else 0
            prev_index = cur_index - 1

            if re.search(start, s):
                if prev_index + 1:
                    if f[prev_index][1] != u'？':
                        f[prev_index][1] = u'。'

            if f[cur_index][1] in u'，。':
                f[cur_index][0] = f[cur_index][0].replace(u'呢', '')

            # if cur_index and f[prev_index][1] in '，。':
            # f[prev_index][0] = f[prev_index][0].replace('呢', '')

            if re.search(endone, s) or re.search(endtwo, s):
                f[cur_index][1] = u'？'

    if f[index][1] in u'，':
        f[index][1] = u'。'

    return f


def punc_task_group(task_group):
    punctuations = u',，?？.。'
    content_list = [task.result[0].strip(punctuations) for task in task_group.tasks]
    punc_dict = punc(content_list)
    for index, result in enumerate(punc_dict):
        task_group.tasks[index].result = [u''.join(result)]


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

        fr = codecs.open(raw_file, 'r', encoding='utf-8')
        fw = codecs.open(dst_file, 'w+', encoding='utf-8')
        text = fr.read()
        content = text.split('，')

    for k, v in punc(content):
        fw.write(k + v)
        os.write(1, '%s ---->%s\n' % (k, v))

    fr.close()
    fw.close()
