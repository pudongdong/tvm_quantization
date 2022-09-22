from kafka import KafkaProducer
import datetime
import time
from kafka import KafkaConsumer


producer = KafkaProducer(bootstrap_servers=['brokers'])

for i in range(100):
    # data = {'num': i, 'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    producer.send('topic', b'{"test_msg":"hello world"}')
    time.sleep(1)
    print(i)
