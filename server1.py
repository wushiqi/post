import redis
import json
import copy

g_command={"com":""}
# redis连接
re_queue = redis.Redis(host='172.17.19.103', port=6379 )

def production(msg):
    re_queue.publish("liao", msg)

ps = re_queue.pubsub()
ps.subscribe('liao')  #从liao订阅消息
for item in ps.listen():        #监听状态：有消息发布了就拿过来
    if item['type'] == 'message':
        print(item['channel'])
        print(item['data'])