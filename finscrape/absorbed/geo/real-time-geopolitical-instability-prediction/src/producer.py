import pandas as pd
from kafka import KafkaProducer
import json
import time
import numpy as np

# =====================================================
# LOAD FULL RAW DATASET
# =====================================================
df = pd.read_csv(
    r"C:\geopolitical instability\data\dataset\GDLET-DATASET.csv"
)

# =====================================================
# REPLACE NaN VALUES
# Kafka JSON cannot send NaN
# =====================================================
df = df.replace({np.nan: None})

# =====================================================
# KAFKA PRODUCER
# =====================================================
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("\n================================================")
print(" Producer started sending RAW data...")
print("================================================\n")

# =====================================================
# SEND FULL RAW ROWS
# =====================================================
for _, row in df.iterrows():

    raw_data = row.to_dict()

    producer.send(
        "geopolitics",
        value=raw_data
    )

    print("\n======================================")
    print("Sent RAW Data:")
    print(raw_data)
    print("======================================")

    # simulate realtime streaming
    time.sleep(2)

producer.close()