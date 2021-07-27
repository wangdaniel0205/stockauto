import os, sys, ctypes
import win32com.client
from BotUtil import dbgout, printlog, write_daily_result
from datetime import datetime
import time, calendar
from math import floor


class Creon():

    def __init__(self):
        # 크레온 플러스 공통 OBJECT
        self.cpCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')
        self.cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
        self.cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
        self.cpStock = win32com.client.Dispatch('DsCbo1.StockMst')
        self.cpOhlc = win32com.client.Dispatch('CpSysDib.StockChart')
        self.cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
        self.cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
        self.cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')  


    def check_creon_system(self):
        """크레온 플러스 시스템 연결 상태를 점검한다."""
        # 관리자 권한으로 프로세스 실행 여부
        if not ctypes.windll.shell32.IsUserAnAdmin():
            dbgout('check_creon_system() : admin user -> FAILED')
            return False
    
        # 연결 여부 체크
        if (self.cpStatus.IsConnect == 0):
            dbgout('check_creon_system() : connect to server -> FAILED')
            return False
    
        # 주문 관련 초기화 - 계좌 관련 코드가 있을 때만 사용
        if (self.cpTradeUtil.TradeInit(0) != 0):
            dbgout('check_creon_system() : init trade -> FAILED')
            return False

        if (self.get_basic_info(printOption=False)[0] == ''):
            dbgout('check_creon_system() : cannot get basic info -> FAILED')
            return False
        return True

    def get_basic_info(self, printOption=True):
        self.cpTradeUtil.TradeInit()
        acc = self.cpTradeUtil.AccountNumber[0]      # 계좌번호
        accFlag = self.cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
        self.cpBalance.SetInputValue(0, acc)         # 계좌번호
        self.cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        self.cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
        self.cpBalance.BlockRequest()     
        res = [
            str(self.cpBalance.GetHeaderValue(0)), str(self.get_current_cash()), str(self.cpBalance.GetHeaderValue(1)),
            str(self.cpBalance.GetHeaderValue(3)), str(self.cpBalance.GetHeaderValue(4)), str(self.cpBalance.GetHeaderValue(7))
        ]
        if printOption:
            dbgout('계좌명: ' + res[0])
            dbgout('주문 가능 금액: ' + res[1])
            dbgout('결제잔고수량 : ' + res[2])
            dbgout('평가금액: ' + res[3])
            dbgout('평가손익: ' + res[4])
            dbgout('종목수: ' + res[5])
        return res

    def get_balance(self):
        info = self.get_basic_info(printOption=False)
        return int(info[3]) - int(info[4])

    def get_stock_balance(self, code, printOption=False):
        # use sample: stock_name, stock_qty = get_stock_balance(code)  # 종목명과 보유수량 조회
        """인자로 받은 종목의 종목명과 수량을 반환한다."""
        self.cpTradeUtil.TradeInit()
        acc = self.cpTradeUtil.AccountNumber[0]      # 계좌번호
        accFlag = self.cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
        self.cpBalance.SetInputValue(0, acc)         # 계좌번호
        self.cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        self.cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
        self.cpBalance.BlockRequest()     
        stocks = []
        for i in range(self.cpBalance.GetHeaderValue(7)):
            stock_code = self.cpBalance.GetDataValue(12, i)  # 종목코드
            stock_name = self.cpBalance.GetDataValue(0, i)   # 종목명
            stock_qty = self.cpBalance.GetDataValue(15, i)   # 수량
            if code == 'ALL':
                if printOption == True:
                    printlog(str(i+1) + ' ' + stock_code + '(' + stock_name + ')' 
                        + ':' + str(stock_qty))
                stocks.append({'code': stock_code, 'name': stock_name, 
                    'qty': stock_qty})
            if stock_code == code:  
                if printOption == True:
                    printlog(str(i+1) + ' ' + stock_code + '(' + stock_name + ')' 
                        + ':' + str(stock_qty))
                return stock_name, stock_qty
        if code == 'ALL':
            return stocks
        else:
            stock_name = self.cpCodeMgr.CodeToName(code)
            return stock_name, 0

    def sell(self, code, qty=-1):
        if code == 'ALL':
            try:
                self.cpTradeUtil.TradeInit()
                acc = self.cpTradeUtil.AccountNumber[0]       # 계좌번호
                accFlag = self.cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션   
                while True:    
                    stocks = self.get_stock_balance('ALL') 
                    total_qty = 0 
                    for s in stocks:
                        total_qty += s['qty'] 
                    if total_qty == 0:
                        return True
                    for s in stocks:
                        if s['qty'] != 0:                  
                            self.cpOrder.SetInputValue(0, "1")         # 1:매도, 2:매수
                            self.cpOrder.SetInputValue(1, acc)         # 계좌번호
                            self.cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                            self.cpOrder.SetInputValue(3, s['code'])   # 종목코드
                            self.cpOrder.SetInputValue(4, s['qty'])    # 매도수량
                            self.cpOrder.SetInputValue(7, "1")   # 조건 0:기본, 1:IOC, 2:FOK
                            self.cpOrder.SetInputValue(8, "12")  # 호가 12:최유리, 13:최우선 
                            # 최유리 IOC 매도 주문 요청
                            ret = self.cpOrder.BlockRequest()
                            printlog('최유리 IOC 매도', s['code'], s['name'], s['qty'], 
                                '-> cpOrder.BlockRequest() -> returned', ret)
                            dbgout('거래 결과 ->'+ str(self.cpOrder.GetDibStatus()) + str(self.cpOrder.GetDibMsg1()))
                            if ret == 4:
                                remain_time = self.cpStatus.LimitRequestRemainTime
                                printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)
                                return False
                        time.sleep(1)
                    time.sleep(5)
            except Exception as ex:
                dbgout("sell('ALL') -> exception! " + str(ex))
        else:
            try:
                self.cpTradeUtil.TradeInit()
                acc = self.cpTradeUtil.AccountNumber[0]       # 계좌번호
                accFlag = self.cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션   

                if qty == -1:
                    name, qty = self.get_stock_balance(code)
                else:
                    name, _ = self.get_stock_balance(code)

                if qty > 0:                  
                    self.cpOrder.SetInputValue(0, "1")         # 1:매도, 2:매수
                    self.cpOrder.SetInputValue(1, acc)         # 계좌번호
                    self.cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                    self.cpOrder.SetInputValue(3, code)   # 종목코드
                    self.cpOrder.SetInputValue(4, qty)    # 매도수량
                    self.cpOrder.SetInputValue(7, "1")   # 조건 0:기본, 1:IOC, 2:FOK
                    self.cpOrder.SetInputValue(8, "12")  # 호가 12:최유리, 13:최우선 
                    # 최유리 IOC 매도 주문 요청
                    ret = self.cpOrder.BlockRequest()
                    printlog('최유리 IOC 매도', code, name, qty, 
                        '-> cpOrder.BlockRequest() -> returned', ret)
                    dbgout('거래 결과 ->'+str(self.cpOrder.GetDibStatus()) + str(self.cpOrder.GetDibMsg1()))
                    if ret == 4:
                        remain_time = self.cpStatus.LimitRequestRemainTime
                        printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)
                        return False
                time.sleep(1)
            except Exception as ex:
                dbgout("sell() -> exception! " + str(ex))
                return False
        return True


    def get_buy_ceiling(self, buy_percent):
        info = self.get_basic_info(printOption=False)
        total_asset = int(info[1]) + int(info[4])
        return floor(total_asset * buy_percent)

    def get_buy_qty(self, code, buy_percent, price):
        ceiling = self.get_buy_ceiling(buy_percent)
        cash = self.get_current_cash()
        
        print(ceiling//price)
        if ceiling < cash:
           return ceiling // price
        return floor(cash*0.8) // price
        


    def get_current_cash(self):
        """증거금 100% 주문 가능 금액을 반환한다."""
        self.cpTradeUtil.TradeInit()
        acc = self.cpTradeUtil.AccountNumber[0]    # 계좌번호
        accFlag = self.cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
        self.cpCash.SetInputValue(0, acc)              # 계좌번호
        self.cpCash.SetInputValue(1, accFlag[0])      # 상품구분 - 주식 상품 중 첫번째
        self.cpCash.BlockRequest() 
        return self.cpCash.GetHeaderValue(9) # 증거금 100% 주문 가능 금액

    def get_current_price(self, code):
        """인자로 받은 종목의 현재가, 매수호가, 매도호가를 반환한다."""
        self.cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보
        self.cpStock.BlockRequest()
        item = {}
        item['cur_price'] = self.cpStock.GetHeaderValue(11)   # 현재가
        item['ask'] =  self.cpStock.GetHeaderValue(16)        # 매수호가
        item['bid'] =  self.cpStock.GetHeaderValue(17)        # 매도호가    
        return item['cur_price']


    def buy(self, code, buy_qty):
        """시장가 기본 매수로 지정한 개수만큼 매수한다"""
        try:
            time_now = datetime.now()
            stock_name, _ = self.get_stock_balance(code)  # 종목명과 보유수량 조회
        
            self.cpTradeUtil.TradeInit()
            acc = self.cpTradeUtil.AccountNumber[0]      # 계좌번호
            accFlag = self.cpTradeUtil.GoodsList(acc, 1) # -1:전체,1:주식,2:선물/옵션                
            # 최유리 FOK 매수 주문 설정
            self.cpOrder.SetInputValue(0, "2")        # 2: 매수
            self.cpOrder.SetInputValue(1, acc)        # 계좌번호
            self.cpOrder.SetInputValue(2, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            self.cpOrder.SetInputValue(3, code)       # 종목코드
            self.cpOrder.SetInputValue(4, buy_qty)    # 매수할 수량
            self.cpOrder.SetInputValue(7, "0")        # 주문조건 0:기본, 1:IOC, 2:FOK
            self.cpOrder.SetInputValue(8, "03")       # 주문호가 1:보통, 3:시장가
                                                    # 5:조건부, 12:최유리, 13:최우선 
            # 매수 주문 요청
            ret = self.cpOrder.BlockRequest() 
            printlog('시장가 기본 매수 ->', stock_name, code, buy_qty, '->', ret)
            dbgout('거래 결과 ->'+str(self.cpOrder.GetDibStatus()) + str(self.cpOrder.GetDibMsg1()))
            if self.cpOrder.GetDibStatus() == -1:
                #symbol_list.remove(code)
                dbgout('거래 실패')
                return False
            if ret == 4:
                remain_time = self.cpStatus.LimitRequestRemainTime
                printlog('주의: 연속 주문 제한에 걸림. 대기 시간:', remain_time/1000)
                time.sleep(remain_time/1000) 
                return False
            time.sleep(2)

            stock_name, bought_qty = self.get_stock_balance(code)
            dbgout("`buy("+ str(stock_name) + ' : ' + str(code) + 
                ") -> " + str(buy_qty) + "EA bought!" + ' total: '+ str(bought_qty) +"`")
            return True
        except Exception as ex:
            dbgout("`buy("+ str(code) + ") -> exception! " + str(ex) + "`")
            return False

if __name__ == '__main__':
    Creon = Creon()
    Creon.sell('ALL')