from BotUtil import dbgout, printlog, write_daily_result
from ThreeRuleAlgorithm import ThreeRule
from datetime import datetime
import time, calendar
import os, sys, ctypes

if __name__ == '__main__': 
    AutoAlgo = ThreeRule()

    if AutoAlgo.set_up() == False: # set up
        sys.exit(0)

    while True:
        t_now = datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
        today = datetime.today().weekday()

        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
            printlog('Today is', 'Saturday.' if today == 5 else 'Sunday.')
            sys.exit(0)

        if t_start < t_now < t_exit :  # AM 09:05 ~ PM 03:20 : RUN
            if AutoAlgo.run() == False:
                sys.exit(0)
            

        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            dbgout('Trade `self-destructed!`')
            sys.exit(0)
        time.sleep(30) 
