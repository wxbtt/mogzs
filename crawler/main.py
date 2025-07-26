import os
import sys
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import chardet
import datetime
from config import TARGET_SITES, MAX_PAGES_PER_SITE, REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS, USER_AGENT

class WebsiteCrawler:
    def __init__(self, base_url, output_dir, max_pages=MAX_PAGES_PER_SITE):
        self.base_url = base_url
        self.max_pages = int(max_pages)
        # 输出目录直接使用仓库根目录下的路径
        self.output_dir = output_dir
        self.visited_urls = set()
        self.to_visit_urls = set()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        
        # 清空并创建输出目录
        if os.path.exists(self.output_dir):
            for root, dirs, files in os.walk(self.output_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化全局日志
        self.log_file = "crawl.log"
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Starting crawl for: {base_url}\n")
            f.write(f"Output directory: {output_dir}\n")
    
    def log(self, message):
        """记录日志到全局文件"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
    
    def get_encoding(self, response):
        """自动检测网页编码"""
        encoding = response.encoding
        if not encoding or encoding.lower() == 'iso-8859-1':
            detected = chardet.detect(response.content)
            encoding = detected['encoding']
        return encoding or 'utf-8'
    
    def is_valid_url(self, url):
        """检查URL是否属于基域"""
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == base_parsed.netloc and parsed.scheme in ('http', 'https')
    
    def normalize_url(self, url):
        """规范化URL，移除片段和查询参数"""
        parsed = urlparse(url)
        return parsed.scheme + "://" + parsed.netloc + parsed.path
    
    def save_page(self, url, content, encoding='utf-8'):
        """保存页面内容到文件"""
        parsed = urlparse(url)
        path = parsed.path.lstrip('/')
        
        if not path:
            path = 'index.html'
        elif path.endswith('/'):
            path = os.path.join(path, 'index.html')
        elif not '.' in os.path.basename(path):
            path = path + '.html'
        
        full_path = os.path.join(self.output_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content.encode(encoding, errors='replace'))
        
        self.log(f"Saved: {full_path}")
    
    def extract_links(self, url, soup):
        """从页面提取所有链接"""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            normalized_url = self.normalize_url(absolute_url)
            
            if self.is_valid_url(absolute_url) and normalized_url not in self.visited_urls:
                links.add(normalized_url)
        return links
    
    def crawl(self):
        """爬取单个网站"""
        start_time = time.time()
        self.log(f"Starting crawl for {self.base_url}")
        
        self.to_visit_urls.add(self.normalize_url(self.base_url))
        
        pbar = tqdm(total=self.max_pages, desc=f"Crawling {self.base_url}")
        
        while self.to_visit_urls and len(self.visited_urls) < self.max_pages:
            current_url = self.to_visit_urls.pop()
            
            if current_url in self.visited_urls:
                continue
                
            try:
                response = self.session.get(current_url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    encoding = self.get_encoding(response)
                    try:
                        content = response.content.decode(encoding)
                    except UnicodeDecodeError:
                        content = response.content.decode('utf-8', errors='replace')
                    
                    soup = BeautifulSoup(content, 'html5lib')
                    self.save_page(current_url, content, encoding)
                    
                    new_links = self.extract_links(current_url, soup)
                    self.to_visit_urls.update(new_links)
                    
                    pbar.update(1)
                    pbar.set_postfix({'URL': current_url[:50] + '...'})
                    
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                error_msg = f"Error crawling {current_url}: {str(e)}"
                print(error_msg)
                self.log(error_msg)
                
            finally:
                self.visited_urls.add(current_url)
        
        pbar.close()
        elapsed = time.time() - start_time
        self.log(f"Finished. Visited {len(self.visited_urls)} pages in {elapsed:.2f}s")

def crawl_all_sites(max_pages_per_site):
    """爬取所有配置的网站"""
    print(f"Crawl started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化全局日志
    with open("crawl.log", 'a', encoding='utf-8') as f:
        f.write(f"\n===== New Crawl Session {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    
    for site_url, output_dir in TARGET_SITES.items():
        crawler = WebsiteCrawler(site_url, output_dir, max_pages_per_site)
        crawler.crawl()
    
    print(f"\nAll sites crawled at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with open("crawl.log", 'a', encoding='utf-8') as f:
        f.write(f"\nAll sites crawled at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else MAX_PAGES_PER_SITE
    crawl_all_sites(max_pages)