import pandas as pd
import sqlalchemy as sa
import datetime

from data_pipeline import utils as dp_utils
from training_environment import utils as te_utils
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn import tree, linear_model
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from xgboost import XGBRegressor

models = {
    "cat": CatBoostRegressor(
        iterations=10, depth=10, learning_rate=0.8, loss_function="RMSE"
    ),
    # "xgb": XGBRegressor(
    #     n_estimators=100,
    #     max_depth=15,  # Maximum depth of each tree
    #     learning_rate=0.3,  # Step size shrinkage for each update
    #     subsample=0.8,  # Fraction of samples used for each tree
    #     colsample_bytree=0.8,  # Fraction of features used for each tree
    #     random_state=42,
    # ),
    # "lgb": LGBMRegressor(
    #     n_estimators=100,
    #     max_depth=15,  # Maximum depth of each tree
    #     learning_rate=0.5,  # Step size shrinkage for each update
    #     subsample=0.8,  # Fraction of samples used for each tree
    #     colsample_bytree=0.8,  # Fraction of features used for each tree
    #     random_state=42,
    # ),
    # "dt": tree.DecisionTreeRegressor(),
    # "lasso": linear_model.Lasso(alpha=0.1),
    # "rfr": RandomForestRegressor(max_depth=15, n_estimators=100, random_state=42),
}


def train_vehicle(retrain_model):
    model_header = "emotion"
    column_names = ["battery_percentage"]

    for model_name, model in models.items():
        for column_name in column_names:
            all_pred_res = pd.DataFrame()
            for vehicle_id in te_utils.get_vehicle_ids():
                model_filename = (
                    model_header
                    + "_"
                    + model_name
                    + "_"
                    + column_name
                    + "_"
                    + str(vehicle_id)
                )
                vehicle_data = te_utils.get_prepped_vehicle_data_autoreg(
                    vehicle=vehicle_id
                )
                # use 1-week data for training
                last_timestamp = vehicle_data.index[-1]
                start_timestamp = last_timestamp - datetime.timedelta(days=1)
                training_data = vehicle_data.loc[start_timestamp:]

                trained_model, max_size, x_test = te_utils.train_predictions(
                    model, model_filename, training_data, column_name, retrain_model
                )
                # filtered_lowpass_vd = te_utils.butter_lowpass_filter(vehicle_data, 2, 0.05, 2, column_name)
                if max_size == 0 and not x_test:
                    continue
                max_prediction = datetime.timedelta(days=1)
                freq = datetime.timedelta(minutes=10)
                forecast_step = int(max_prediction / freq)
                pred_result = te_utils.forecast(
                    trained_model,
                    x_test,
                    column_name,
                    last_timestamp,
                    forecast_step,
                    freq,
                )
                pred_result = pred_result.assign(vehicle=vehicle_id)
                if all_pred_res.empty:
                    all_pred_res = pred_result
                else:
                    all_pred_res = pd.concat([all_pred_res, pred_result])

            dp_utils.save_df_to_db(
                all_pred_res,
                f"predicted_{column_name}_{model_name}",
                "replace",
                dtype={
                    "timestamp": sa.types.TIMESTAMP,
                },
            )


def train_asm_terni(retrain_model):
    model_header = "asm"
    column_names = ["w4_building_consumption", "w4_production"]

    for model_name, model in models.items():
        for column_name in column_names:
            all_pred_res = pd.DataFrame()
            w4_calc_data = te_utils.get_w4_calc_data(column_name=column_name)
            # use 1-week data for training
            last_timestamp = w4_calc_data.index[-1]
            start_timestamp = last_timestamp - datetime.timedelta(days=5)
            training_data = w4_calc_data.loc[start_timestamp:]

            model_filename = model_header + "_" + model_name + "_" + column_name
            trained_model, max_size, x_test = te_utils.train_predictions(
                model, model_filename, training_data, column_name, retrain_model
            )
            if max_size == 0 and not x_test:
                continue

            max_prediction = datetime.timedelta(days=1)
            freq = datetime.timedelta(seconds=5)
            forecast_step = int(max_prediction / freq)
            dt6 = te_utils.get_asm_6_to_6_timestamp(last_timestamp)
            pred_result = te_utils.forecast(
                trained_model,
                x_test,
                column_name,
                dt6,
                forecast_step,
                freq,
            )
            if all_pred_res.empty:
                all_pred_res = pred_result
            else:
                all_pred_res = pd.concat([all_pred_res, pred_result])

            dp_utils.save_df_to_db(
                all_pred_res,
                f"predicted_{column_name}_{model_name}",
                "replace",
                dtype={
                    "timestamp": sa.types.TIMESTAMP,
                },
            )


def start_training():
    script_start_date = datetime.date.today()
    while True:
        current_date = datetime.date.today()
        retrain_model, script_new_date = te_utils.check_retrain_model(
            script_start_date, current_date
        )
        if script_new_date != script_start_date:
            script_start_date = script_new_date

        train_asm_terni(retrain_model)
        train_vehicle(retrain_model)


if __name__ == "__main__":
    start_training()
