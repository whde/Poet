#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import importlib
from bs4 import BeautifulSoup
from urllib.parse import quote
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import string
import time
import re
import pymysql
import hashlib


root_folder = 'images/'
filename = 'Poet.csv'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}
writer = ''
db = ''


def create_id():
    m = hashlib.md5(str(time.time()).encode('utf-8'))
    return m.hexdigest()


def getwebdatasoup(url):
    url = quote(url, safe=string.printable)
    http = urllib3.PoolManager()
    web_data = http.request('GET', url, headers=headers).data
    soup = BeautifulSoup(web_data, 'html.parser', from_encoding='utf-8')
    return soup


def downloadimg(url, filepath):
    try:
        http = urllib3.PoolManager()
        r = http.request('GET', url)
        data = r.data
        f = open(filepath, 'wb+')
        f.write(data)
        print(u'正在保存的一张图片为:', filepath)
        f.close()
    except Exception as e:
        print(url+" error", e)
        pass


def ajaxziliao(id):
    url = 'https://so.gushiwen.org/authors/ajaxziliao.aspx?id='+id
    print(url)
    soup = getwebdatasoup(url)
    if soup is None:
        return '', ''
    contyishang = soup.find(class_='contyishang')
    if contyishang is None:
        return '', ''
    type = ''
    try:
        type = contyishang.select('div > h2 > span')[0].get_text()
    except Exception as e:
        print(e)
        pass
    ziliaos = contyishang.findAll('p')
    ziliaostr = ''
    re_br = re.compile('<br.*?/?>')  # 处理换行
    for ziliao in ziliaos:
        contsonstr = str(ziliao)
        contsonhtml = re_br.sub(r'\n', contsonstr)  # 将br转换为换行
        contson = BeautifulSoup(contsonhtml, "html.parser")
        content = contson.get_text()
        ziliaostr = ziliaostr+content+'\n'
    ziliaostr = pymysql.escape_string(ziliaostr)
    return type, ziliaostr


def detail(url):
    soup = getwebdatasoup(url)
    main3 = soup.find(class_='main3')
    left = main3.find(class_='left')
    sonspic = left.find(class_='sonspic')
    filepath = ''
    try:
        divimg = sonspic.find(class_='divimg')
        img = divimg.find('img').get('src')
        imgname = img.split('/')[-1]
        filepath = root_folder + str(imgname)
        downloadimg(img, filepath)
    except Exception as e:
        print(e)
        pass

    poet = sonspic.select('div > h1 > span > b')
    name = ''
    try:
        name = poet[0].get_text()
    except Exception as e:
        print(e)
        pass
    try:
        namedetail = sonspic.select('div > p')
        namedetail = namedetail[0].contents[0]
    except Exception as e:
        print(e)
        pass

    shirenid = create_id()
    sql = "insert into shiren(name, img, introduce, shirenid)\
     values ('%s', '%s', '%s', '%s');" % \
          (name, filepath, namedetail, shirenid)
    try:
        db.cursor().execute(sql)
        pass
    except Exception as e:
        print(sql)
        print(str(e))
        pass

    fanyiquanlist = left.findAll(name="div", class_='sons', attrs={"id": re.compile(r"fanyiquan(\s\w+)?")})
    for fanyiquan in fanyiquanlist:
        id = fanyiquan.get('id').replace('fanyiquan', '')
        type, ziliao = ajaxziliao(id)
        sql = "insert into ziliao(shirenid, type, detail)\
         values ('%s', '%s', '%s');" % \
              (shirenid, type, ziliao)
        try:
            db.cursor().execute(sql)
            pass
        except Exception as e:
            print(sql)
            print(str(e))
            pass
    print('')


# 爬取每页下面的内容
def page(url):
    soup = getwebdatasoup(url)
    main3 = soup.find(class_='main3')
    left = main3.find(class_='left')
    sonspic = left.findAll(class_='sonspic')
    for sonpic in sonspic:
        a = sonpic.select('div > p > a')[0]
        if a is not None:
            herf = 'https://so.gushiwen.org'+a.get('href')
            print(herf)
            detail(herf)
    db.commit()


# 获取排行榜的页数
def getpages():
    url = 'https://so.gushiwen.org/authors/default.aspx?p=1&c='
    soup = getwebdatasoup(url)
    # 找总页数
    sumpage = soup.find(attrs={'id': 'sumPage'})
    pages = sumpage.get_text()
    print(pages)
    return pages


# 开始爬取数据
def spider():
    i = 1
    # 去获取排行榜的页数
    pages = getpages()
    while i <= int(pages):
        # 拼接每一页的URL地址
        pageurl = 'https://so.gushiwen.org/authors/default.aspx?p='+str(i)+'&c='
        print(pageurl)
        # 获取每页下面的内容
        page(pageurl)
        i = i+1
        pass
    else:
        print('大于页数')


# 程序入口
if __name__ == "__main__":
    importlib.reload(sys)
    if os.path.isdir(root_folder):
        pass
    else:
        os.mkdir(root_folder)
    print('mysql __init__')
    db = pymysql.connect(
        host="localhost",
        user="root",
        passwd="666666",
        port=3306,
        db="poet")
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS shiren;")
    cursor.execute("DROP TABLE IF EXISTS ziliao;")
    cursor.execute("""SET SQL_SAFE_UPDATES = 0;""")
    shiren = '''
    CREATE TABLE shiren (id int primary key auto_increment,
    name text,
    img text,
    introduce text,
    shirenid text);
    '''
    try:
        cursor.execute(shiren)
        pass
    except Exception as e:
        print(str(e))
    ziliao = '''
    CREATE TABLE ziliao (id int primary key auto_increment,
    shirenid text,
    type text,
    detail text);
    '''
    try:
        cursor.execute(ziliao)
        pass
    except Exception as e:
        print(str(e))

    # 开始爬取数据
    print('**** spider ****')
    spider()
