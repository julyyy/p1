from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
from lxml import etree
import os
import time
from threading import Thread
import operator
import math
import shutil
from datetime import datetime

# ==================== 配置 ====================
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44",
    "Content-Type": "text/html;charset=UTF-8"
}

urltemplate = "https://www.hitxhot.org/gallerys/UENzWnBrWCtZV3ZuaUtva2EwWlZtQT09.html?page={}"
pfolder = "C:\\E3\\Down\\pachong\\"
picpath = "C:\\E3\\Down\\pachong\\{}\\{}\\"

RETRYTIME = 0
WAIT_TIMEOUT = 20  # Selenium等待超时时间

# ==================== 工具函数 ====================
def create_driver():
    """创建并返回Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式（可选，取消注释以禁用浏览器窗口）
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def downloadpic(fname, furl):
    """下载图片到本地"""
    global RETRYTIME
    try:
        res = requests.get(furl, headers=headers, timeout=30)
        with open(fname, 'wb') as f:
            f.write(res.content)
        return furl
    except Exception as e:
        if RETRYTIME == 2:
            RETRYTIME = 0
            print(f"[下载失败] {furl} - {str(e)}")
            return "no"
        RETRYTIME += 1
        print(f"[重试下载] {furl}，20秒后重试第{RETRYTIME}次")
        time.sleep(20)
        return downloadpic(fname, furl)

def checkfolderexist(title):
    """检查文件夹是否存在，返回已有的或新名称"""
    dirs = os.listdir(pfolder)
    for dic in dirs:
        if dic[0] == ".":
            continue
        sondic = os.listdir(pfolder + dic)
        for son in sondic:
            if son.split('[')[0] == title:
                return son
    return title

def get_main_page_items(driver, page_index):
    """
    使用Selenium获取主列表页面的所有大图项目
    新网站结构：使用contentme容器中的链接和图片
    """
    try:
        url = urltemplate.format(page_index)
        print(f"[主页] 正在加载第{page_index}页: {url}")
        driver.get(url)
        
        # 等待页面完全加载
        print(f"[主页] 等待页面加载...")
        time.sleep(10)  # 增加延迟
        
        # 等待document.readyState为complete
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # 再等一些时间给JavaScript执行
        time.sleep(3)
        
        # 获取HTML并解析
        html_text = driver.page_source
        
        # 保存源码用于调试
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"[调试] 页面源码已保存到debug_page.html (长度: {len(html_text)})")
        
        html = etree.HTML(html_text)
        
        # 新网站结构：找contentme容器中的<a><img>链接
        items = html.xpath('//div[@class="VKSUBTSWA contentme"]//a[@href]')
        print(f"[主页] 第{page_index}页找到{len(items)}个图片链接")
        
        if len(items) == 0:
            print(f"[调试] 尝试其他XPath选择器...")
            # 尝试更宽泛的选择
            items = html.xpath('//div[contains(@class, "contentme")]//a[@href]')
            print(f"[调试] 找到{len(items)}个contentme中的链接")
        
        return items
    except Exception as e:
        print(f"[错误] 获取主页失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def get_download_link_from_subpage(driver, suburl):
    """
    打开二级页面，获取图片下载链接
    URL已经包含了图片编码，无需进一步处理
    """
    try:
        # 直接从URL中提取实际的图片URL
        # URL格式: /img.html?url=https://...
        if '?url=' in suburl:
            img_url = suburl.split('?url=')[1]
            print(f"[二级页] 从URL提取图片: {img_url}")
            return img_url
        
        print(f"[二级页] 无法从URL提取图片URL: {suburl}")
        return None
        
    except Exception as e:
        print(f"[错误] URL解析失败: {str(e)}")
        return None

def docrawler(page_index, items, driver):
    """
    爬取列表中的每个项目
    新网站结构：items是lxml Element对象（来自html.xpath）
    """
    global totalitems, finisheditem
    
    for idx, item in enumerate(items):
        try:
            # 从lxml Element获取href属性（使用XPath）
            suburl_list = item.xpath('@href')
            if not suburl_list:
                print(f"[警告] 无法获取URL，跳过项目{idx + 1}")
                finisheditem += 1
                continue
            
            suburl = suburl_list[0]
            
            # URL可能是相对的
            if suburl.startswith('/'):
                suburl = "https://www.hitxhot.org" + suburl
            
            print(f"[爬虫] page:{page_index}, item:{idx + 1}/{len(items)}, 打开: {suburl}")
            
            # 访问二级页面获取图片
            img_url = get_download_link_from_subpage(driver, suburl)
            
            if img_url:
                # 下载图片
                imgname = os.path.basename(img_url)
                # 简化文件夹结构，直接使用page_index作为文件夹名
                picfolder = os.path.join(pfolder, f"page_{page_index}")
                
                if not os.path.exists(picfolder):
                    os.makedirs(picfolder)
                    print(f"[文件夹] 创建: {picfolder}")
                
                nofullname = os.path.join(picfolder, imgname)
                
                if not os.path.exists(nofullname):
                    result = downloadpic(nofullname, img_url)
                    if result != "no":
                        print(f"[完成] page:{page_index}, item:{idx + 1}/{len(items)}, 图片已保存: {nofullname}")
                    else:
                        print(f"[失败] 下载失败: {img_url}")
                else:
                    print(f"[跳过] 文件已存在: {nofullname}")
            else:
                print(f"[警告] 无法获取图片URL: {suburl}")
            
            finisheditem += 1
            
        except Exception as e:
            print(f"[错误] 处理项目失败: {str(e)}")
            import traceback
            traceback.print_exc()
            finisheditem += 1
            continue

# ==================== 全局变量 ====================
totalitems = 0
finisheditem = 0

# ==================== 后处理函数 ====================
def rename_all_images():
    """
    全局重命名所有图片为001.jpg、002.jpg等格式，按下载顺序排序
    """
    base_path = pfolder.rstrip("\\")
    
    if not os.path.exists(base_path):
        print(f"[错误] 基础路径不存在: {base_path}")
        return False
    
    # 扫描所有 page_N 文件夹
    page_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("page_"):
            page_folders.append((item, item_path))
    
    page_folders.sort(key=lambda x: int(x[0].split("_")[1]))
    
    if not page_folders:
        print(f"[警告] 未找到任何page_*文件夹")
        return False
    
    print(f"\n{'='*60}")
    print(f"[重命名] 扫描到 {len(page_folders)} 个文件夹")
    print(f"{'='*60}\n")
    
    # 收集所有文件
    all_files = []
    for page_name, page_path in page_folders:
        for file in os.listdir(page_path):
            file_path = os.path.join(page_path, file)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                all_files.append((file_path, file, page_name, mtime))
    
    if not all_files:
        print(f"[警告] 没有找到任何文件")
        return False
    
    # 按修改时间全局排序
    all_files.sort(key=lambda x: x[3])
    
    print(f"[开始] 全局重命名 {len(all_files)} 个文件\n")
    
    # 按顺序重命名
    for idx, (file_path, old_name, page_name, _) in enumerate(all_files, 1):
        ext = os.path.splitext(old_name)[1]
        new_name = f"{idx:03d}{ext}"
        new_path = os.path.join(os.path.dirname(file_path), new_name)
        
        if os.path.exists(new_path) and new_path != file_path:
            print(f"[警告] 目标文件已存在，跳过: {new_name}")
            continue
        
        try:
            os.rename(file_path, new_path)
            if idx % 50 == 0 or idx == len(all_files):  # 每50个显示一次
                print(f"[{idx:3d}/{len(all_files)}] {page_name:8s} {old_name[:30]:30s} → {new_name}")
        except Exception as e:
            print(f"[失败] 无法重命名 {old_name}: {str(e)}")
    
    print(f"\n[完成] 所有文件全局重命名完毕 (001-{len(all_files):03d})")
    return True

def move_images_to_timestamped_folder():
    """
    将所有重命名后的图片从各子文件夹移到单个时间戳文件夹
    """
    base_path = pfolder.rstrip("\\")
    
    if not os.path.exists(base_path):
        print(f"[错误] 基础路径不存在: {base_path}")
        return False
    
    # 创建时间戳文件夹名称（年月日小时分钟）
    now = datetime.now()
    folder_name = now.strftime("%Y%m%d%H%M")
    output_folder = os.path.join(base_path, folder_name)
    
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"\n{'='*60}")
        print(f"[创建] 新文件夹: {folder_name}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print(f"[警告] 文件夹已存在: {folder_name}")
        print(f"{'='*60}\n")
    
    # 扫描所有 page_N 文件夹
    page_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("page_"):
            page_folders.append((item, item_path))
    
    page_folders.sort(key=lambda x: int(x[0].split("_")[1]))
    
    if not page_folders:
        print(f"[警告] 未找到任何page_*文件夹")
        return False
    
    print(f"[扫描] 找到 {len(page_folders)} 个文件夹\n")
    
    # 收集所有文件
    total_count = 0
    all_files = []
    
    for page_name, page_path in page_folders:
        for file in os.listdir(page_path):
            file_path = os.path.join(page_path, file)
            if os.path.isfile(file_path) and file.endswith('.jpg'):
                mtime = os.path.getmtime(file_path)
                all_files.append((file_path, file, mtime))
                total_count += 1
    
    if not all_files:
        print(f"[警告] 没有找到任何jpg文件")
        return False
    
    # 按修改时间全局排序
    all_files.sort(key=lambda x: x[2])
    
    print(f"[开始] 移动 {len(all_files)} 个文件到 {folder_name}\n")
    
    # 移动文件
    success_count = 0
    for idx, (file_path, file_name, _) in enumerate(all_files, 1):
        dest_path = os.path.join(output_folder, file_name)
        
        try:
            shutil.move(file_path, dest_path)
            if idx % 50 == 0 or idx == len(all_files):  # 每50个显示一次
                print(f"[{idx:3d}/{total_count}] {file_name:20s} 移动完成")
            success_count += 1
        except Exception as e:
            print(f"[失败] 无法移动 {file_name}: {str(e)}")
    
    print(f"\n[完成] 成功移动 {success_count}/{len(all_files)} 个文件")
    print(f"[保存] 所有图片已保存到: {folder_name}\n")
    return True
def main():
    global totalitems, finisheditem
    
    # 爬虫配置
    totalpage = 12  # 爬取全部12页
    currentpage = 1
    
    # 创建驱动
    driver = create_driver()
    
    try:
        for i in range(currentpage, totalpage + 1):
            print(f"\n{'='*60}")
            print(f"[开始] 爬虫第 {i}/{totalpage} 页")
            print(f"{'='*60}")
            
            # 获取主列表页的所有项目
            items = get_main_page_items(driver, i)
            
            if not items:
                print(f"[警告] 第{i}页未找到项目，跳过")
                continue
            
            totalitems = len(items)
            finisheditem = 0
            
            # 处理列表中的所有项目
            docrawler(i, items, driver)
            
            print(f"[完成] 第{i}页下载完毕，完成了{finisheditem}/{totalitems}个项目")
            time.sleep(3)
        
        print(f"\n{'='*60}")
        print(f"[完成] 所有页面爬虫任务完成！")
        print(f"{'='*60}")
        
        # 下载完成后，执行后处理
        print(f"\n{'='*60}")
        print(f"[后处理] 开始重命名和移动图片")
        print(f"{'='*60}")
        
        rename_all_images()
        move_images_to_timestamped_folder()
        
        print(f"{'='*60}")
        print(f"[完成] 所有任务完成！所有图片已整理完毕")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n[中止] 用户中断爬虫")
    except Exception as e:
        print(f"\n[错误] 爬虫过程出错: {str(e)}")
    finally:
        driver.quit()
        print("[清理] 关闭浏览器驱动")

if __name__ == "__main__":
    main()
