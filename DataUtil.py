import time
import win32com.client
import pandas as pd
import re
import os, sys, ctypes
from BotUtil import dbgout, printlog, write_daily_result

class DataUtil:
    def __init__(self):
        self.obj_CpCodeMgr = win32com.client.Dispatch('CpUtil.CpCodeMgr')
        self.obj_CpCybos = win32com.client.Dispatch('CpUtil.CpCybos')
        self.obj_StockChart = win32com.client.Dispatch("CpSysDib.StockChart")
        self.cpCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')

    def read_stock_list(self):
        f = open("stock_list.txt", "r")
        stocks = f.read().split(" ")
        return stocks

    def code_to_name(self, code):
        return self.cpCodeMgr.CodeToName(code)

    def to_csv(self, df, inputs):
        code, date_from, date_to, req_type = inputs.split(' ')
        name = self.code_to_name(code)
        file_name = 'readonly/{}_{}_{}_{}.csv'.format(name,date_from,date_to,req_type)
        df.to_csv(file_name, index=False)
        print('Succesfully created {}!!'.format(file_name))

    def from_csv(self, file_name):
        df = pd.read_csv(file_name)
        return df

    def _wait(self):
        time_remained = self.obj_CpCybos.LimitRequestRemainTime
        cnt_remained = self.obj_CpCybos.GetLimitRemainCount(1)  # 0: 주문 관련, 1: 시세 요청 관련, 2: 실시간 요청 관련
        if cnt_remained <= 0:
            timeStart = time.time()
            while cnt_remained <= 0:
                time.sleep(time_remained / 1000)
                time_remained = self.obj_CpCybos.LimitRequestRemainTime
                cnt_remained = self.obj_CpCybos.GetLimitRemainCount(1)

    def add_moving_avg(self, df, col, unit):
        if col not in ('open', 'high', 'low', 'close'):
            printlog('add_moving_avg: col error')
            return None
        if df.shape[0] < int(unit):
            printlog('add_moving_avg: unit error shape[0]={}'.format(df.shape[0]))
            return None
        col_name = 'ma_'+str(col)+str(unit)
        df[col_name] = df[col].rolling(int(unit)).mean()
        return df

    def query(self, inputs):
        """
        http://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=102&page=1&searchString=StockChart&p=8841&v=8643&m=9505
        
        return:
            pd.DataFrame
        """
        code, date_from, date_to, req_type = inputs.split(' ')
        name = self.code_to_name(code)
        b_connected = self.obj_CpCybos.IsConnect
        if b_connected == 0:
            print("연결 실패")
            return None

        list_field_key = [0, 1, 2, 3, 4, 5, 8]
        list_field_name = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
        dict_chart = {name: [] for name in list_field_name}

        # if req_type has T, add int to ushort
        ushort = None
        if type(re.search("m",req_type)) != type(None):
            ushort = int(re.search(r'\d+', req_type).group()) 
            req_type = 'm'


        while True:
            self.obj_StockChart.SetInputValue(0, code)
            self.obj_StockChart.SetInputValue(1, ord('1'))  # 0: 개수, 1: 기간
            self.obj_StockChart.SetInputValue(2, date_to)  # 종료일
            self.obj_StockChart.SetInputValue(3, date_from)  # 시작일
            self.obj_StockChart.SetInputValue(4, 100)  # 요청 개수
            self.obj_StockChart.SetInputValue(5, list_field_key)  # 필드
            self.obj_StockChart.SetInputValue(6, ord(req_type))  # 'D' 일, 'W' 주, 'M' 월, 'm' 분, 'T' 틱
            if ushort != None:
                self.obj_StockChart.SetInputValue(7, ushort)
            self.obj_StockChart.BlockRequest()

            status = self.obj_StockChart.GetDibStatus()
            msg = self.obj_StockChart.GetDibMsg1()
            #print("통신상태: {} {}".format(status, msg))
            if status != 0:
                return None

            cnt = self.obj_StockChart.GetHeaderValue(3)  # 수신개수
            for i in range(cnt):
                dict_item = {name: self.obj_StockChart.GetDataValue(pos, i) for pos, name in zip(range(len(list_field_name)), list_field_name)}
                for k, v in dict_item.items():
                    dict_chart[k].append(v)

            if not self.obj_StockChart.Continue:
                break
            self._wait()

        #print("차트: {} {}".format(cnt, dict_chart))
        df = pd.DataFrame(dict_chart, columns=list_field_name)
        df = df.iloc[::-1] # reverse rows
        return df

if __name__ == '__main__':
    DataUtil = DataUtil()
    target_stocks = [
        'A051910 20201010 20201229 D'
    ]

    for item in target_stocks:
        df = DataUtil.query(item)
        if type(df) == None:
            quit()
        DataUtil.add_moving_avg(df, 'close', '5')
        DataUtil.add_moving_avg(df, 'open', '10')
        DataUtil.to_csv(df, item)
