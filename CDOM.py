import requests
from collections import deque
from concurrent.futures import ThreadPoolExecutor,as_completed
from bs4 import BeautifulSoup
from urllib.parse import urlparse,urljoin
import re
from requests.exceptions import (SSLError,ConnectionError,Timeout,RequestException)
import argparse
import json

class SubdomainHunter :
   def __init__(self,domain,depth,max_pages,concurrency,deep_js,output_to_file,timeout):
      self.domain = domain
      self.depth = depth
      self.max_pages = max_pages
      self.crawl_page = 1
      self.visit = set()
      self.history_crawl = set()
      self.concurrency = concurrency
      self.deep_js = deep_js
      self.output_to_file = output_to_file
      self.timeout = timeout

   def crawl(self,do_domain,scheme="https"):
      ## 爬取子域名，最终返回一个集合set()
      if not do_domain.startswith(("https://","http://")):
         do_domain = f"{scheme}://{do_domain}"
      try:
         vt = requests.get(do_domain,timeout=2)
      except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {do_domain} 请求超时")
        return
      except requests.exceptions.ConnectionError:
         print(f"[CONN-ERR] {do_domain} 连接失败（DNS/拒绝/网络不通）")
         return
      except requests.exceptions.HTTPError as e:
         print(f"[HTTP-ERR] {do_domain} 状态码异常: {e.response.status_code}")
         return
      except requests.exceptions.TooManyRedirects:
         print(f"[REDIRECT] {do_domain} 重定向次数过多")
         return
      except requests.exceptions.RequestException as e:
         print(f"[REQ-ERR] {do_domain} 其他请求异常: {e}")
         return
      b1 = BeautifulSoup(vt.text,"lxml")
      a_href = [i1.get("href") for i1 in b1.select("a[href]") if i1.get("href")]
      s_src = [i1.get("src") for i1 in b1.select("script[src]") if i1.get("src")]
      li_href = [i1.get("href") for i1 in b1.select("link[href]") if i1.get("href")]
      if_src = [i1.get("src") for i1 in b1.select("iframe[src]") if i1.get("src")]
      img_src = [i1.get("src") for i1 in b1.select("img[src]") if i1.get("src") ]
      vt1 = urlparse(vt.url).hostname.removeprefix("www.")
      form_action = [i1.get("action") for i1 in b1.select("form[action]") if i1.get("action")]
      w_list = ["http","https",""]
      all_domain = a_href + s_src + li_href + if_src + img_src + form_action
      z_domain = set()
      for i in all_domain:
         ist = i.strip()
         if ist.startswith("#"):
            continue
         else:
            ti = ist.split("#")[0]
            i_scheme = urlparse(ti).scheme
            if i_scheme in w_list and urlparse(ti).netloc == urlparse(self.domain).netloc:
               z_domain.add(urljoin(vt.url,ti))
      if self.deep_js:
         i_re = re.findall(rf"[\w.-]*\.{re.escape(vt1)}",vt.text)
         for d in i_re:
            z_domain.add("https://" + d.lstrip("/"))
      return (z_domain,len(z_domain))      


   def probe(self,subdomain):
      ## 对传入的url进行http/https双线探活,根据探活结果，如果探活失败则标记，具体如何标记是后续的事情
      subdomain = subdomain.removeprefix("https://")
      subdomain = subdomain.removeprefix("http://")
      takeover_risk = False
      
      try:
         https = requests.get(f"https://{subdomain}",timeout=self.timeout)
         print(f"{subdomain} 存活，状态码:{https.status_code}")
         if https.status_code == 404:
            print("疑似 POTENTIAL_TAKEOVER")
            print(https.text)
            takeover_risk = True
         https_text = https.text
         https_status = https.status_code
         https_title = re.findall(r"<title>(.*?)</title>",https_text,re.S | re.I)
         return True,subdomain,https_title,https_status,takeover_risk,"https"
      
      except (SSLError,ConnectionError) :
         print(f"目标的https请求被重置或握手失败,转入http请求尝试↓")
         try:
            http = requests.get(f"http://{subdomain}",timeout=self.timeout)
            http_status = http.status_code
            print(f"{subdomain} 存活，状态码:{http.status_code}")
            if http_status == 404:
                  print("疑似 POTENTIAL_TAKEOVER")
                  print(http.text)
                  takeover_risk = True
            http_text = http.text
            http_status = http.status_code
            http_title = re.findall(r"<title>(.*?)</title>",http_text,re.S | re.I)
            return True,subdomain,http_title,http_status,takeover_risk,"http"
         
         except Timeout:
            print("http 连接超时")
            return False,False,False,False,False,False
         except RequestException:
            print("http 连接失败")
            return False,False,False,False,False,False
      except Timeout:
         print("https 连接超时")
         return False,False,False,False,False,False
      except RequestException as r:
         print("https s连接失败")
         return False,False,False,False,False,False
   
   def TPE(self):
      live_num = 0
      subdomains = []
      with ThreadPoolExecutor(max_workers=self.concurrency) as T:
         futures = [T.submit(self.probe,c) for c in self.history_crawl]  
         for r in as_completed(futures):
            if r.result():
               live_num += 1
               subdomains.append({
                  "subdomain": r.result()[1],
                  "source_evidence": ["found_in_html_href", "found_in_js_regex"],
                  "is_alive": r.result()[0],
                  "protocol": r.result()[5],
                  "status_code": r.result()[3],
                  "title": r.result()[2],
                  "takeover_risk": r.result()[4]
               })
      return live_num,subdomains
   
   def crawl_process_list(self):
      q = deque()
      q.append((self.domain,1))
      
      while q and self.crawl_page <= self.max_pages:
         now_domain,now_depth = q.popleft()
         if now_domain in self.visit:
            continue
            
         elif now_depth <= self.depth:
            self.visit.add(now_domain)
            result_domain = self.crawl(now_domain)[0]
            self.history_crawl.update(result_domain)   ## 历史子域名记录
            self.crawl_page += 1
            for d in result_domain:
               if now_depth + 1 <= self.depth:
                  q.append((d,now_depth + 1))
      

         ## 爬虫操作

   def run(self):
      self.crawl_process_list()
      scan = self.TPE()
      text = {
         "scan_metadata":{
            "root_domain": self.domain,
            "total_pages_crawled": self.crawl_page,
            "unique_subdomains_found": len(self.history_crawl),
            "alive_subdomains_count": scan[0]
         },
         "subdomains":[i for i in scan[1]]
      }
      with open(self.output_to_file,"w",encoding="utf-8") as f1:
               json.dump(text,f1,indent=4,ensure_ascii=False)


if __name__ == "__main__":
   arg = argparse.ArgumentParser()
   arg.add_argument("-d","--domain",required=True,help="待挖掘的主域名(不带协议头)")
   arg.add_argument("-depth",default=2,type=int,help="爬取深度层级（整数，默认 2。深度 1 仅爬取主页提取到的链接；深度 2 会进一步爬进这些同域链接继续挖掘）")
   arg.add_argument("--max-pages",default=30,type=int,help="最大爬取页面数量上限（默认 30，达到此数量强行截断，防止爬爆服务器）")
   arg.add_argument("--deep-js",action="store_true",help="布尔开关。若携带此参数，则在爬取过程中，遇到外部引入的同域 .js 文件时，主动将 JS 代码拉取下来并执行正则子域名深挖")
   arg.add_argument("-c","--concurrency",default=20,type=int,help="探活阶段的最大并发工作线程数（默认 20）")
   arg.add_argument("--timeout",default=3.0,help="单次探活请求超时（默认 3.0 秒）")
   arg.add_argument("-o","--output",default="subdomains.json",help="输出文件名（JSON 格式）")
   vt = arg.parse_args()
   vt7 = SubdomainHunter(vt.domain,vt.depth,vt.max_pages,vt.concurrency,vt.deep_js,vt.output,vt.timeout)
   vt7.run()