import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo
from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

driver = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(driver, 10)

driver.set_window_size(1400, 900)
def search():
    try:
        driver.get("https://www.taobao.com ")
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
            )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button'))
            )
        element.send_keys("美食")
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
            )
        products()
        return total.text
    except TimeoutException:
        return search()

def next_page(page_number):
    print('正在翻页')
    try:
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
            )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
            )
        element.clear()
        element.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
            )
        products()
    except TimeoutException:
        return next_page(page_number)

def products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = driver.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text().split(),
            'paynumber':item.find('.deal-cnt').text()[:-3],
            'information':item.find('.J_ClickStat').text().split(),
            'shopname':item.find('.shopname').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('成功')
    except Exception:
        print('失败')

def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total+1):
        next_page(i)

if __name__ == '__main__':
    main()