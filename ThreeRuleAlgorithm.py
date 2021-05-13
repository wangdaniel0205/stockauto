from BotUtil import dbgout, printlog, write_daily_result
from CreonUtil import Creon
from DataUtil import DataUtil
from datetime import datetime, timedelta
from math import floor

class Stock():
    def __init__(self, code, info, isBought):
        self.code = code
        self.info = info
        self.isBought = isBought


class ThreeRule():
    
    def set_up(self):
        
        self.buy_percent = 0.4 # change appropriately 

        # init classes 
        self.Creon = Creon()
        if self.Creon.check_creon_system() == False:
            return False
        printlog('Sucessfully Connected to Creon!!')
        self.DataUtil = DataUtil()

        # init stock lists
        symbol_list = self.DataUtil.read_stock_list()
        bought_list = [item['code'] for item in self.Creon.get_stock_balance('ALL')]
        self.stock_list = []

        # for each stock, read moving averages of: ma_low7, ma_high7, ma_close200 
        today = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        past = (datetime.today() - timedelta(days=300)).strftime("%Y%m%d")
        
        for code in symbol_list:
            df = self.DataUtil.query("{} {} {} D".format(code, past, today))
            self.DataUtil.add_moving_avg(df, 'high', 7)
            self.DataUtil.add_moving_avg(df, 'low', 7)
            self.DataUtil.add_moving_avg(df, 'close', 200)
            s = df.iloc[-1]
            info = {'ma_high7': floor(s['ma_high7']), 'ma_low7': floor(s['ma_low7']), 'ma_close200': floor(s['ma_close200'])}
            self.stock_list.append(Stock(code, info, code in bought_list))
        return True 

    def run(self):

        if self.Creon.check_creon_system() == False:
            return False

        for stock in self.stock_list:
            current_price, _, _ = self.Creon.get_current_price(stock.code)
            if stock.isBought == False: # if stock is not bought
                signal = self.check_buy_signal(current_price, stock.info) # check buy signal
                if signal: # if signal
                    # buy stock
                    if self.Creon.buy(stock.code, Creon.get_buy_qty(stock.code, self.buy_percent)): # if successfully bought
                        stock.isBought = True
                        
                printlog("'{}' buy_signal: current({}) < ma_low7({}) AND current({}) > ma_close200({}) => {}".format(self.DataUtil.code_to_name(stock.code), current_price, stock.info['ma_low7'], current_price, stock.info['ma_close200'], signal))

            else: # if stock is already bought
                signal = self.check_sell_signal(current_price, stock.info)
                if signal: # check sell signal
                    # sell
                    if self.Creon.sell(stock.code): # if successfully sold
                        stock.isBought = False 
                printlog("'{}' sell_signal: current({}) > ma_high7({}) => {}".format(self.DataUtil.code_to_name(stock.code), current_price, stock.info['ma_high7'], signal))

        return True

    def check_buy_signal(self, current_price, data):
        '''Return True if buy singal is on, otherwise False'''
        if current_price < data['ma_low7'] and current_price > data['ma_close200']:
            return True
        return False

    def check_sell_signal(self, current_price, data):
        '''Return True if sell singal is on, otherwise False'''
        if current_price > data['ma_high7']:
            return True
        return False





if __name__ == '__main__': 

    algo = ThreeRule()
    algo.set_up()
    algo.run()