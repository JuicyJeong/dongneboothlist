
import time
import schedule
import sys


time_now = ""


def exit():
    print("function exit")
    sys.exit() # 프로그램 종료

def pr():
    print("test...")

def now():
    time_now = time.strftime('%Y-%m-%d-%H-%M', time.localtime(time.time()))
    print("현재시간:",time_now)


    if time_now == "2022-04-30-00-10":
        print("끝.")
        exit()
    else:
        print("실행중...")


schedule.every(60).seconds.do(now)
schedule.every().day.at("10:17").do(exec,open("booth_search_total.py").read())
schedule.every().day.at("06:00").do(exec,open("booth_search_total.py").read())
schedule.every().day.at("12:00").do(exec,open("booth_search_total.py").read())
schedule.every().day.at("18:00").do(exec,open("booth_search_total.py").read())


# time_now = time.strftime('%Y-%m-%d-%H-%M', time.localtime(time.time()))



while True:

    schedule.run_pending()
    time.sleep(10)






