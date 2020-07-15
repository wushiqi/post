import pika


class RabbitMQ(object):
    def __init__(self, host, port, username, password, vhost):
        self._host = host  # broker IP
        self._port = port  # broker port
        self._vhost = vhost  # vhost
        self._credentials = pika.PlainCredentials(username, password)
        self._connection = None

    def connect(self):
        # 连接RabbitMQ的参数对象
        parameter = pika.ConnectionParameters(self._host, self._port, self._vhost,
                                              self._credentials,heartbeat=0)
        self._connection = pika.BlockingConnection(parameter)  # 建立连接

    def put(self, message_str, queue_name, route_key, exchange=''):
        if self._connection is None:
            return

        channel = self._connection.channel()      # 获取channel
        #channel.queue_declare(queue=queue_name)
        channel.queue_declare(queue=queue_name,durable='false', arguments={'x-message-ttl': 1000,'x-max-length': 100})# 申明使用的queue
        #  调用basic_publish方法向RabbitMQ发送数据， 这个方法应该只支持str类型的数据
        channel.basic_publish(
            exchange=exchange,  # 指定exchange
            routing_key=route_key,  # 指定路由
            body=message_str      # 具体发送的数据
        )
    '''
    def getting_start(self, queue_name):
        if self._connection is None:
            return
        channel = self._connection.channel()
        channel.queue_declare(queue=queue_name)

        # 调用basic_consume方法，可以传入一个回调函数
        channel.basic_consume(self.callback,
                              queue=queue_name,
                              no_ack=True)
        channel.start_consuming()   # 相当于run_forever(), 当Queue中没有数据，则一直阻塞等待

    @staticmethod
    def callback(ch, method, properties, message_str):
        """定义一个回调函数"""
        print "[x] Received {0}".format(message_str)
    '''
    def close(self):
        """关闭RabbitMQ的连接"""
        if self._connection is not None:
            self._connection.close()