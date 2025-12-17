import pulsar

client = pulsar.Client("pulsar://192.168.178.51/:6650")

producer = client.create_producer("my-topic")

for i in range(10):
    producer.send(("Hello-%d" % i).encode("utf-8"))

client.close()
