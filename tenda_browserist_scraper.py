import os
import glob
import datetime as dt
from time import sleep
import csv
from browserist import Browser, BrowserSettings, BrowserType
from bs4 import BeautifulSoup


def init(seed_url):
    a_s = BrowserType.CHROME  # tipo de navegador
    b_s = True  # habilita ou desabilita as imagens do navegador
    c_s = True  # mostra ou esconde o navegador
    settings = BrowserSettings(type=a_s, disable_images=b_s, headless=c_s)
    browser = Browser(settings)
    browser.window.set.size(1920, 1200)
    browser.open.url(seed_url)
    btn = '//html/body/div[1]/div/section[1]/div[3]/div[2]/div/button'
    browser.click.button(btn)  # botão dos cookies
    browser.input.value("//*[@id='cep']", "12211-180\n")
    browser.click.button("//*[@class='btn btn-secondary']")
    browser.wait.seconds(7)
    btn = '//html/body/div[1]/div/div[3]/div/div[2]/div/div/div[3]/'
    btn = btn + 'div[1]/div[2]/div/div/div[1]'
    browser.click.button(btn)
    browser.wait.seconds(2)
    return browser


def deleteFile(directory):
    if (os.path.exists(directory)) is not True:
        os.mkdir(directory)
    for f in glob.glob(directory+"*.csv"):
        os.remove(f)


def saveItem(list_input, name, directory):
    try:
        with open(directory+name+".csv", "a") as fopen:  # Open the csv file.
            csv_writer = csv.writer(fopen)
            csv_writer.writerow(list_input)
        return True
    except:
        return False


def write_to_csv(list_input, name='allGroceries', directory='./Mercado'):
    # The scraped info will be written to a CSV here.
    directory = directory + '_' + dt.datetime.now().date().isoformat() + '/'

    if (os.path.isfile(directory+name+'.csv')) is not True:
        saveItem(['ID', 'PRODUTO', 'PRECO-FINAL', 'PRECO-CHEIO',
                 'PRECO/KG', 'PRECO/L', 'DEPARTAMENTO', 'MERCADO'],
                 name, directory)
        saveItem(list_input, name, directory)
    else:
        saveItem(list_input, name, directory)


def get_cards(soup):
    nmb_items = (soup('span', class_="result-title")[0].text).split(' ')[0]
    cards = (soup.find_all('div', class_="card-item"))
    return cards, int(nmb_items)


def get_price_per_kilo(product_name, price_real):
    '''Extrai o peso/volume e calcula o valor do preço por quilo'''
    price_per_kilo = ''
    splited_title = product_name.split(' ')
    for item in splited_title:
        condition_1 = (price_per_kilo) and item.upper().find('KG') > 0
        condition_2 = ((item.upper().split('KG')[0]).replace('.', ''))
        condition_2 = condition_2.replace(',', '').isnumeric()
        if not condition_1 and condition_2:
            weight = float((item.upper().split('KG')[0]).replace(',', '.'))
            price = price_real.replace(',', '.')
            price_per_kilo = (str(round((float(price)/weight)*1, 2)))
        condition_1 = (price_per_kilo) and item.upper().find('G') > 0
        condition_2 = ((item.upper().split('G')[0]).replace('.', ''))
        condition_2 = condition_2.replace(',', '').isnumeric()
        if not condition_1 and condition_2:
            weight = float((item.upper().split('G')[0]).replace(',', '.'))
            price = price_real.replace(',', '.')
            price_per_kilo = (str(round((float(price)/weight)*1000, 2)))
    return price_per_kilo


def get_price_per_litro(product_name, price_real):
    '''Extrai o peso/volume e calcula o valor do preço por litro'''
    price_per_litre = ''
    splited_title = product_name.split(' ')
    for item in splited_title:
        condition_1 = item.upper().find('L') > 0
        condition_2 = ((item.upper().split('L')[0]).replace('.', ''))
        condition_2 = condition_2.replace(',', '').isnumeric()
        if condition_1 and condition_2:
            volume = float((item.upper().split('L')[0]).replace(',', '.'))
            price = price_real.replace(',', '.')
            price_per_litre = (str(round((float(price)/volume)*1, 2)))
        condition_1 = item.upper().find('ML')
        condition_2 = ((item.upper().split('ML')[0]).replace('.', ''))
        condition_2 = condition_2.replace(',', '').isnumeric()
        if condition_1 > 0 and condition_2:
            volume = float((item.upper().split('ML')[0]).replace(',', '.'))
            price = price_real.replace(',', '.')
            price_per_litre = (str(round((float(price)/volume)*1000, 2)))
    return price_per_litre


def get_data(cards):
    data_list = []
    for idx, card in enumerate(cards):
        if card('div', class_="ProductNotAvailableComponent"):
            continue
        product_name = card('h3')[0].get_text()
        if card('span', class_="card-price"):
            price_real = card('span', class_="card-price")[0]
            price_real = price_real.text.split('\xa0')[1].split(' ')[0]
            price_real = price_real.replace(',', '.')
            price_full = card('span', class_="card-after-price")[0]
            price_full = price_full.text.split('\xa0')[1].split(' ')[0]
            price_full = price_full.replace(',', '.')
        else:
            price_real = card('span', class_="card-after-price")[0]
            price_real = price_real.text.split('\xa0')[1].split(' ')[0]
            price_real = price_real.replace(',', '.')
            price_full = ''
        price_per_kilo = get_price_per_kilo(product_name, price_real)
        price_per_litre = get_price_per_litro(product_name, price_real)
        data_list.append([idx+1, product_name, price_real, price_full,
                         price_per_kilo, price_per_litre])

    return data_list


def stop_no_product(cards):
    count_product_NA = 0
    for card in cards:
        if card('div', class_="ProductNotAvailableComponent"):
            count_product_NA = count_product_NA + 1
        if count_product_NA > 20:
            PARE = True
        else:
            PARE = False
    return PARE


def scroll(browser):
    # Get scroll height
    last_number = 1
    count = 0
    nmb_items = 0
    delay = 0.3
    offset = 0
    while True:
        # Scroll down to bottom
        browser.scroll.down_by(450, delay+offset)
        cards, nmb_items = get_cards(BeautifulSoup
                            (browser.driver.page_source, "html.parser"))
        if last_number < 100:
            delay = 0.75
        elif last_number > 100 and last_number < 200:
            delay = 0.5
        elif last_number > 200 and last_number < 500:
            delay = 0.5
        elif last_number > 500 and last_number < 800:
            delay = 0.3
        elif last_number > 800:
            delay = 0.1
        # get_data(cards)
        print(str(len(cards))+'/'+str(nmb_items)+'-'+str(count))
        if len(cards) == nmb_items:
            print(True)
            break
        new_number = len(cards)
        if last_number == new_number:
            count = count + 1
        else:
            count = 0
        if (count > 15) or (stop_no_product(cards) is True):
            print(False)
            break
        last_number = len(cards)
    return cards


def scrape(source_url, browser):
    sleep(3)
    browser.open.url(source_url)
    browser.wait.seconds(2)
    fileName = (str(source_url).rpartition('/')[-1])
    fileName = fileName.replace('.html', '').rsplit(sep='?')[0]
    # cards_list = []
    try:
        print(f"Now Scraping - {source_url}")
        cards = scroll(browser)
        list_to_save = get_data(cards)
    except:
        list_to_save = ''
    for item in list_to_save:
        item.append(fileName.upper())
        item.append('Tenda')
        write_to_csv(item)
    return True


if __name__ == "__main__":
    directory = './Mercado'
    pages = ['https://www.tendaatacado.com.br/sabonetes-bebe',
             'https://www.tendaatacado.com.br/aguas',
             'https://www.tendaatacado.com.br/carne-bovina',
             'https://www.tendaatacado.com.br/frios-e-laticinios',
             ]
    directory = directory + '_' + dt.datetime.now().date().isoformat() + '/'
    try:
        deleteFile(directory)
    except:
        print('Deu ruim')
    browser = init('https://www.tendaatacado.com.br/')
    for page in pages:
        seed_url = page
        print("\nWeb scraping has begun")
        result = scrape(seed_url, browser)
        if result is True:
            pass
        else:
            print(f"Oops, That doesn't seem right!!! - {result}\n")
    if result is True:
        print("Web scraping is now complete!")
        browser.driver.close()
        os.sys.exit()
    else:
        print(f"Oops, That doesn't seem right!!! - {result}\n")
        browser.driver.close()
        os.sys.exit()
