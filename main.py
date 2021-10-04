import requests
import pytz
from tabulate import tabulate
from datetime import datetime
import time
import logging
import subprocess
from config import telegram_dict

logname = r'/home/ubuntu/hk_usdt_p2p_price_monitoring/log/p2p_notification.log'
logging.basicConfig(filename=logname,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

def binance_p2p_scan(telegram_url, group_chat_id, alert_level):
    payload = {
        "page": 1,
        "rows": 10,
        "payTypes": [
            "FPS"
        ],
        "asset": "USDT",
        "tradeType": "BUY",
        "fiat": "HKD",
        "publisherType": None,
        "merchantCheck": False
    }
    while True:
        try:
            res = requests.post(r'https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/adv/search/', json=payload)
            res = res.json()
            break
        except:
            print('Binance Requests Error')
            time.sleep(5)
    
    if res['success'] != True:
        logging.info('Binance Error')
        return

    json_res = res['data']
    price = [float(ele['adv']['price']) for ele in json_res]
    min_amount = [float(ele['adv']['minSingleTransAmount']) for ele in json_res]
    max_amount = [float(ele['adv']['maxSingleTransAmount']) for ele in json_res]

    df = [price, min_amount, max_amount]
    
    print_df = []
    for i in range(len(price)):
        if price[i] <= alert_level and min_amount[i] <= 2500:
            print_df.append([df[0][i], df[1][i], df[2][i]])

    number_of_transactions = len(print_df)
    if number_of_transactions > 0:
        min_price = min([ele[0] for ele in print_df])
        
        time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n 最低價錢有 ${min_price}'
        message = f'Binance 有 {number_of_transactions} 個 quote 既 rate <= {alert_level} 同埋 minimum <= 2500'
        
        headers = ['Rate', 'Min $', 'Max $']
        requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            time_message + '\n' + message + '```\n ' + tabulate(print_df, headers= headers,tablefmt='fancy_grid', showindex=False) +'```', group_chat_id))

def aax_p2p_scan(telegram_url, group_chat_id, alert_level):
    while True:
        try:
            res = requests.get(r'https://api.aax.com/otc/v2/order/all?coin=USDT&orderType=sell&orderBy=ASC&unit=HKD&paymentMethods=4&amount=-1&page=0&limit=10&region=*&amountType=Ordinary')
            res = res.json()
            break
        except:
            print('AAX Requests Error')
            time.sleep(5)
    

    if res['success'] != True:
        logging.info('AAX Error')
        return

    price = [float(ele['price']) for ele in res['data']['orders']]
    min_amount = [float(ele['minAmount']) for ele in res['data']['orders']]
    max_amount = [float(ele['maxAmount']) for ele in res['data']['orders']]

    print_df = []
    for i in range(len(price)):
        if price[i] <= alert_level and price[i] != 0 and min_amount[i] <= 2500:
            print_df.append([price[i], min_amount[i], max_amount[i]])

    number_of_transactions = len(print_df)
    if number_of_transactions > 0:
        min_price = min([ele[0] for ele in print_df])

        time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n 最低價錢有 {min_price}'
        message = f'AAX 有 {number_of_transactions} 個 quote 既 rate <= {alert_level} 同埋 minimum <= 2500 '
        
        headers = ['Rate', 'Min $', 'Max $']
        requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            time_message + '\n' + message + '``` \n' + tabulate(print_df, headers= headers,tablefmt='fancy_grid', showindex=False) +'```', group_chat_id))

def trim_log():
    rc = subprocess.call("/home/ubuntu/hk_usdt_p2p_price_monitoring/trim_log.sh", shell=True)


def lambda_handler(event=None, context=None):
    alert_level = 7.8
    telegram_url = telegram_dict['telegram_url']
    group_chat_id = telegram_dict['group_chat_id']
    headers = {'Content-Type': 'application/json'}

    while(True):
        logging.info(f'Scanning P2P at {datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")}')
        binance_p2p_scan(telegram_url, group_chat_id, alert_level)
        aax_p2p_scan(telegram_url, group_chat_id, alert_level)
        trim_log()
        time.sleep(10)



if __name__ == '__main__':
    lambda_handler(event=None, context=None)