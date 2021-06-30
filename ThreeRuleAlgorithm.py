from BotUtil import dbgout, printlog, write_daily_result
from CreonUtil import Creon
from DataUtil import DataUtil
from RecordUtil import RecordUtil
from datetime import datetime, timedelta
from math import floor
from time import sleep

class Stock():
    def __init__(self, code, info, isBought):
        self.code = code
        self.info = info
        self.isBought = isBought


class ThreeRule():
    
    def set_up(self):
        
        self.buy_percent = 0.15 # change appropriately 

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
            if type(self.DataUtil.add_moving_avg(df, 'close', 200)) == type(None):
                printlog('{} cannot add 200 close moving average'.format(code))
                
                symbol_list.remove(code)
                continue

            s = df.iloc[-1]
            info = {'ma_high7': floor(s['ma_high7']), 'ma_low7': floor(s['ma_low7']), 'ma_close200': floor(s['ma_close200'])}
            self.stock_list.append(Stock(code, info, code in bought_list))

        self.Creon.get_basic_info(printOption=True)
        self.Creon.get_stock_balance('ALL',printOption=True)

        self.RecordUtil = RecordUtil()

        return True 

    def run(self):

        if self.Creon.check_creon_system() == False:
            return False

        median_stock_code = self.stock_list[len(self.stock_list)//2].code
        for stock in self.stock_list:
            if stock.code == median_stock_code:
                sleep(20)
            current_price = self.Creon.get_current_price(stock.code)
            while current_price == False:
                current_price = self.Creon.get_current_price(stock.code)
            if stock.isBought == False: # if stock is not bought
                signal = self.check_buy_signal(current_price, stock.info) # check buy signal
                if signal: # if signal
                    dbgout("'{}' buy_signal: current({}) < ma_low7({}) AND current({}) > ma_close200({}) => {}".format(self.DataUtil.code_to_name(stock.code), current_price, stock.info['ma_low7'], current_price, stock.info['ma_close200'], signal))
                    # buy stock
                    qty = self.Creon.get_buy_qty(stock.code, self.buy_percent, current_price)
                    if qty > 0 and self.Creon.buy(stock.code, qty): # if successfully bought
                        stock.isBought = True
                        self.RecordUtil.record_update(code=stock.code, status='b', amount=qty, price=current_price)
                    #else:
                    #    for i, target in enumerate(self.stock_list):
                    #        if target.code == stock.code:
                    #            self.stock_list.pop(i)
                        
                #printlog("'{}' buy_signal: current({}) < ma_low7({}) AND current({}) > ma_close200({}) => {}".format(self.DataUtil.code_to_name(stock.code), current_price, stock.info['ma_low7'], current_price, stock.info['ma_close200'], signal))

            else: # if stock is already bought
                signal = self.check_sell_signal(current_price, stock.info)
                if signal: # check sell signal
                    dbgout("'{}' sell_signal: current({}) > ma_high7({}) => {}".format(self.DataUtil.code_to_name(stock.code), current_price, stock.info['ma_high7'], signal))
                    # sell
                    if self.Creon.sell(stock.code): # if successfully sold
                        self.RecordUtil.record_update(code=stock.code, status='s', amount='x', price=current_price)
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

    def terminate(self):
        balance = self.Creon.get_balance
        self.RecordUtil.record_finalize(balance=balance)




if __name__ == '__main__': 

    algo = ThreeRule()
    algo.set_up()
    algo.terminate()