import redis

# redis连接
re_queue = redis.Redis(host='localhost', port=6379, decode_responses=True)
g_re_queue_pipe=re_queue.pipeline()
g_count=0
g_count_2=0
g_count_3=0
def production(msg):
    re_queue.publish("CORE", msg)

def productionStartCar(msg):
    # re_queue.publish("CARSTART", msg)
    global  g_re_queue_pipe
    global  g_count
    if g_count<99:
        g_re_queue_pipe.publish("CARSTART", msg)
        g_count=g_count+1
    else:
        g_re_queue_pipe.execute()
        g_count=0

def productionStopCar(msg):
    # re_queue.publish("CARSTOP", msg)
    global  g_re_queue_pipe
    global  g_count_2
    if g_count_2<99:
        g_re_queue_pipe.publish("CARSTOP", msg)
        g_count_2=g_count_2+1
    else:
        g_re_queue_pipe.execute()
        g_count_2=0
def productionMessage(msg):
    re_queue.publish("SENDMESS", msg)

def productionMail(msg):
    re_queue.publish("MAIL", msg)
