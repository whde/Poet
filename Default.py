#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import csv
import string
import time


filename = 'Poetry.csv'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}
writer = ''


def getwebdatasoup(url):
    url = quote(url, safe=string.printable)
    http = urllib3.PoolManager()
    web_data = http.request('GET', url, headers=headers).data
    soup = BeautifulSoup(web_data, 'html.parser', from_encoding='utf-8')
    return soup


# 爬取每页下面的内容
def page(url):
    soup = getwebdatasoup(url)
    main3 = soup.find(class_='main3')
    left = main3.find(class_='left')
    sons = left.findAll(class_='sons')
    for son in sons:
        cont = son.find(class_='cont')
        namep = cont.find('p')
        name = namep.get_text()
        a = namep.find('a')
        herf = a.get('href')
        source = cont.find(class_='source').findAll('a')
        cstr = source[0].get_text()
        author = source[1].get_text()
        contson = cont.find(class_='contson')
        re_br = re.compile('<br.*?/?>')  # 处理换行
        contsonstr = str(contson)
        contsonhtml = re_br.sub(r'\n', contsonstr)  # 将br转换为换行
        contson = BeautifulSoup(contsonhtml, "html.parser")
        content = contson.get_text()
        tag = son.find(class_='tag')
        tags = ''
        if tag is not None:
            tags = tag.get_text().replace('\n', '')
        print(herf+'\n'+name+'\n'+cstr+':'+author+'\n'+content+'\n'+tags+'\n\n')
        arr = [name, herf, cstr, author, content, tags]
        try:
            writer.writerow(arr)
        except Exception as e:
            print('Error:', e)
            pass


# 获取排行榜的页数
def getpages():
    url = 'https://www.gushiwen.org/shiwen/default.aspx?page=1&type=0&id=0'
    soup = getwebdatasoup(url)
    # 找总页数
    sumPage = soup.find(attrs={'id': 'sumPage'})
    pages = sumPage.get_text()
    print(pages)
    return pages


# 开始爬取数据
def spider():
    i = 1
    # 去获取排行榜的页数
    pages = getpages()
    while i <= int(pages):
        # 拼接每一页的URL地址
        pageurl = 'https://www.gushiwen.org/shiwen/default.aspx?page='+str(i)+'&type=0&id=0'
        print(pageurl)
        # 获取每页下面的内容
        page(pageurl)
        time.sleep(5)
        i = i+1
        pass
    else:
        print('大于页数')


# 程序入口
if __name__ == "__main__":
    try:
        csvfile = open(filename, "w", encoding="utf-8")
        writer = csv.writer(csvfile)
        writer.writerow(['name', 'herf', 'cstr', 'author', 'content', 'tags'])
    except Exception as e:
        print('Error:', e)
        pass
    pass
    # 开始爬取数据
    print('**** spider ****')
    spider()
