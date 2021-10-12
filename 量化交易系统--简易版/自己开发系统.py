#coding:utf-8
import dateutil.parser
import numpy as np
import pandas as pd
from pylab import plt,mpl
plt.style.use('seaborn')
import akshare as ak
import datetime
import dateutil
import tushare as ts

# trade_cal=ak.tool_trade_date_hist_sina()
# trade_cal.to_excel('trade_cal.xlsx')
trade_cal=pd.read_excel('trade_cal.xlsx')
# trade_cal['trade_date']=trade_cal['trade_date'].apply(lambda x: x.strftime('%Y-%m-%d'))
# print(trade_cal)


cash=100000
start_date='2021-07-08'
end_date='2021-09-30'

class Context:
    def __init__(self,cash,start_date,end_date):
        self.cash=cash
        self.start_date=start_date
        self.end_date=end_date
        self.positions={}
        self.benchmark=None
        self.date_range=trade_cal[(trade_cal['trade_date']!=None) & (trade_cal['trade_date']>=start_date) & \
                                  (trade_cal['trade_date']<=end_date)].loc[:,'trade_date'].values
        # self.dt=datetime.datetime.strptime('',start_date)
        # self.dt=dateutil.parser.parse(start_date)
        self.dt=None
context=Context(cash,start_date,end_date)
# print(context.date_range)

class G:
    pass
g=G()

def set_benchmark(security): #只支持一直股票作为基准
    context.benchmark=security


#获取从今天起count天的多少天的数据
def attribute_history(security,count,fields=('open','close','high','low','volume')):
    end_date=(context.dt-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    start_date=(trade_cal[(trade_cal['trade_date']<=end_date)][-count:].iloc[0,:]['trade_date']).strftime('%Y-%m-%d')
    print(start_date,end_date)
    return attribute_daterange_history(security,start_date,end_date,fields)
# attribute_history('600085',10)

def attribute_daterange_history(security,start_date,end_date,fields=('open','close','high','low','volume')):


    df=ts.get_k_data(security,start_date,end_date)
    df=df.set_index('date')
    df.to_excel(security+'.xlsx')
    df=pd.read_excel(security+'.xlsx',index_col='date',parse_dates=True)
    # df=df.dropna(inplace=True)

        # print('wrong')

    return df
# print(attribute_daterange_history('601318','2021-08-01','2021-09-09'))

def get_today_data(security):
    today=context.dt.strftime('%Y-%m-%d')
    try:
        # f=open(security+'.xlsx',encoding='utf-8').read()
        data=pd.read_excel(security+'.xlsx',index_col='date',parse_dates=True).loc[today,:]
    # except FileNotFoundError:
    except:
        data=ts.get_k_data(security,today,today).iloc[0,:]
    # except KeyError:
    #     data=pd.Series()
    # print(data)
    return data

# get_today_data('601318')

def _order(today_data,security,amount):
    p=today_data['open']

    if len(today_data)==0:
        print('今日停牌')


    if context.cash-amount* p <0:
        amount=int(context.cash/p)
        print('现金不足，已调整为%d'%(amount))

    if amount % 100 !=0:
        if amount !=-context.positions.get(security,0):
            amount= int(amount/100)*100
            print('不是100的倍数，已调整为%d'%(amount))

    if context.positions.get(security,0)< -amount:
        amount = -context.positions.get(security,0)
        print('卖出股票数不能超过持仓数，已调整为%d' %amount)

    context.positions[security]=context.positions.get(security,0)+amount
    #字典里的get 方法 取key是security的值，如果没有返回0
    context.cash -= amount*p
    if context.positions[security]==0:
        del context.positions[security]

def order(security,amount):
    today_data=get_today_data(security)
    _order(today_data,security,amount)


def order_target(security,amount):
    if amount <0:
        print('数量不能为负，已经调成0')
        amount=0

    today_data=get_today_data(security)
    hold_amount=context.positions.get(security,0)
    delta_amount=amount-hold_amount
    _order(today_data,security,delta_amount)

def order_value(security,value):
    today_data=get_today_data(security)
    amount=int(value/today_data['open'])
    _order(today_data,security,amount)

def order_target_value(security,value):
    today_data=get_today_data(security)
    if value<0:
        print('价值不能为负，已调整为0')
        value=0
    hold_value=context.positions.get(security,0)*today_data['open']
    delta_value=value-hold_value
    order_value(security,delta_value)

# _order(get_today_data('601318'),'601318',-100)
# print(context.positions)
# order('601318',100)
# order_value('600621',3000)
# order_target('000420',520)
# order_target_value('000420',30000)
# print(context.positions)


#回测
def run():
    plt_df=pd.DataFrame(index=pd.to_datetime(context.date_range),columns=['value'])
    init_value=context.cash
    initialize(context)
    last_prize={}
    for dtt in context.date_range:
        # context.dt=dateutil.parser.parse(dtt)
        dtt=pd.to_datetime(dtt)
        context.dt=dtt
        handle_data(context)
        value=context.cash
        for stock in context.positions:
            #考虑到停牌的情况
            today_data=get_today_data(stock)
            if len(today_data)==0:

                p=last_prize[stock]
            else:
                p=get_today_data(stock)['open']
                last_prize[stock]=p
            value += p*context.positions[stock]
        plt_df.loc[dtt,'value']=value #这个是最终的持仓市值

    #收益率
    plt_df['ratio']=(plt_df['value']-init_value)/init_value

    #benchmark
    bm_df=attribute_daterange_history(context.benchmark,context.start_date,context.end_date)
    bm_init=bm_df['open'][0]
    plt_df['benchmark_ratio']=(bm_df['open']-bm_init)/bm_init

    plt_df[['ratio','benchmark_ratio']].plot()
    plt.show()
    print(plt_df['ratio'])
    print(plt_df)





def initialize(context):
    set_benchmark('601318')
    g.p1=5
    g.p2=10
    g.security='601318'


def handle_data(context):
    # order('601318',100)
    hist=attribute_history(g.security,g.p2)


    ma5=hist['close'][-g.p1:].mean()
    # print(ma5)
    ma60=hist['close'].mean()

    if ma5>ma60 and g.security not in context.positions:
        order_value(g.security,context.cash)
    elif ma5<ma60 and g.security in context.positions:
        order_target(g.security,0)
run()
# init(context)

# print(context.s1)
# print(init(context).s1)