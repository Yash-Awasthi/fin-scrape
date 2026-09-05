import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report,accuracy_score
from sklearn.metrics import confusion_matrix
from xgboost import plot_importance
import json
import time
import joblib

# Load the GDELT dataset from Google Drive
df = pd.read_csv("C:\geopolitical instability\data\dataset\GDLET-DATASET.csv")

# Drop actor-related columns that are not required for instability prediction
drop_cols = [

'Actor1Code','Actor1Name','Actor1KnownGroupCode',
'Actor1EthnicCode','Actor1Religion1Code','Actor1Religion2Code',
'Actor1Type2Code','Actor1Type3Code',

'Actor2Code','Actor2Name','Actor2KnownGroupCode',
'Actor2EthnicCode','Actor2Religion1Code','Actor2Religion2Code',
'Actor2Type2Code','Actor2Type3Code',

'ActionGeo_FullName'

]

df = df.drop(columns=drop_cols)

# Map country codes to broader geopolitical regions
def map_region(code):

    north_america = ['US','CA','MX']
    europe = ['FR','GM','UK','IT','SP','RS','UP','PL','HU','GR','RO','BG','NO','SW','FI','DA','NL','BE','LU','PO']
    middle_east = ['IR','IZ','SY','IS','SA','TU','JO','AE','QA','KU','YM']
    south_asia = ['IN','PK','BG','NP','CE','AF']
    east_asia = ['CH','JA','KS','TW','HK']
    southeast_asia = ['RP','TH','VM','MY','ID','SG','CB']
    africa = ['EG','KE','ZA','NI','NG','SU','TZ','UG','ET','GH','SN','ML','CM','BF','AO']
    latin_america = ['BR','AR','CH','PE','CO','VE','UY','BO','EC','GY']
    oceania = ['AU','NZ','FJ']

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
    
df['Region'] = df['ActionGeo_CountryCode'].apply(map_region)


# Fill missing values using appropriate statistical methods
df['GoldsteinScale'] = df['GoldsteinScale'].fillna(df['GoldsteinScale'].mean())

df['ActionGeo_Lat'] = df['ActionGeo_Lat'].fillna(df['ActionGeo_Lat'].mean())
df['ActionGeo_Long'] = df['ActionGeo_Long'].fillna(df['ActionGeo_Long'].mean())

df['ActionGeo_CountryCode'] = df['ActionGeo_CountryCode'].fillna(df['ActionGeo_CountryCode'].mode()[0])

# EventIntensity measures the overall media attention for an event
df['EventIntensity'] = df['NumMentions'] + df['NumArticles']

# Create instability labels based on GDELT QuadClass
# 0 = Stable events
# 1 = Verbal conflict
# 2 = Material conflict (high instability)
def create_target(row):

    if row["QuadClass"] == 4:
        return 2

    elif row["QuadClass"] == 3:
        return 1

    else:
        return 0


df["instability_label"] = df.apply(create_target, axis=1)

# Convert categorical region names into numeric values
encoder = LabelEncoder()

df['Region_encoded'] = encoder.fit_transform(df['Region'])

features = [
'AvgTone',
'GoldsteinScale',
'NumMentions',
'NumSources',
'NumArticles',
'EventIntensity',
'Region_encoded'
]

# Sort dataset by time
df = df.sort_values("SQLDATE")

# Split dataset (80 / 10 / 10)
train_size = int(len(df) * 0.8)
test_size = int(len(df) * 0.9)

train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:test_size]
stream_df = df.iloc[test_size:]

# Create train and test sets
X_train = train_df[features]
y_train = train_df['instability_label']

X_test = test_df[features]
y_test = test_df['instability_label']

X_test.to_csv("test_data.csv", index=False)

# Train XGBoost
# Train XGBoost classifier to predict geopolitical instability level

model = XGBClassifier(
    objective='multi:softmax',
    num_class=3,
    eval_metric='mlogloss',
    n_estimators=300,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8
)
#model training
model.fit(X_train, y_train)

# Evaluate model
pred = model.predict(X_test)

print(classification_report(y_test, pred))
print("Accuracy:", accuracy_score(y_test, pred))
print(confusion_matrix(y_test, pred))

# Save trained XGBoost model for later use in streaming prediction


joblib.dump(
    model,
    r"C:\geopolitical instability\model\xgboost_instability_model.pkl"
)

joblib.dump(
    encoder,
    r"C:\geopolitical instability\model\region_encoder.pkl"
)

goldstein_mean = df['GoldsteinScale'].mean()

joblib.dump(
    goldstein_mean,
    r"C:\geopolitical instability\model\goldstein_mean.pkl"
)