import pandas as pd
import numpy as np
from DataUtil import DataUtil
from datetime import datetime
import time, calendar

def make_new_record(fileName):
    dataUtil = DataUtil()
    cols = ['date', 'balance', 'profit'] + dataUtil.read_stock_list()
    df = pd.DataFrame(columns=cols)
    
    df.to_csv(fileName,index=False)


class RecordUtil():

    recordFormat = "{}_{}_{}"

    def __init__(self):
        ## apply changes to stock items
        self.fileName = 'Record.csv'
        self.dataUtil = DataUtil()
        self.df = pd.read_csv(self.fileName)
        self.date = datetime.today().strftime("%Y-%m-%d")
        
        stocks = self.dataUtil.read_stock_list() 
        old_stocks =  self.df.columns[3:].tolist()

        if not(self.date in self.df['date'].values):
            self.df = self.df.append(pd.Series({'date':self.date}, dtype='object'), ignore_index=True)
            self.save_record()

        diff = list((set(old_stocks) | set(stocks)) - set(old_stocks))
        if len(diff) > 0:
            for new_stock in diff:
                self.df[new_stock] = ""
            self.save_record()

    def record_update(self, code, status, amount, price):
        i = self.df[self.df['date'] == self.date].index.values[0]
        if type(self.df.loc[i,code]) == type(''):
            self.df.loc[i,code] = self.df.loc[i,code] + ', ' + self.recordFormat.format(status,amount,price)
        else:
            self.df.loc[i,code] = self.recordFormat.format(status,amount,price)
        self.save_record()

    def update_profit(self, date=None):
        profit = 0 
        if date == None: date = self.date
        i = self.df[self.df['date'] == date].index.values[0]
        s = self.df.iloc[i,3:].dropna()
        for code in s.where(s.str.contains('s_')).dropna().index.values:
            cur = self.df.iloc[:i+1][code]
            if not any(cur.str.contains('b_').dropna()): # no buy in previous days
                continue
            last_buy = cur.where(cur.str.contains('b_')).dropna().values[-1].split('_')
            last_sell = cur.where(cur.str.contains('s_')).dropna().values[-1].split('_')
            buy_price = int(last_buy[1]) * int(last_buy[2])
            sell_price = int(last_buy[1]) * int(last_sell[2])
            profit += (sell_price - buy_price)
        self.df.loc[i, 'profit'] = profit


    def record_finalize(self, balance):
        i = self.df[self.df['date'] == self.date].index.values[0]
        self.df.loc[i,'balance'] = balance
        self.update_profit()
        self.save_record()
    
    def save_record(self):
        self.df.to_csv(self.fileName,index=False)




if __name__ == '__main__':
    
    record = RecordUtil()
    
    #record.record_update(code='A005380', status='s', amount=3, price=100)