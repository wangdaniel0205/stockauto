from BotUtil import dbgout, printlog, write_daily_result
from CreonUtil import Creon
from DataUtil import DataUtil
from RecordUtil import RecordUtil
from datetime import datetime, timedelta
from math import floor
from time import sleep

class Stock():
    def __init__(self, code, info, isBought, stop_loss=None):
        self.code = code
        self.info = info
        self.isBought = isBought
        self.stop_loss = stop_loss

class HeikinAshi():
    
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

        # for each stock, read moving averages of: ma_close100 
        today = datetime.today().strftime("%Y%m%d")
        past = (datetime.today() - timedelta(days=3)).strftime("%Y%m%d")
        
        for code in symbol_list:
            df = self.DataUtil.query("{} {} {} m5".format(code, past, today)) # take period as the 5min candle
            if df.shape[0] < 100: 
                printlog('{} cannot add 200 close moving average'.format(code))
                symbol_list.remove(code)
                continue
            
            df = df.tail(101).reset_index(drop=True)
            self.to_heikin_ashi(df)
            self.DataUtil.add_moving_avg(df, 'close', 100) # 'ma_close100'

            # add to stock_list
            self.stock_list.append(Stock(code, df, code in bought_list))


        self.Creon.get_basic_info(printOption=True)
        self.Creon.get_stock_balance('ALL',printOption=True)
        self.RecordUtil = RecordUtil()

        return True 

    def run(self):
        if self.Creon.check_creon_system() == False:
            return False
        pass

    def terminate(self):
        pass

    def check_buy_signal(self, cur_price, stock):
        pass

    def check_sell_signal(self, cur_price, stock):
        pass

    def to_heikin_ashi(self, df, i=None):
        if not i:
            for i in range(1,df.shape[0]):
                self.to_heikin_ashi(df, i=i)
            return

        if i == 0:
            return

        heikin_candle = df.iloc[i]
        heikin_candle['open'] = (df.iloc[i-1]['open'] + df.iloc[i-1]['close']) // 2
        heikin_candle['close'] = (df.iloc[i]['open'] + df.iloc[i]['close'] + 
                                  df.iloc[i]['high'] + df.iloc[i]['low']) // 4
        # high and low are the same as before
        # the candle is green if close > open
        df.iloc[i] = heikin_candle
        return
        


if __name__ == '__main__': 
    #print((datetime.today() - timedelta(days=3)).strftime("%Y%m%d"))
    algo = HeikinAshi()
    HeikinAshi().set_up()