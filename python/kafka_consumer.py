from kafka import KafkaConsumer

# dp_item_hotel_processed_info_staging_hotel_sku
consumer = KafkaConsumer('topic', group_id='group_name',
                         bootstrap_servers=['broker1', 'broker2', 'broke3'])
for msg in consumer:
    print(msg)
