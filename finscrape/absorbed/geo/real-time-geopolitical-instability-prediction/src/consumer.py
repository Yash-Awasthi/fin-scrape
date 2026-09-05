from pyspark.sql import SparkSession
import json
import joblib
import pandas as pd
from datetime import datetime
import logging

# HIDE SPARK WARNINGS
logging.getLogger("py4j").setLevel(logging.ERROR)
logging.getLogger("org").setLevel(logging.ERROR)

# =========================================================
# LOAD TRAINED MODEL
# =========================================================
model = joblib.load(
    r"C:\geopolitical instability\model\xgboost_instability_model.pkl"
)
# Load SAME encoder used during training
encoder = joblib.load(
    r"C:\geopolitical instability\model\region_encoder.pkl"
)
# Load SAME mean used during training
goldstein_mean = joblib.load(
    r"C:\geopolitical instability\model\goldstein_mean.pkl"
)
# =========================================================
# CREATE SPARK SESSION
# =========================================================
# spark = SparkSession.builder \
#     .appName("GeoPrediction") \
#     .getOrCreate()

from pyspark.sql import SparkSession
import os

os.environ["HADOOP_HOME"] = "C:\\hadoop"

spark = SparkSession.builder \
    .appName("GeoPoliticalConsumer") \
    .master("local[*]") \
    .config("spark.sql.streaming.checkpointLocation", "file:///C:/tmp/spark-checkpoints") \
    .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
    .config("spark.hadoop.fs.AbstractFileSystem.file.impl", "org.apache.hadoop.fs.local.LocalFs") \
    .config("spark.hadoop.hadoop.native.lib", "false") \
    .config("spark.driver.extraJavaOptions", "-Dhadoop.home.dir=C:\\hadoop") \
    .config("spark.executor.extraJavaOptions", "-Dhadoop.home.dir=C:\\hadoop") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

spark.sparkContext.setLogLevel("ERROR")

print("\n==================================================")
print(" Consumer is READY and waiting for Kafka data...")
print("==================================================\n")

# =========================================================
# READ STREAM FROM KAFKA
# =========================================================
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "geopolitics") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .option("minPartitions", 1) \
    .option("maxOffsetsPerTrigger", 1) \
    .load()

# Convert Kafka value to STRING
df = df.selectExpr("CAST(value AS STRING)")

# =========================================================
# SAME REGION MAPPING USED IN TRAINING
# =========================================================
def map_region(code):

    north_america = ['US','CA','MX']

    europe = [
        'FR','GM','UK','IT','SP','RS','UP',
        'PL','HU','GR','RO','BG','NO','SW',
        'FI','DA','NL','BE','LU','PO'
    ]

    middle_east = [
        'IR','IZ','SY','IS','SA','TU',
        'JO','AE','QA','KU','YM'
    ]

    south_asia = [
        'IN','PK','BG','NP','CE','AF'
    ]

    east_asia = [
        'CH','JA','KS','TW','HK'
    ]

    southeast_asia = [
        'RP','TH','VM','MY','ID','SG','CB'
    ]

    africa = [
        'EG','KE','ZA','NI','NG','SU','TZ',
        'UG','ET','GH','SN','ML','CM','BF','AO'
    ]

    latin_america = [
        'BR','AR','CH','PE','CO',
        'VE','UY','BO','EC','GY'
    ]

    oceania = [
        'AU','NZ','FJ'
    ]

    if code in north_america:
        return 'North America'

    elif code in europe:
        return 'Europe'

    elif code in middle_east:
        return 'Middle East'

    elif code in south_asia:
        return 'South Asia'

    elif code in east_asia:
        return 'East Asia'

    elif code in southeast_asia:
        return 'Southeast Asia'

    elif code in africa:
        return 'Africa'

    elif code in latin_america:
        return 'Latin America'

    elif code in oceania:
        return 'Oceania'

    else:
        return 'Unknown'
    

# =========================================================
# PROCESS EACH BATCH
# =========================================================
def process_batch(batch_df, batch_id):

    # Convert Spark DF -> Pandas
    data = batch_df.toPandas()

    if len(data) == 0:
        return

    # Convert JSON string -> dataframe
    data = data['value'].apply(json.loads).apply(pd.Series)

    # =====================================================
    # ENSURE REQUIRED COLUMNS EXIST
    # =====================================================

    required_cols = [
        'AvgTone',
        'GoldsteinScale',
        'NumMentions',
        'NumSources',
        'NumArticles',
        'ActionGeo_CountryCode',
        'QuadClass'
    ]

    for col in required_cols:
        if col not in data.columns:
            data[col] = None

    # =====================================================
    # SAME PREPROCESSING AS TRAINING
    # =====================================================

    # Fill missing values
    data['GoldsteinScale'] = data['GoldsteinScale'].fillna(goldstein_mean)

    # Fill missing country
    data['ActionGeo_CountryCode'] = data[
        'ActionGeo_CountryCode'
    ].fillna('Unknown')

    # Feature engineering
    data['EventIntensity'] = (
        data['NumMentions'] +
        data['NumArticles']
    )

    # Region mapping
    data['Region'] = data[
        'ActionGeo_CountryCode'
    ].apply(map_region)

    # SAME encoder as training
    valid_classes = set(encoder.classes_)

    data['Region'] = data['Region'].apply(
        lambda x: x if x in valid_classes else 'Unknown'
    )

    data['Region_encoded'] = encoder.transform(data['Region'])

    # =====================================================
    # FEATURES
    # =====================================================
    features = [
        'AvgTone',
        'GoldsteinScale',
        'NumMentions',
        'NumSources',
        'NumArticles',
        'EventIntensity',
        'Region_encoded'
    ]

    X = data[features]

    # =====================================================
    # PREDICTION
    # =====================================================
    preds = model.predict(X)

    # =====================================================
    # PRINT RESULTS
    # =====================================================
    for i in range(len(X)):

        row = data.iloc[i]
        pred = preds[i]

        # Label mapping
        if pred == 2:
            label = "HIGH INSTABILITY"

        elif pred == 1:
            label = "VERBAL CONFLICT"

        else:
            label = "STABLE"

        print("\n" + "="*60)

        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

        print("\nIncoming Raw Data:")

        print(f"CountryCode     : {row['ActionGeo_CountryCode']}")
        print(f"AvgTone         : {row['AvgTone']}")
        print(f"GoldsteinScale  : {row['GoldsteinScale']}")
        print(f"NumMentions     : {row['NumMentions']}")
        print(f"NumSources      : {row['NumSources']}")
        print(f"NumArticles     : {row['NumArticles']}")

        print("\nProcessed Features:")

        print(f"Region           : {row['Region']}")
        print(f"Region_encoded   : {row['Region_encoded']}")
        print(f"EventIntensity   : {row['EventIntensity']}")

        print("\nPrediction Result:")

        print(f" {label}")

        print("="*60)

# =========================================================
# START STREAMING
# =========================================================
query = df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .trigger(processingTime='1 second') \
    .option("checkpointLocation", "file:///C:/tmp/spark-checkpoints") \
    .start()

query.awaitTermination()