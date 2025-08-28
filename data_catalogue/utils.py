import datetime

import pandas as pd
import sqlalchemy as sa
import os

from config.settings import (
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
)


engine = sa.create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def get_all_vehicles():
    sql_query = f"SELECT * FROM vehicle"

    try:
        vehicle_metadata = pd.read_sql(sql=sql_query, con=engine)
        existing_ids = vehicle_metadata["vehicle"].tolist()
    except Exception as e:
        existing_ids = [e]
    return existing_ids


def get_all_towers():
    sql_query = f"SELECT * FROM tower"

    try:
        tower_metadata = pd.read_sql(sql=sql_query, con=engine)
        existing_ids = tower_metadata["tower"].tolist()
    except Exception as e:
        existing_ids = [e]
    return existing_ids


def get_vehicle_charges(vehicle_id):
    sql_query = f"SELECT * FROM vehicle WHERE vehicle.vehicle={int(vehicle_id)}"

    try:
        vehicle_metadata = pd.read_sql(sql=sql_query, con=engine)
        existing_ids = vehicle_metadata["charge_id"].tolist()
    except Exception as e:
        existing_ids = [e]

    return existing_ids


def get_tower_charges(tower_id):
    sql_query = f"SELECT * FROM tower WHERE tower.tower={int(tower_id)}"

    try:
        tower_metadata = pd.read_sql(sql=sql_query, con=engine)
        existing_ids = tower_metadata["charge_id"].tolist()
    except Exception as e:
        existing_ids = [e]
    return existing_ids


def get_vehicle_charge_information(charge_id):
    sql_query = (
        f"""SELECT * FROM "vehicle_states" WHERE "vehicle_states".id={int(charge_id)}"""
    )

    try:
        charge_info = pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        charge_info = e
    return charge_info.to_dict(orient="records")


def get_tower_charge_information(charge_id):
    sql_query = (
        f"""SELECT * FROM "tower_states" WHERE "tower_states".id={int(charge_id)}"""
    )

    try:
        charge_info = pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        charge_info = e
    return charge_info.to_dict(orient="records")


def get_building_consumption(start_date:datetime.date, end_date:datetime.date):
    sql_query = (
        f"""SELECT timestamp, w4_building_consumption FROM w4_calc WHERE timestamp BETWEEN {start_date} and {end_date}"""
    )
    try:
        building_consumption = pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        building_consumption = e
    return building_consumption["w4_building_consumption"]


def get_energy_production(start_date:datetime.date, end_date:datetime.date):
    sql_query = (
        f"""SELECT timestamp, w4_production FROM w4_calc WHERE timestamp BETWEEN {start_date} and {end_date}"""
    )
    try:
        energy_production = pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        energy_production = e
    return energy_production["w4_production"]
