# 配置要爬取的网站及对应的保存目录
TARGET_SITES = {
    "http://play.ruanyazyk.com/": "ruanya",
    "https://wmdz.com/": "cangku", 
    "https://www.heimao.app/": "heimao"
}

# 默认设置
MAX_PAGES_PER_SITE = 100  # 每个站点最大爬取页面数
REQUEST_TIMEOUT = 10      # 请求超时时间(秒)
DELAY_BETWEEN_REQUESTS = 1  # 请求间延迟(秒)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"