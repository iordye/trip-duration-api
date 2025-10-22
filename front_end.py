import streamlit as st 
import pandas as pd 
from datetime import datetime
import requests


API_URL = 'https://the-trip-predictor.onrender.com/predict'



st.title("NYC Taxi Trip Duration Prediction")
st.write("Fill in the details below to predict your trip duration")

# === Basic trip details ===
vendor_id = st.selectbox("Vendor ID", [1, 2])
store_and_fwd_flag = st.selectbox("Store and Forward Flag", ["Y", "N"])
rate_code = st.selectbox("Rate Code ID", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
passenger_count = st.selectbox("Passenger Count", [1, 2, 3, 4, 5, 6])
trip_distance = st.number_input("Trip Distance (miles)", min_value=0.0, step=0.1)

# === Location info ===
pu_location = st.number_input("Pickup Location ID", min_value=1, value=74)
do_location = st.number_input("Dropoff Location ID", min_value=1, value=168)

# === Datetime inputs ===
pickup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
dropoff_time = pickup_time

# === Fare details ===
fare_amount = st.number_input("Fare Amount ($)", min_value=0.0, step=0.5, value=6.0)
extra = st.number_input("Extra Charges ($)", min_value=0.0, step=0.1, value=0.5)
mta_tax = st.number_input("MTA Tax ($)", min_value=0.0, step=0.1, value=0.5)
tip_amount = st.number_input("Tip Amount ($)", min_value=0.0, step=0.5, value=0.0)
tolls_amount = st.number_input("Tolls Amount ($)", min_value=0.0, step=0.5, value=0.0)
ehail_fee = st.number_input("Ehail Fee ($)", min_value=0.0, step=0.1, value=0.0)
improvement_surcharge = st.number_input("Improvement Surcharge ($)", min_value=0.0, step=0.1, value=0.3)

# === Trip type info ===
payment_type = st.selectbox("Payment Type", [1, 2, 3, 4, 5])
trip_type = st.selectbox("Trip Type", [1, 2])
congestion_surcharge = st.number_input("Congestion Surcharge ($)", min_value=0.0, step=0.1, value=0.0)

total_amount = (
    fare_amount
    + extra
    + mta_tax
    + tip_amount
    + tolls_amount
    + ehail_fee
    + improvement_surcharge
    + congestion_surcharge
)

st.number_input("💰 Total Amount($):", value=total_amount, disabled=True)

input_data = { "data": [{
    "VendorID": vendor_id,
    "lpep_pickup_datetime": pickup_time,
    "lpep_dropoff_datetime": dropoff_time,
    "store_and_fwd_flag": store_and_fwd_flag,
    "RatecodeID": rate_code,
    "PULocationID": pu_location,
    "DOLocationID": do_location,
    "passenger_count": passenger_count,
    "trip_distance": trip_distance,
    "fare_amount": fare_amount,
    "extra": extra,
    "mta_tax": mta_tax,
    "tip_amount": tip_amount,
    "tolls_amount": tolls_amount,
    "ehail_fee": ehail_fee,
    "improvement_surcharge": improvement_surcharge,
    "total_amount": total_amount,
    "payment_type": payment_type,
    "trip_type": trip_type,
    "congestion_surcharge": congestion_surcharge
}]}


# ==========================
# Predict Button
# ==========================
if st.button("Predict Trip Duration 🚖"):
    try:
        response = requests.post(API_URL, json=input_data)
        response.raise_for_status()
        prediction = response.json()["predicted_trip_duration_minutes"][0]
        st.success(f"⏱ Estimated Trip Duration: {prediction:.2f} minutes")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
    except KeyError:
        st.error("Unexpected response from API. Check your backend.")

# ==========================
# Preview Input Data (Optional)
# ==========================
#st.write("### Preview of Input Data Sent to API")
#st.json(input_data)
