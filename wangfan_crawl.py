# -*- coding: gbk -*-
import time
import random
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.edge.service import Service

def webserver():
    driver_path = "msedgedriver.exe"  # 替换为实际的msedgedriver路径

    # 设置Microsoft Edge的期望能力和选项
    desired_capabilities = DesiredCapabilities.EDGE
    desired_capabilities["pageLoadStrategy"] = "none"

    options = webdriver.EdgeOptions()
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

    service = Service(executable_path=driver_path)
    driver = webdriver.Edge(service=service, options=options)

    return driver

def open_page(driver, keyword):
    driver.get("https://s.wanfangdata.com.cn/advanced-search/paper")
    time.sleep(2)
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, '''/html/body/div[5]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[1]/div[2]/div[2]/input'''))
    ).send_keys(keyword)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[3]/span[1]/span[2]/div[1]/div[1]/div/i'))).click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[3]/span[1]/span[2]/div[1]/div[2]/ul[2]/li[6]'))).click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[3]/span[1]/span[2]/div[2]/div[1]/div/i'))).click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[3]/span[1]/span[2]/div[2]/div[2]/ul[2]/li[5]'))).click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[1]/div[2]/div[4]'))).click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[4]/span[1]'))).click()
    time.sleep(2)
    res_unm = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[1]/div/div[1]/span[1]/span[2]'))).text
    res_unm = int(res_unm.replace(",", ''))
    page_unm = int(res_unm / 20) + 1
    print(f"共找到 {res_unm} 条结果, {page_unm} 页。")
    return res_unm

def get_info(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return element.text
    except:
        return '无'

def get_choose_info(driver, xpath1, xpath2, str):
    try:
        if WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath1))).text == str:
            return WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath2))).text
        else:
            return '无'
    except:
        return '无'

def save_progress(file_path, count):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(count))

def load_progress(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    return 0

def crawl_page(driver, term, file_path, lock):
    try:
        title_xpath = f'''/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/div/div[{term}]/div/div[1]/div[2]/span[2]'''
        abstract_xpath = f'''/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/div/div[{term}]/div/div[3]/span[2]'''
        title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath))).text
        abstract = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, abstract_xpath))).text
        print(f'title: {title}')
        paper_element_xpath = f'/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/div/div[{term}]'
        paper_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, paper_element_xpath)))
        author_area = paper_element.find_element(By.XPATH, './/div[@class="author-area"]')
        authors = [span.text for span in author_area.find_elements(By.XPATH, './/span[@class="authors"]')]
        print(f'authors: {authors}')
        keywords_area = paper_element.find_element(By.XPATH, './/div[@class="keywords-area"]')
        keywords = [span.text for span in keywords_area.find_elements(By.XPATH, './/span[@class="keywords-list"]')]
        print(f'keywords: {keywords}')
        res = f"{title}\t{authors}\t{keywords}\t{abstract}\t".replace("\n", "") + "\n"
        with lock:
            with open(file_path, 'a', encoding='gbk') as f:
                f.write(res)
                print('基本信息写入成功')
    except Exception as e:
        print(f"爬取第 {term} 条失败: {str(e)}")

def crawl(driver, papers_need, theme):
    count = load_progress(f"progress_{theme}.txt") + 1
    file_path = f"wangfan_{theme}.tsv"
    lock = threading.Lock()

    while count <= papers_need:
        random_sleep_time = random.uniform(0.9, 1.5)
        time.sleep(random_sleep_time)

        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for term in range((count-1) % 20 + 1, 21):
                future = executor.submit(crawl_page, driver, term, file_path, lock)
                futures.append(future)

            for future in futures:
                future.result()  # 确保所有线程都执行完毕

        save_progress(f"progress_{theme}.txt", count)
        count += 20

        try:
            next_button_xpath = '//span[@class="next"]'
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, next_button_xpath))).click()
        except Exception as e:
            print(f"翻页失败: {str(e)}")
            break

    print("爬取完毕")

if __name__ == "__main__":
    keyword = "空间"
    papers_need = 100
    driver = webserver()
    open_page(driver, keyword)
    crawl(driver, papers_need, keyword)
    driver.quit()
