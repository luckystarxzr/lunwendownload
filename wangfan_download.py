# -*- coding: gbk -*-
import time
import random
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.edge.service import Service

def webserver():
    driver_path = "msedgedriver.exe"  # 替换为实际的msedgedriver路径

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

    # 输入关键词并执行搜索
    search_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '''/html/body/div[5]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[1]/div[2]/div[2]/input'''))
    )
    search_box.send_keys(keyword)

    search_button = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div[1]/div[4]/span[1]'))
    )
    search_button.click()
    time.sleep(2)

    bought_papers_checkbox = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[1]/div[2]/div/label[1]/span/input'))
    )
    bought_papers_checkbox.click()
    time.sleep(1)

def download_page(driver, papers_need, start_page):
    count = start_page * 20 + 1
    while count <= papers_need:
        time.sleep(2)
        remaining = min(papers_need - count + 1, 20)
        for i in range(remaining):
            print(f"\n###### 正在下载 (第{i+1}条) ######\n")
            term = (count - 1) % 20 + 1
            xpath = f"/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/div/div[{term}]/div/div[5]/div[1]/div/div[2]/div/span"
            try:
                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                download_button.click()
                time.sleep(2)
                print("下载成功!")
                count += 1
                if count > papers_need:
                    break
            except Exception as e:
                print(f"无法点击元素：{e}")
                continue
        if count <= papers_need:
            next_button_xpath = '/html/body/div[5]/div/div[3]/div[2]/div[2]/div[2]/div[2]/div/div/div[2]/div[3]/span[9]'
            next_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, next_button_xpath))
            )
            next_button.click()
            time.sleep(2)
    print(f"页面 {start_page} 下载完毕")

def main(keyword, papers_need):
    with ThreadPoolExecutor(max_workers=4) as executor:
        driver_list = [webserver() for _ in range(4)]
        futures = []
        for i, driver in enumerate(driver_list):
            open_page(driver, keyword)
            start_page = i * (papers_need // 4)
            future = executor.submit(download_page, driver, papers_need // 4, start_page)
            futures.append(future)

        for future in futures:
            future.result()

        for driver in driver_list:
            driver.quit()

if __name__ == "__main__":
    keyword = "计算机艺术"
    papers_need = 100
    main(keyword, papers_need)
