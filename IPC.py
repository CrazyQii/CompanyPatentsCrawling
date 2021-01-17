"""
爬取soopat专利网站IPC的所有分类
author: hanlinqi
date: 2021/1/10
"""
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import random
from multiprocessing import Pool


class Category(object):
    def __init__(self):
        self.base_url = 'http://www.soopat.com'
        # 采用隧道动态转发，避免ip被封（无忧代理网）
        self.proxyIp = 'tunnel.data5u.com:56789'
        self.proxyUsername = 'a79701cc2f7e8aefc423b4f205bb19b3'
        self.proxyPwd = '1202403'
        self.proxy = {
            'http': f'http://{self.proxyUsername}:{self.proxyPwd}@{self.proxyIp}',
            'https': f'http://{self.proxyUsername}:{self.proxyPwd}@{self.proxyIp}'
        }  # 生成代理，避免爬虫被封
        self.headers = {  # 请求头
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0;Win64;x64) '
                          'AppleWebKit/537.36(KHTML,likeGecko) '
                          'Chrome/87.0.4280.141 '
                          'Safari/537.36',
            'Host': 'www.soopat.com'
        }

    def _get_html(self, url):
        """ 返回soup解析过的html页面 """
        try:
            time.sleep(random.randint(1, 3))  # 休眠
            resp = requests.get(url, headers=self.headers, proxies=self.proxy, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content.decode('utf-8'), 'lxml')
                if soup is not None:
                    return soup
            # 如果页面为空或者请求状态码不为200，重新请求当前链接
            print(f'获取html页面错误：{resp.status_code} -- 3秒后重试')
            return self._get_html(url)
        except Exception as e:
            # 网络连接错误，重新请求当前链接
            print(f'获取html页面错误：{e} -- 5秒后重试')
            return self._get_html(url)

    def _get_html_link(self, url):
        """ 查找soopat专利网的IPC类别链接 """
        try:
            time.sleep(random.randint(1, 3))  # 休眠
            resp = requests.get(url, headers=self.headers, proxies=self.proxy, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content.decode('utf-8'), 'lxml')
                if soup is not None:
                    return soup.find_all('td', attrs={'class': 'IPCChild'})  # 返回当前IPC子类别链接
            # 如果页面为空或者请求状态码不为200，重新请求当前链接
            print(f'获取html页面错误：{resp.status_code} -- 3秒后重试')
            return self._get_html_link(url)
        except Exception as e:
            # 网络连接错误，重新请求当前链接
            print(f'获取html页面错误：{e} -- 5秒后重试')
            return self._get_html_link(url)

    def soup_detail(self, url):
        """ 查询对应IPC类别下的详细页面 """
        try:
            soup = self._get_html(url)
            info = soup.find('p', attrs={'class': 'right'}).find_all('b')  # 查找专利和专利数量
            info = {
                'patents_num': info[0].get_text(),
                'patents_code': info[1].get_text().split('(')[1][:-1]
            }
            self._write_to_csv([info])  # 写入文件
            print(info)
        except Exception as e:
            # 出现错误重复进行请求，直到修复好网络
            print(f'注意: 请手动点击验证码或ip存在问题, 3秒后重新请求!!! {e}')
            self.soup_detail(url)

    def _parse_page(self, word):
        """ 根据IPC类目依次获取 herf 链接 """
        try:
            url = f'{self.base_url}/IPC/Parent/{word}'
            for item_1 in self._get_html_link(url):  # A大类
                url = f"{self.base_url}{item_1.find('a')['href']}"
                for item_2 in self._get_html_link(url):  # A01类
                    url = f"{self.base_url}{item_2.find('a')['href']}"
                    for item_3 in self._get_html_link(url):  # A01B类
                        url = f"{self.base_url}{item_3.find_next_siblings()[1].find('a')['href']}"  # 1/00类链接
                        self.soup_detail(url)  # 找到对应的详细网页
        except Exception as e:
            print(f'解析页面错误：{e}')

    def _write_to_csv(self, data):
        """ 写入文件 """
        try:
            df = pd.DataFrame(data)
            df.to_csv('code.csv', encoding="gb2312", mode='a', index=False, header=False)
            print('数据写入成功')
        except Exception as e:
            print(f'写入文件错误：{e}')

    def start(self):
        """ 启动程序，专利总共分为ABCDEFGH 8个类别 """
        pool = Pool(processes=4)  # 创建多进程
        try:
            print('开始 A and B and C and D')
            pool.map(self._parse_page, (['A', 'B', 'C', 'D']))
            time.sleep(15)
            print('开始 E and F and G and H')
            pool.map(self._parse_page, (['E', 'F', 'G', 'H']))
        except Exception as e:
            print(f'并发进程错误：{e}')


if __name__ == '__main__':
    # 专利类别爬取
    c = Category()
    c.start()
