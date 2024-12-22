# -*- coding: gbk -*-
import time
from selenium.webdriver.common.action_chains import ActionChains
import random
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def webserver():
    driver_path = "msedgedriver.exe"
    service = Service(executable_path=driver_path)
    options = webdriver.EdgeOptions()
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    driver = webdriver.Edge(service=service, options=options)
    return driver

def open_page(driver, keyword, start_year, end_year):
    driver.get("https://kns.cnki.net/kns8/AdvSearch")
    time.sleep(1)
    elm1 = driver.find_element(By.XPATH, '//*[@id="datebox0"]')
    elm2 = driver.find_element(By.XPATH, '//*[@id="datebox1"]')
    js1 = 'arguments[0].removeAttribute("readonly");'
    driver.execute_script(js1, elm1)
    driver.execute_script(js1, elm2)
    elm1.send_keys(start_year)
    elm1.click()
    time.sleep(1)
    elm2.send_keys(end_year)
    time.sleep(1)
    elm2.click()
    time.sleep(1)
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, '''//*[@id="gradetxt"]/dd[1]/div[2]/input'''))
    ).send_keys(keyword)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="ModuleSearch"]/div[1]/div/div[2]/div/div[1]/div[1]/div[2]/div[3]/input'))).click()
    time.sleep(1)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="ModuleSearch"]/div[2]/div/div/ul/li[1]/a'))).click()
    time.sleep(1)
    res_unm = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="countPageDiv"]/span[1]/em'))).text
    res_unm = int(res_unm.replace(",", ''))
    page_unm = int(res_unm / 20) + 1
    print(f"共找到 {res_unm} 条结果, {page_unm} 页。")
    return res_unm

def click_with_actions(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        actions = ActionChains(driver)
        actions.move_to_element(element).click().perform()
        print("点击成功")
    except Exception as e:
        print(f"点击失败: {e}")

def click_iframe_button(driver, iframe_id, element_id):
    try:
        driver.switch_to.frame(driver.find_element(By.ID, iframe_id))
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        driver.execute_script("arguments[0].click();", element)
        print("点击成功")
    except Exception as e:
        print(f"点击失败: {e}")
    finally:
        driver.switch_to.default_content()

def download(driver, papers_need, retries=3):
    count = 1
    while count <= papers_need:
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '''//*[@id="DFR"]'''))
        ).click()
        time.sleep(1)
        for i in range((count-1) % 20 + 1, 21):
            print(f"\n###### 正在下载 {count} (第{(count-1) // 20 + 1}页第{i}条) ######\n")
            term = (count-1) % 20 + 1
            try:
                ye_xpath = f"/html/body/div[2]/div[2]/div[2]/div[2]/div/div[2]/div[1]/div[1]/div/div/div/table/tbody/tr[{term}]/td[2]/a"
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, ye_xpath))
                ).click()
                time.sleep(random.uniform(0.7, 1))

                download_button_xpath = '//*[@id="pdfDown"]'
                download_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, download_button_xpath))
                )
                driver.execute_script("arguments[0].click();", download_button)
                print("下载触发成功")

            except Exception as e:
                print(f"无法下载文献: {e}")

            count += 1

        try:
            next_page_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "PageNext"))
            )
            next_page_element.click()
        except Exception as e:
            print(f"无法找到下一页按钮: {e}")
            print("遇到验证码，请手动进行验证。完成后按 Enter 键继续...")
            input("按 Enter 键继续程序执行...")
    print("下载完毕")

if __name__ == "__main__":
    keyword = "计算机操作系统"
    start_year = "2019-01-01"
    end_year = "2021-01-01"
    driver = webserver()
    papers_need = 200
    res_unm = open_page(driver, keyword, start_year, end_year)
    papers_need = min(papers_need, res_unm)
    download(driver, papers_need)
    driver.quit()
