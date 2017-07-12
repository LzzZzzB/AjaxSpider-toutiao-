import json
import re
from urllib.parse import urlencode

import pymongo
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import requests
from config import *


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def get_page_index(offset, keyword):

    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 3
    }
    url = "http://www.toutiao.com/search_content/?"+ urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求发生错误")
        return None


def parse_page_index(html):
    data = json.loads(html)    #html本来是text，loads()转化成json对象
    if data and 'data'in data.keys():   #判断if存在，同时json对象data里面含有'data'这个关键字，再用yield生成url列表
        for item in data.get('data'):
            yield item.get('article_url')


def get_page_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求详情页面出错",url)
        return None


def parse_page_detail(html,url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    print(title)
    image_pattern = re.compile('var gallery =(.*?);', re.S)
    result = re.search(image_pattern, html)
    if result:
        # print(result.group(1))已经可以成功输出我们用re获取图片url数据（字符串形式）
        data = json.loads(result.group(1))        #转化为json来解析数据
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')   # 这里的sub_images提取出一个列表[]，字典里面包括多个字典{}
            images = [item.get('url') for item in sub_images]   # 对于每一个在sub_images里面的item, 都使用item.get('url'),来获取其中的url,作为列表[]
            return {
                'title': title,
                'images': images,
                'url': url
            }



def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("存储到MongoDB成功", result)
            return True
        return False
    except TypeError:           # 跳过了不同类型页面，图片排版不同导致的TypeError
        print("TypeErrorrrrrrrr")
        return None

def main():
    html = get_page_index(0,'街拍')
    #print(html)
    for url in parse_page_index(html):
        html= get_page_detail(url)
        if html:
            result = parse_page_detail(html,url)
            #print(result)
            save_to_mongo(result)

if __name__ == '__main__' :
    main()