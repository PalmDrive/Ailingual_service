# coding:utf8
from __future__ import absolute_import

from xiaobandeng.config import load_config
from xiaobandeng.lean_cloud import init
from xiaobandeng.config import CONFIG
import leancloud
import datetime
env = 'production'
load_config(env)
init(CONFIG)

CLASS_NAME = 'Media'

lean_cloud_class = leancloud.Object.extend(CLASS_NAME)
query = lean_cloud_class.query

name_list = [
    "JavaII 6.5 框架加数据.mp4",
    "JavaII 6.4 可扩展性.mp4",
    "JavaII 6.3 封装.mp4",
    "JavaII 6.2 消除代码复制.mp4",
    "JavaII 6.1 城堡游戏.mp4",
    "JavaII 5.3.2 DoME的新类型.mp4",
    "JavaII 5.3.1 Object类.mp4",
    "JavaII 5.2 多态.mp4",
    "JavaII 5.1.2 向上造型.mp4",
    "JavaII 5.1.1 多态变量.mp4",
    "JavaII 4.2.2 子类父类关系II.mp4",
    "JavaII 4.2.1 子类父类关系.mp4",
    "JavaII 4.1.2 继承.mp4",
    "JavaII 4.1.1 媒体资料库的故事.mp4",
    "JavaII 3.4 Hash表.mp4",
    "JavaII 3.3 集合Set.mp4",
    "JavaII 3.2.2 for-each.mp4",
    "JavaII 3.2.1 对象数组.mp4",
    "JavaII 3.1.3 ArrayList类的操作.mp4",
    "JavaII 3.1.2 范型容器类.mp4",
    "JavaII 3.1.1 记事本.mp4",
    "JavaII 2.4.2 类函数.mp4",
    "JavaII 2.4.1 类变量.mp4",
    "JavaII 2.3 包.mp4",
    "JavaII 2.2.2 开放的访问属性.mp4",
    "JavaII 2.2.1 封闭的访问属性.mp4",
    "JavaII 2.1.2 对象交互.mp4",
    "JavaII 2.1.1 对象的识别.mp4",
    "JavaII 1.5 编程题提示.mp4",
    "JavaII 1.4 对象初始化.mp4",
    "JavaII 1.3 成员变量和成员函数.mp4",
    "JavaII 1.2 定义类.mp4",
    "JavaII 1.1 用类制造对象.mp4",
    "Java 7-2.2 本地变量.mp4",
    "Java 7-2.1 参数传递.mp4",
    "Java 7-1.2 调用函数.mp4",
    "Java 7-1.1 定义函数.mp4",
    "Java 6-2.3 Math类.mp4",
    "Java 6-2.2 字符串操作.mp4",
    "Java 6-2.1 字符串变量.mp4",
    "Java 6-1.3 包裹类型.mp4",
    "Java 6-1.2 逃逸字符.mp4",
    "Java 6-1.1 字符类型.mp4",
    "8.2.2 MVC设计模式.mp4",
    "8.2.1 JTable.mp4",
    "8.1.3 内部类.mp4",
    "8.1.2 反转控制.mp4",
    "8.1.1 布局管理器.mp4",
    "7.3.3 接口设计模式.mp4",
    "7.3.2 接口.mp4",
    "7.3.1 狐狸与兔子.mp4",
    "7.2.2 数据与表现分离.mp4",
    "7.2.1 细胞自动机.mp4",
    "7.1 抽象.mp4",
    "5-2.4 二维数组.mp4",
    "5-2.3 素数.mp4",
    "5-2.2 遍历数组.mp4",
    "5-2.1 数组变量.mp4",
    "5-1.4 投票统计.mp4",
    "5-1.3 数组的元素.mp4",
    "5-1.2 创建数组.mp4",
    "5-1.1 初试数组.mp4",
    "4-3.2 最大公约数.mp4",
    "4-3.1 求和.mp4",
    "4-2.3 逻辑类型.mp4",
    "4-2.2 多重循环.mp4",
    "4-2.1 循环控制.mp4",
    "4-1.2 复合赋值.mp4",
    "4-1.1 for循环.mp4",
    "3-2.4 整数分解.mp4",
    "3-2.3 猜数游戏.mp4",
    "3-2.2 算平均数.mp4",
    "3-2.1 计数循环.mp4",
    "3-1.4 do-while循环.mp4",
    "3-1.3 while循环.mp4",
    "3-1.2 数数字.mp4",
    "3-1.1 循环.mp4",
    "2.3.2 对象串行化.mp4",
    "2.3.1 流的应用.mp4",
    "2.2.3 格式化输入输出.mp4",
    "2.2.2 汉字编码.mp4",
    "2.2.1 文本流.mp4",
    "2.1.3 流过滤器.mp4",
    "2.1.2 文件.mp4",
    "2.1.1 流.mp4",
    "2-2.5 多路分支.mp4",
    "2-2.4 判断语句的常见问题.mp4",
    "2-2.3 嵌套和级联的判断.mp4",
    "2-2.2 判断语句.mp4",
    "2-2.1 做判断.mp4",
    "2-1.2 关系运算.mp4",
    "2-1.1 比较.mp4",
    "1.2.4 异常遇到继承.mp4",
    "1.2.3 异常捕捉时的匹配.mp4",
    "1.2.2 抛出异常.mp4",
    "1.2.1 异常.mp4",
    "1.1.4 finally.mp4",
    "1.1.3 捕捉到的异常.mp4",
    "1.1.2 异常捕捉机制.mp4",
    "1.1.1 捕捉异常.mp4",
    "1-3.1 如何交作业.mp4",
    "1-2.6 类型转换.mp4",
    "1-2.5 优先级.mp4",
]

total = 0
for name in name_list:
    media_name = name.rstrip(".mp4")
    query.equal_to("media_name", media_name)  #‘XXXX’

    media_list = query.find()
    if not media_list:
        media_name1 = name.replace(" ", "_")   #1.2_XXX.mp4
        query.equal_to("media_name", media_name1)
        media_list = query.find()

        if not media_list:
            media_name2 = media_name + ".mp4"  #1.2 XXX.mp4
            query.equal_to("media_name",media_name2)
            media_list = query.find()

            if not media_list:
                media_name3 = media_name.replace(" ", "_")
                query.equal_to("media_name", media_name3) #1.2_XXX
                media_list = query.find()
                if not media_list:
                    print "not found:", media_name
                    continue


    media = media_list[0]
    print media_name,
    print media.get("duration")
    total+=media.get("duration")

    media.set("company_name","网易云课堂")
    media.save()

def turn_date(sec):
    a=datetime.datetime(1970,1,1,0,0,0)
    d =datetime.timedelta(seconds=sec)
    return a+d-a

s=""
s+= 'length:%s'%len(name_list)
s+= 'seconds:%s'%total
s+= 'minutes:%s'%(total/60.0)
s+= 'hour:%s'%turn_date(total)
print s

import os
os.system("say ok")