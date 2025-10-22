from fastapi import FastAPI
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import os
import great_expectations as gx


# ===============================
# 1️⃣ Load trained model
# ===============================
model = joblib.load(os.path.join(os.path.dirname(__file__), "model.pkl"))

app = FastAPI(title="NYC Taxi Trip Duration Prediction API")

# ===============================
# 2️⃣ Define input columns
# ===============================
columns = [
    'VendorID', 'lpep_pickup_datetime', 'lpep_dropoff_datetime',
    'store_and_fwd_flag', 'RatecodeID', 'PULocationID', 'DOLocationID',
    'passenger_count', 'trip_distance', 'fare_amount', 'extra', 'mta_tax',
    'tip_amount', 'tolls_amount', 'ehail_fee', 'improvement_surcharge',
    'total_amount', 'payment_type', 'trip_type', 'congestion_surcharge'
]

# ===============================
# 3️⃣ Home route
# ===============================
@app.get('/')
def home():
    """
    Returns a welcome message
    """
    return {"message": "🚕 Welcome to the NYC Taxi Trip Duration Prediction API!"}

#================================
#4️⃣ Data validation
#================================

def validate_input_data(df):

    """
    Validate incoming API request data using Great Expectations
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        bool: True if validation passes
        
    Raises:
        ValueError: If validation fails
    """

    #get the ephemeral Data context
    context = gx.get_context()
    data_source = context.data_sources.add_pandas(name = "trip_data")

    data_asset = data_source.add_dataframe_asset(name = "trip_data_asset")
    # Define the Batch Definition name
    batch_definition_name = "trip_data_batch"
    # Add the Batch Definition
    batch_definition = data_asset.add_batch_definition_whole_dataframe(batch_definition_name)
    

    # Define the Batch Parameters
    batch_parameters = {"dataframe": df}
    # Retrieve the Batch
    batch = batch_definition.get_batch(batch_parameters=batch_parameters)


    # Create an Expectation Suite
    expectation_suite_name = "trip_suite"
    suite = gx.ExpectationSuite(name=expectation_suite_name)

    # Add expectations

    # No NULLs in any column
    null_expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        for col in columns
    ]

    # Add all expectations to the suite
    for expectation in null_expectations:
        suite.add_expectation(expectation)

    # a Definite set of values for the store_and_fwd_flag
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="store_and_fwd_flag",
            value_set=["Y", "N"]        
        )
    )

    # Structural expectation
    suite.add_expectation(
        gx.expectations.ExpectTableColumnsToMatchOrderedList(
            column_list=columns
        )
    )

    # Add the Expectation Suite to the Context
    context.suites.add(suite)

    # Validate the Data Against the Suite
    validation_results = batch.validate(suite)
    # Evaluate the Results

    if not validation_results.success:
        # Extract detailed failure information
        failed_expectations = [
            exp for exp in validation_results.results 
            if not exp.success
        ]
        raise ValueError(
            f"Data validation failed. "
            f"{len(failed_expectations)} expectation(s) failed: "
            f"{failed_expectations}"
        )

    return True

# ===============================
# 5️⃣ Feature engineering
# ===============================
def feature_extraction(df):
    """
    Carries out feature extraction on a dataset  

    Parameters:
    ----------
    df: DataFrame
        A dataframe containing atleast a row and column.
    
    Return:
    ------
    DataFrame: Returns a dataframe containing
    new features.

    """
    df['pickup_year'] = df['lpep_pickup_datetime'].dt.year
    df['pickup_month'] = df['lpep_pickup_datetime'].dt.month
    df['pickup_dayofweek'] = df['lpep_pickup_datetime'].dt.dayofweek
    df['pickup_day'] = df['lpep_pickup_datetime'].dt.day
    df['pickup_hour'] = df['lpep_pickup_datetime'].dt.hour
    df['pickup_minute'] = df['lpep_pickup_datetime'].dt.minute
    df['pickup_second'] = df['lpep_pickup_datetime'].dt.second

    # Drop unnecessary columns
    df.drop(['ehail_fee', 'VendorID', 'lpep_pickup_datetime', 'lpep_dropoff_datetime'], axis=1, inplace=True)
    return df

# ===============================
# 6️⃣ Preprocessing
# ===============================
def preprocess(df):

    """
    Returns a standardized and encoded dataset for Numerical and categorical data in the datset

    Parameters:
    ----------
    df: DataFrame
        A dataframe containing atleast a row and column.
    
    Returns:
    --------
    numpy.ndarray

    """
    numerical = [
        'RatecodeID', 'PULocationID', 'DOLocationID',
        'passenger_count', 'trip_distance', 'fare_amount', 'extra', 'mta_tax',
        'tip_amount', 'tolls_amount', 'improvement_surcharge', 'total_amount',
        'payment_type', 'trip_type', 'congestion_surcharge',
        'pickup_year', 'pickup_month', 'pickup_dayofweek', 'pickup_day',
        'pickup_hour', 'pickup_minute', 'pickup_second'
    ]

    categorical = ['store_and_fwd_flag']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical),
            ('cat', OneHotEncoder(sparse_output=False), categorical)
        ]
    )

    # Apply transformations
    X = df[numerical + categorical]
    X_processed = preprocessor.fit_transform(X).astype('float32')
    return X_processed

# ===============================
# 7️⃣ Prediction endpoint
# ===============================
@app.post('/predict')
def predict(data: dict):

    """
    Predicts the Trip duration from a given set of features

    Parameters:
    ----------
    data {dict}: a dictionary containing right features

    Returns:
    -------

    a dictionary of the predicted trip duration in minutes
    """
    # Convert incoming JSON to DataFrame
    df = pd.DataFrame(data["data"], columns=columns)

     # Validate input data
    validate_input_data(df)

    # Convert date columns to datetime
    for col in ['lpep_pickup_datetime', 'lpep_dropoff_datetime']:
        df[col] = pd.to_datetime(df[col])

    # Feature extraction
    df = feature_extraction(df)

    # Preprocessing
    X_processed = preprocess(df)

    # Make prediction
    preds = model.predict(X_processed)

    # Return prediction
    return {"predicted_trip_duration_minutes": preds.tolist()}
