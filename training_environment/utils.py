import datetime
import numpy as np
import pickle
import pandas as pd

from data_pipeline import utils as dp_utils
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from scipy.signal import butter, filtfilt


def train_detector(df, column_names):
    model = IsolationForest(
        n_estimators=50, max_samples="auto", contamination=float(0.1), max_features=1.0
    )
    model.fit(df[column_names])
    df["scores"] = model.decision_function(df[column_names])
    df["anomaly"] = model.predict(df[column_names])
    df = df.loc[df["anomaly"] == 1]
    return df


def get_vehicle_ids():
    db_output = dp_utils.get_table(columns=["vehicle"], table_name="vehicle")
    if db_output.empty:
        Exception(
            "No vehicle ids found in the database. Please check the vehicle table."
        )
    print(f"{db_output.shape[0]} vehicle ids found in the database.")
    return db_output["vehicle"].values


def butter_lowpass_filter(data, cutoff, fs, order, column_name):
    result_df = pd.DataFrame()
    normal_cutoff = cutoff / 0.5 * fs
    # Get the filter coefficients
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    filtered_data = filtfilt(b, a, data[column_name])
    result_df[column_name] = filtered_data
    return result_df.set_index(data.index)


def get_prepped_vehicle_data_autoreg(vehicle=1, vehicle_columns="battery_percentage"):
    vehicle_data = dp_utils.get_table(
        columns=[vehicle_columns, "timestamp"],
        table_name="vehicle_states",
        clause=f"WHERE vehicle={vehicle}",
    )
    sorted_vd = vehicle_data.sort_values(by=["timestamp"])
    sorted_vd.set_index("timestamp", inplace=True)
    return sorted_vd


def get_w4_calc_data(column_name):
    w4_calc_data = dp_utils.get_table(
        columns=[column_name, "timestamp"], table_name="w4_calc"
    ).drop_duplicates(subset=["timestamp"], keep="first")
    w4_calc_data.set_index("timestamp", inplace=True)
    return w4_calc_data


def get_asm_6_to_6_timestamp(last_timestamp):
    if last_timestamp.hour < 6:
        dt6 = datetime.datetime(last_timestamp.year,last_timestamp.month,last_timestamp.day,5,0,0,0)
    else:
        tomorrow = last_timestamp + datetime.timedelta(days=1)
        dt6 = datetime.datetime(tomorrow.year,tomorrow.month,tomorrow.day,5,0,0,0)
    return dt6


def check_retrain_model(script_start_date, current_date):
    # check if model is over a week old
    retrain_model = False
    if current_date > script_start_date + datetime.timedelta(days=7):
        script_start_date = current_date
        retrain_model = True

    return retrain_model, script_start_date


def train_predictions(model, model_filename, current_data, column_name, retrain_model):
    lag_step = 1
    max_lag = 1500
    print(f"Len of current data: {len(current_data)}")
    if len(current_data) < max_lag:
        print(f"Not enough data to train model {model_filename} for column {column_name}.")
        return model, 0, []

    for i in range(1, (max_lag * lag_step) + 1, lag_step):
        current_data[f"{column_name}_lag_{i}"] = current_data[column_name].shift(i)

    print(f"null values in current_data: {current_data.isnull().sum()}")
    print(f"current data example:\n{current_data.head()}")
    current_data.dropna(inplace=True)

    if current_data.empty:
        print(f"No data available to train model {model_filename} for column {column_name}.")
        return model, 0, []

    print(f"Training model {model_filename} for column {column_name} with data size: {len(current_data)}")
    train_size = int(0.8 * len(current_data))
    train_data = current_data.iloc[:train_size]
    test_data = current_data.iloc[train_size:]

    x_train = train_data.drop(columns=[column_name])
    y_train = train_data[column_name]

    x_test = test_data.drop(columns=[column_name])
    y_test = test_data[column_name]
    print(f"Training data size: {x_train.shape}, Test data size: {x_test.shape}")

    try:
        trained_model = pickle.load(open("training_environment/models/" + model_filename + ".pkl", "rb"))
    except (OSError, IOError) as e:
        model.fit(x_train, y_train)
        pickle.dump(model, open("training_environment/models/" + model_filename + ".pkl", "wb"))
    else:
        if retrain_model:
            print(f"Retraining model {model_filename} for column {column_name}.")
            model.fit(x_train, y_train)
            pickle.dump(model, open(model_filename + ".pkl", "wb"))
        else:
            model = trained_model

    return model, int(max_lag), x_test


def forecast(model, data, data_name, last_data_timestamp, forecast_step, freq):
    pred_result = {}
    future_forecasts = []
    data = data.iloc[-1].copy()
    for step in range(forecast_step):
        forecasted_data = model.predict([data])[0]
        future_forecasts.append(forecasted_data)
        data = np.concatenate(([forecasted_data], data[:-1]))

    future_timestamps = pd.date_range(
        start=last_data_timestamp, periods=forecast_step + 1, freq=freq
    )[1:]

    pred_result[data_name] = future_forecasts
    pred_result["timestamp"] = future_timestamps

    return pd.DataFrame(pred_result)
