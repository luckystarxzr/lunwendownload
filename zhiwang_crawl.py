import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver(proxy=None):
    driver_path = "msedgedriver.exe"  # 确保这个路径是正确的
    options = webdriver.EdgeOptions()
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    if proxy:
        capabilities = webdriver.DesiredCapabilities.EDGE
        capabilities['proxy'] = {
            "proxyType": ProxyType.MANUAL,
            "httpProxy": proxy,
            "sslProxy": proxy
        }
        driver = webdriver.Edge(service=Service(driver_path), options=options, desired_capabilities=capabilities)
    else:
        driver = webdriver.Edge(service=Service(driver_path), options=options)
    return driver

def open_page(driver, keyword, start_year, end_year):
    try:
        driver.get("https://kns.cnki.net/kns8/AdvSearch")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="datebox0"]')))

        elm1 = driver.find_element(By.XPATH, '//*[@id="datebox0"]')
        elm2 = driver.find_element(By.XPATH, '//*[@id="datebox1"]')
        driver.execute_script('arguments[0].removeAttribute("readonly");', elm1)
        driver.execute_script('arguments[0].removeAttribute("readonly");', elm2)

        elm1.send_keys(start_year)
        elm2.send_keys(end_year)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="gradetxt"]/dd[1]/div[2]/input'))
        ).send_keys(keyword)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="ModuleSearch"]/div[1]/div/div[2]/div/div[1]/div[1]/div[2]/div[3]/input'))
        ).click()

        res_unm = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="countPageDiv"]/span[1]/em'))
        ).text
        res_unm = int(res_unm.replace(",", ''))
        logging.info(f"共找到 {res_unm} 条结果。")
        return res_unm
    except Exception as e:
        logging.error(f"打开页面失败: {e}")
        return 0

def process_paper(driver, title_element):
    try:
        title = title_element.text
        title_element.click()
        driver.switch_to.window(driver.window_handles[-1])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "keywords"))
        )

        keywords = driver.find_element(By.CLASS_NAME, "keywords").text[:-1]
        url = driver.current_url

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return title, keywords, url
    except Exception as e:
        logging.error(f"处理论文失败: {e}")
        return None, None, None

def save_progress(file_path, count):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(count))

def load_progress(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    return 0

def crawl(driver, papers_need, theme):
    progress_file = f"progress_{theme}.txt"
    count = load_progress(progress_file) + 1
    file_path = f"CNKI_{theme}.tsv"

    with open(file_path, 'a', encoding='gbk') as f:
        while count <= papers_need:
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "fz14")))
                titles = driver.find_elements(By.CLASS_NAME, "fz14")

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(process_paper, driver, title) for title in titles]

                    for future in futures:
                        title, keywords, url = future.result()
                        if title and keywords:
                            f.write(f"{title}\t{keywords}\t{url}\n")
                            save_progress(progress_file, count)
                            count += 1
                            if count > papers_need:
                                break
            except Exception as e:
                logging.error(f"爬取失败: {e}")
                break

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@id='PageNext']"))
                ).click()
            except Exception as e:
                logging.info("没有更多页面可供翻页。")
                break

    logging.info("爬取完毕")

if __name__ == "__main__":
    keyword = "青少年"
    start_year = "2010-01-01"
    end_year = "2020-01-01"
    proxy = None  # 设置为代理服务器地址，例如 "http://proxy.example.com:8080" 如果需要使用代理
    driver = setup_driver(proxy)
    papers_need = 100
    res_unm = open_page(driver, keyword, start_year, end_year)
    papers_need = min(papers_need, res_unm)
    crawl(driver, papers_need, keyword)
    driver.quit()
