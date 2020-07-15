
import redis
import threading
import redisMQ
import json

# redis连接

def shengchan(body):
    redisMQ.re_queue.publish("liao", body)


def xioafei1():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('liao')  #从liao订阅消息
    for item in ps.listen():        #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            #print(item['channel'])  CORE   BACKEND
            print(item['data'])
            print('11')
def xioafei2():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('liao')  #从liao订阅消息
    for item in ps.listen():        #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            #print(item['channel'])  CORE   BACKEND
            print(item['data'])
            print('22')
t3 = threading.Thread(target=xioafei1,)
t3.start()
t4 = threading.Thread(target=xioafei2,)
t4.start()
