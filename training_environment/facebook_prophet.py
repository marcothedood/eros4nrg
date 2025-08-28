import pandas as pd
import matplotlib.pyplot as plt
import datetime
from prophet import Prophet
from dataset import TimeSeriesDataset
from data_pipeline import utils as dp_utils
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# -----------------------------------------------
# Forecast using Facebook Prophet
# -----------------------------------------------
if __name__ == '__main__':
    # Configuration
    table_name = "w4_calc"
    column_of_interest = "w4_building_consumption"
    split_date = datetime.date.today() - datetime.timedelta(days=7)  # like "2024-01-01"
    window_size = 700         # for the dataset class
    horizon_steps = 100       # number of to be forecasted

    # Create train/test datasets
    train_battery_dataset = TimeSeriesDataset(
        table_name=table_name,
        column_of_interest=column_of_interest,
        window_size=window_size,
        split_date=split_date,
        train_test_split=1,
        train_test='train',
        # normalize=True
    )
    # test_battery_dataset = TimeSeriesDataset(
    #     data_path=dataset_file,
    #     column_of_interest=column_of_interest,
    #     window_size=window_size,
    #     split_date=split_date,
    #     train_test_split=0.85,
    #     train_test='test',
    #     # normalize=True
    # )


    # Prepare the training data for Prophet
    if train_battery_dataset.normalize:
        train_series_original = train_battery_dataset.inverse_transform(train_battery_dataset.series)
    train_series_original = train_battery_dataset.series
    train_df = pd.DataFrame({
        "ds": train_battery_dataset.df_index,
        "y": train_series_original
    })

    # Fit the Prophet model with tuning
    # Tune changepoint_prior_scale and set seasonality_mode to multiplicative if needed.
    model = Prophet(changepoint_prior_scale=.1, seasonality_mode='additive')
    # If your data shows weekly seasonality, add it explicitly.
    model.add_seasonality(name='weekly', period=1.5, fourier_order=17)
    model.add_seasonality(name='daily', period=1, fourier_order=7)
    model.add_seasonality(name='hourly', period=.5, fourier_order=17)
    model.fit(train_df)

    # Create a future DataFrame for forecasting
    # freq = pd.infer_freq(train_df["ds"])
    # if freq is None:
    freq = "10min"
    future = model.make_future_dataframe(periods=horizon_steps, freq=freq)

    # Forecast
    forecast = model.predict(future)
    forecast_future = forecast.tail(horizon_steps)

    # Prepare the test actuals
    if train_battery_dataset.normalize:
        test_series_original = train_battery_dataset.inverse_transform(train_battery_dataset.series)
    else:
        test_series_original = train_battery_dataset.series

    forecast_df = pd.DataFrame()
    if not forecast_future.empty:
        forecast_df["timestamp"] = forecast_future["ds"]
        forecast_df["w4_building_consumption"] = forecast_future["yhat"]
        forecast_df["trend"] = forecast_future["trend"]
        forecast_df["daily"] = forecast_future["daily"]
        forecast_df["hourly"] = forecast_future["hourly"]
        forecast_df["weekly"] = forecast_future["weekly"]
        dp_utils.save_df_to_db(
            forecast_df,
            f"prophet_forecast_{column_of_interest}",
            if_exists="replace"
        )