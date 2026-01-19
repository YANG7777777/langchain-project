from bs4 import BeautifulSoup
import requests

url = "https://cn.bing.com/" # 抓去bing搜索引擎的网页内容
response = requests.get(url)

# 解决中文乱码问题（知道的情况下）
# response.encoding = 'utf-8'

# 使用 chardet 检测编码
import chardet

# 检测编码
detected_encoding = chardet.detect(response.content)['encoding']
print(f"检测到的编码: {detected_encoding}")
response.encoding = detected_encoding


# 确保请求成功
if response.status_code == 200:
    # 使用 BeautifulSoup 解析网页
    soup = BeautifulSoup(response.text, "lxml") # 使用 lxml 解析器
    # soup = BeautifulSoup(response.text, 'html.parser') # 解析网页内容 html.parser 解析器

    # 查找 <title> 标签
    title_tag = soup.find("title") # 查找第一个 <title> 标签
    if title_tag:
        print("标题:", title_tag.text)
    else:
        print("未找到标题标签")

    all_links = soup.find_all("a") # 查找所有 <a> 标签
    for link in all_links:
        href = link.get("href")
        if href and href.startswith("http"):
            print("绝对链接:", href)
        else:
            print("相对链接:", href)
else:
    print(f"请求失败，状态码：{response.status_code}")
