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

    def record_finalize(self, balance):
        i = self.df[self.df['date'] == self.date].index.values[0]
        self.df.loc[i,'balance'] = balance
        if i != 0:
            self.df.loc[i,'profit'] = balance - self.df.loc[i-1,'balance'] 
        self.save_record()

    def save_record(self):
        self.df.to_csv(self.fileName,index=False)




if __name__ == '__main__':
    make_new_record('Record.csv')
    record = RecordUtil()
    #record.record_update(code='A005380', status='s', amount=3, price=100)