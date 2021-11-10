import requests
import pytz
from tabulate import tabulate
from datetime import datetime
import time
import logging
import subprocess
from config import telegram_dict
from os.path import join, abspath, dirname
import pandas as pd

root_path = dirname(abspath(__file__))
logname = join(root_path, 'log', 'p2p_notification.log')
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
    adv_no = [int(ele['adv']['advNo']) for ele in json_res] 
    price = [float(ele['adv']['price']) for ele in json_res]
    min_amount = [float(ele['adv']['minSingleTransAmount']) for ele in json_res]
    max_amount = [float(ele['adv']['maxSingleTransAmount']) for ele in json_res]

    df = [adv_no, price, min_amount, max_amount]
    
    print_df = []
    for i in range(len(price)):
        if price[i] <= alert_level and min_amount[i] <= 2500:
            print_df.append([df[0][i], df[1][i], df[2][i], df[3][i]])

    old_data = pd.read_csv(join(root_path, 'binance_quote.csv'))
    number_of_transactions = len(print_df)

    if number_of_transactions > 0:

        new_data_df = pd.DataFrame(print_df)
        new_data_df.columns = ['adv_no', 'price', 'min', 'max']

        # No new quotes
        if new_data_df['adv_no'].isin(old_data['adv_no']).all() and old_data['adv_no'].isin(new_data_df['adv_no']).all():
            return
        else:
            new_data_df.to_csv(join(root_path, 'binance_quote.csv'), index=False)
            min_price = new_data_df['price'].min()
        
            time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n 最低價錢有 ${min_price}'
            message = f'Binance 有 {number_of_transactions} 個 quote 既 rate <= {alert_level} 同埋 minimum <= 2500'
            
            headers = ['Rate', 'Min $', 'Max $']
            requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
                time_message + '\n' + message + '```\n ' + tabulate(new_data_df.iloc[:,1:], headers= headers,tablefmt='fancy_grid', showindex=False) +'```', group_chat_id))

    # All existing quotes are closed
    elif number_of_transactions == 0 and old_data.shape[0] != 0:
        new_data_df = pd.DataFrame(columns = ['adv_no', 'price', 'min', 'max'])
        new_data_df.to_csv(join(root_path, 'binance_quote.csv'))

        time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n Binance 沒有適合的 quote'
        requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            time_message, group_chat_id))
        

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

    id = [int(ele['id']) for ele in res['data']['orders']]
    price = [float(ele['price']) if float(ele['price']) != 0 else float(ele['minPrice']) for ele in res['data']['orders']]
    min_amount = [float(ele['minAmount']) for ele in res['data']['orders']]
    max_amount = [float(ele['maxAmount']) for ele in res['data']['orders']]

    print_df = []
    for i in range(len(price)):
        if price[i] <= alert_level and price[i] != 0 and min_amount[i] <= 2500:
            print_df.append([id[i], price[i], min_amount[i], max_amount[i]])

    old_data = pd.read_csv(join(root_path, 'aax_quote.csv'))
    number_of_transactions = len(print_df)

    if number_of_transactions > 0:

        new_data_df = pd.DataFrame(print_df)
        new_data_df.columns = ['id', 'price', 'min', 'max']

        # No new quotes
        if new_data_df['adv_no'].isin(old_data['adv_no']).all() and old_data['adv_no'].isin(new_data_df['adv_no']).all():
            return
        else:
            new_data_df.to_csv(join(root_path, 'aax_quote.csv'), index=False)
            min_price = new_data_df['price'].min()
        
            time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n 最低價錢有 ${min_price}'
            message = f'AAX 有 {number_of_transactions} 個 quote 既 rate <= {alert_level} 同埋 minimum <= 2500'
            
            headers = ['Rate', 'Min $', 'Max $']
            requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
                time_message + '\n' + message + '```\n ' + tabulate(new_data_df.iloc[:,1:], headers= headers,tablefmt='fancy_grid', showindex=False) +'```', group_chat_id))

    # All existing quotes are closed
    elif number_of_transactions == 0 and old_data.shape[0] != 0:
        new_data_df = pd.DataFrame(columns = ['id', 'price', 'min', 'max'])
        new_data_df.to_csv(join(root_path, 'aax_quote.csv'))

        time_message = f'時間：{datetime.now(pytz.timezone("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S")} \n AAX 沒有適合的 quote'
        requests.get(telegram_url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            time_message, group_chat_id))
        
def trim_log():
    rc = subprocess.call(join(root_path, "trim_log.sh"), shell=True)

def lambda_handler(event=None, context=None):
    alert_level = 7.82
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