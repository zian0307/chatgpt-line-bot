import twstock
from twstock import Stock, BestFourPoint
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import io

def update_stock_codes():
    twstock.__update_codes()
    return "股票代碼已更新"

def analyze_stock(stock_code):
    stock = Stock(stock_code)
    analysis = f"分析 {stock_code} 股票：\n"
    analysis += f"五日均價: {stock.moving_average(stock.price, 5)[-1]:.2f}\n"
    analysis += f"五日均量: {stock.moving_average(stock.capacity, 5)[-1]:.0f}\n"
    analysis += f"五日均價持續天數: {stock.continuous(stock.moving_average(stock.price, 5))}\n"
    analysis += f"五日、十日乖離值: {stock.ma_bias_ratio(5, 10)[-1]:.2f}"
    return analysis

def fetch_stock_data(stock_code, year, month):
    stock = Stock(stock_code)
    stock.fetch_from(year, month)
    return f"{stock_code} 從 {year} 年 {month} 月至今的收盤價：\n{stock.price}"

def get_stock_info(stock_code):
    stock_info = twstock.codes[stock_code]
    info = f"{stock_code} 股票資訊：\n"
    info += f"名稱: {stock_info.name}\n"
    info += f"類型: {stock_info.type}\n"
    info += f"市場: {stock_info.market}\n"
    info += f"產業: {stock_info.group}\n"
    info += f"上市日期: {stock_info.start}"
    return info

def best_four_point_analysis(stock_code):
    stock = Stock(stock_code)
    bfp = BestFourPoint(stock)
    analysis = f"{stock_code} 四大買賣點分析：\n"
    analysis += f"買點: {'是' if bfp.best_four_point_to_buy() else '否'}\n"
    analysis += f"賣點: {'是' if bfp.best_four_point_to_sell() else '否'}\n"
    analysis += f"綜合建議: {bfp.best_four_point()}"
    return analysis

def get_realtime_stock_info(stock_codes):
    if isinstance(stock_codes, str):
        stock_codes = [stock_codes]
    realtime_data = twstock.realtime.get(stock_codes)
    info = ""
    for code in stock_codes:
        info += f"{code} 即時股票資訊：\n"
        info += f"成交價: {realtime_data[code]['realtime'].get('latest_trade_price', 'N/A')}\n"
        info += f"漲跌: {realtime_data[code]['realtime'].get('diff', 'N/A')}\n"
        info += f"成交量: {realtime_data[code]['realtime'].get('accumulate_trade_volume', 'N/A')}\n\n"
    return info.strip()

def calculate_rsi(stock_code, period=14):
    stock = Stock(stock_code)
    prices = np.array(stock.price)
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)

    return f"{stock_code} 的 RSI ({period}日) 指標：\n最新RSI值：{rsi[-1]:.2f}"

def stock_screener(criteria):
    results = []
    for stock_id in twstock.twse:
        try:
            stock = Stock(stock_id)
            if not stock.price or not stock.capacity:
                continue  # 跳過沒有價格或成交量數據的股票
            
            latest_price = stock.price[-1]
            latest_volume = stock.capacity[-1]
            
            if (criteria['price_min'] <= latest_price <= criteria['price_max'] and
                criteria['volume_min'] <= latest_volume):
                results.append((stock_id, latest_price, latest_volume))
        except Exception as e:
            print(f"處理股票 {stock_id} 時發生錯誤: {str(e)}")
            continue
    
    results.sort(key=lambda x: x[1])  # 按價格排序
    output = "符合條件的股票：\n"
    for stock_id, price, volume in results[:10]:  # 只顯示前10個結果
        output += f"{stock_id}: 價格 {price:.2f}, 成交量 {volume}\n"
    
    if not results:
        output = "沒有找到符合條件的股票。"
    
    return output

def visualize_stock_history(stock_code, days=30):
    stock = Stock(stock_code)
    plt.figure(figsize=(10, 6))
    plt.plot(stock.price[-days:])
    plt.title(f"{stock_code} 近 {days} 天收盤價走勢")
    plt.xlabel("日期")
    plt.ylabel("價格")
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return buffer