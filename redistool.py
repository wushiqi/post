import redis
import json
redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)  # , password='123456'

def redis_set(key,val):
    data = {
        'foo': 'bar',
        'answer': 42,
        'arr': [None, True, 3.1444],
        'truth': {
            'coord': 'out there'
        }}
    redis_conn.execute_command('JSON.SET', 'doc1', '.', json.dumps(data))
    reply = json.loads(redis_conn.execute_command('JSON.GET', 'doc1','.foo'))
    print(str(reply))
def redis_get(com,key,path,val):
    reply = json.loads(redis_conn.execute_command('JSON.GET', 'doc1','.foo'))
    print(str(reply))
    return reply

def set(key,value):
    redis_conn.set(key, value)

def get(key):
    return redis_conn.get(key)

def hset(name,key,value):
    redis_conn.hset(name, key, value)

def hmset(name,keyvalues):
    redis_conn.hmset(name, keyvalues)

def hget(name, key):
    return redis_conn.hget(name, key)

def hgetall(name):
    return redis_conn.hgetall(name)

def exists(key):
    return redis_conn.exists(key)

def redis_del(key):
    return redis_conn.delete(key)

def hexists(name, key):
    return redis_conn.hexists(name, key)

def hdelete(name, key):
    return redis_conn.hdel(name,key)

def hkeys(key):
    return redis_conn.hkeys(key)

def hvals(name):
    return redis_conn.hvals(name)

def hkeys(name):
    return redis_conn.hkeys(name)
