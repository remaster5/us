#!/usr/bin/env python

import FinanceDataReader as fdr
fdr.__version__
import os
import os.path
import time
import numpy as np
import pandas as pd
import datetime as dt
import textwrap
import csv
import yfinance as yf


LIST_FILENAME = "nasdaq-list.csv"
TARGET = 'NASDAQ'
DATA_DIR_ROOT = "DATA"

print("나스닥 리스트를 가져옵니다.")
nasdaq_list = fdr.StockListing(TARGET)
nasdaq_list.to_csv(LIST_FILENAME)

print(nasdaq_list.shape)

now = dt.datetime.now()
date = now.strftime("%Y-%m-%d")

data_dir = os.path.join(DATA_DIR_ROOT, date)
os.makedirs(data_dir, exist_ok=True)

for i in nasdaq_list.itertuples():
    ssymbol = i.Symbol.replace('.', '-')
    print(f"작업({i.Index}): {ssymbol} / {i.Name}")
    filename = f"{ssymbol}.csv"
    file_path = os.path.join(data_dir, filename)

    if os.path.exists(file_path):
        print(f"{file_path}가 이미 있습니다.\n가져오지 않습니다.")
    else:
        print(f"{ssymbol}를 가져옵니다.")
        tticker = yf.Ticker(ssymbol)
        data = tticker.history(start = "2022-01-01")
        data.to_csv(file_path)
        print(f"{ssymbol}를 가져왔습니다. 잠시 대기합니다.")
        time.sleep(np.random.uniform(0.1, 0.9))

print("모든 항목을 가져왔습니다.")

quater = 21 * 3
# 1 year = 252 = 21 * 3 * 4
# https://www.prorealcode.com/topic/relative-strength-rank-screener/
# https://www.investopedia.com/ask/answers/021015/how-can-you-calculate-volatility-excel.asp
# https://www.investopedia.com/articles/06/historicalvolatility.asp

rs_df = pd.DataFrame(columns=[
    'Symbol',
    'Name',
    'Score',
    'YesterdayScore',
    'Close1',
    'Close2',
    'MA50',
    'MA150',
    'MA200',
    'LastMonthMA200',
    'Min52W',
    'Max52W'
])


def c(symbol):
    link = f"https://finance.yahoo.com/quote/{symbol}/"
    return f"[{symbol}]({link})"


def calc_score(data, day=-1):
    try:
        today = data.loc[data.index[day]]
        one_quarter_ago = data.loc[data.index[day - (quater)]]
        two_quarter_ago = data.loc[data.index[day - (quater * 2)]]
        three_quarter_ago = data.loc[data.index[day - (quater * 3)]]
        four_quarter_ago = data.loc[data.index[day - (quater * 4)]]

        score_1 = today.Close / one_quarter_ago.Close
        score_2 = one_quarter_ago.Close / two_quarter_ago.Close
        score_3 = two_quarter_ago.Close / three_quarter_ago.Close
        score_4 = three_quarter_ago.Close / four_quarter_ago.Close

        # https://www.williamoneil.com/proprietary-ratings-and-rankings/
        total_score = (score_1 * 2) + score_2 + score_3 + score_4
        return total_score

    except IndexError as e:
        print(f"날짜가 충분하지 않은 것 같습니다. {e}")
        return -1


for i in nasdaq_list.itertuples():
    ssymbol = i.Symbol.replace('.', '-')
    print(f"작업({i.Index}): {ssymbol} / {i.Name}")
    filename = f"{ssymbol}.csv"
    file_path = os.path.join(data_dir, filename)
    data = pd.read_csv(file_path)
    today_score = calc_score(data)
    yesterday_score = calc_score(data, -2)

    if today_score != -1:
        today = data.loc[data.index[-1]]
        four_quarter_ago = data.loc[data.index[-1 - (quater * 4)]]

        data_260 = data.tail(260)
        data_260_close = data_260.Close
        max_52w = data_260_close.max()
        min_52w = data_260_close.min()
        data_220_close = data_260_close.tail(220)
        last_month_ma_200 = int(data_220_close.head(200).mean())
        data_200_close = data_220_close.tail(200)
        ma_200 = int(data_200_close.mean())
        data_150_close = data_200_close.tail(150)
        ma_150 = int(data_150_close.mean())
        data_50_close = data_150_close.tail(50)
        ma_50 = int(data_50_close.mean())

        rs_df = rs_df.append({
            'Symbol': ssymbol,
            'Name': i.Name,
            'Score': today_score,
            'YesterdayScore': yesterday_score,
            'Close1': round(four_quarter_ago.Close,4),
            'Close2': round(today.Close,4),
            'MA50': ma_50,
            'MA150': ma_150,
            'MA200': ma_200,
            'LastMonthMA200': last_month_ma_200,
            'Min52W': round(min_52w,4),
            'Max52W': round(max_52w,4),
        }, ignore_index=True)
    print(f"today score: {today_score} / yesterday score: {yesterday_score}")

rs_df['Rank'] = rs_df['Score'].rank()
rs_df['RS'] = (rs_df['Rank'] * 98 / len(rs_df)).apply(np.int64) + 1

rs_df['YesterdayRank'] = rs_df['YesterdayScore'].rank()
rs_df['YesterdayRS'] = (rs_df['YesterdayRank'] * 98 /
                        len(rs_df)).apply(np.int64) + 1

na_index = rs_df['YesterdayRS'].isna()
rs_df['RankChange'] = rs_df['RS'] - rs_df['YesterdayRS']
rs_df[na_index]['RankChange'] = -1

sorted = rs_df.sort_values('Rank', ascending=False)

posts_dir = os.path.join("docs", "_posts")
result_file_path = os.path.join(posts_dir, f"{date}-nasdaq-rs.markdown")

with open(result_file_path, "w") as f:
    header_start = '''\
    ---
    layout: single
    '''
    f.write(textwrap.dedent(header_start))
    f.write(now.strftime('title: "NASDAQ RS %Y년 %-m월 %-d일"\n'))
    f.write(now.strftime("date: %Y-%m-%d %H:%M:%S +0900\n"))
    header_end = '''\
    categories: rs
    ---
    '''
    f.write(textwrap.dedent(header_end))

    comment = '''\
    나스닥 상대강도

    윌리엄 오닐 상대 강도

    ## 나스닥 상대강도
    
    |티커|이름|1년 전|종가|상대강도|
    |------|---|-----|--|------|
    '''
    f.write(textwrap.dedent(comment))

    for i in sorted.itertuples():
        ssymbol = i.Symbol.replace('.', '-')
        if i.RankChange == 0:
            change = ""
        elif i.RankChange > 0:
            change = f"(+{i.RankChange})"
        else:
            change = f"({i.RankChange})"
        f.write(
            f"|{c(ssymbol)}|{i.Name}|{i.Close1}|{i.Close2}|{i.RS} {change}|\n")


result_file_path = os.path.join(
    posts_dir, f"{date}-nasdaq-trend-template.markdown")

minervini = sorted[sorted.RS >= 70]
minervini = minervini[minervini.Close2 > minervini.MA50]
minervini = minervini[minervini.Close2 > minervini.MA150]
minervini = minervini[minervini.Close2 > minervini.MA200]
minervini = minervini[minervini.MA50 > minervini.MA150]
minervini = minervini[minervini.MA150 > minervini.MA200]
minervini = minervini[minervini.MA200 > minervini.LastMonthMA200]
minervini = minervini[minervini.Close2 > minervini.Min52W * 1.3]
minervini = minervini[minervini.Close2 > minervini.Max52W * 0.75]

# Close > MA50, Close > MA150, Close > MA200
# MA50 > MA150 > MA200
# 1달전 MA200 < 오늘 MA200
# Close > 52-low * 1.3
# Close <= 52-high * 0.75
# RS 70점 이상

with open(result_file_path, "w") as f:
    header_start = '''\
    ---
    layout: single
    '''
    f.write(textwrap.dedent(header_start))
    f.write(now.strftime('title: "NASDAQ 미너비니 %Y년 %-m월 %-d일"\n'))
    f.write(now.strftime("date: %Y-%m-%d %H:%M:%S +0900\n"))
    header_end = '''\
    categories: minervini
    ---
    '''
    f.write(textwrap.dedent(header_end))

    comment = '''\
    마크 미니버니 상대강도

    ## 미너비니 상대강도
    
    |티커|이름|종가|RS|신고가,신저가|MA50,150,200|
    |------|---|---|--|---------|------------|
    '''
    f.write(textwrap.dedent(comment))

    for i in minervini.itertuples():
        ssymbol = i.Symbol.replace('.', '-')
        f.write(
            f"|{c(ssymbol)}|{i.Name}|{i.Close2}|{i.RS}|{i.Max52W}, {i.Min52W}|{i.MA50}, {i.MA150}, {i.MA200}|\n")
    
    f.write("\n")
    footer = '''\
    
    '''
    f.write(textwrap.dedent(footer))
