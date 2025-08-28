import datetime

import data_catalogue.utils as dc_util

from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from keycloak import KeycloakOpenID

app = FastAPI()

keycloak_openid = KeycloakOpenID(
    server_url="https://keycloak.nemo.onelab.eu",
    client_id="admin@eros4nrg.com",
    realm_name="Eros4NRG",
    client_secret_key="aesh3cheiroMah6t",
    # server_url="http://localhost:8080",
    # client_id="pythontest",
    # realm_name="test1",
    # client_secret_key="NYIbJIZ4MLNRWrVloGZdg0Rz1sdOuqhr",
)
bearer_scheme = HTTPBearer()


@app.post("/token")
async def login(username: str, password: str):
    """
    Login function using keycloak as security
    """
    token = keycloak_openid.token(username, password)
    return token["access_token"]


@app.get("/vehicles")
async def get_vehicles():
    return dc_util.get_all_vehicles()


@app.get("/vehicles/{vehicle_id}/charges")
async def get_vehicle_charges(vehicle_id: str, token=Depends(bearer_scheme)):
    return dc_util.get_vehicle_charges(vehicle_id)


@app.get("/vehicle-charges/{charge_id}")
async def get_vehicle_charge_infos(charge_id: str, token=Depends(bearer_scheme)):
    return dc_util.get_vehicle_charge_information(charge_id)


@app.get("/towers")
async def get_towers():
    return dc_util.get_all_towers()


@app.get("/towers/{tower_id}/charges")
async def get_tower_charges(tower_id: str, token=Depends(bearer_scheme)):
    return dc_util.get_tower_charges(tower_id)


@app.get("/tower-charges/{charge_id}")
async def get_tower_charge_infos(charge_id: str, token=Depends(bearer_scheme)):
    return dc_util.get_tower_charge_information(charge_id)


@app.get("building_consumption/")
async def get_building_consumption(start_date: datetime.date, end_date:datetime.date, token=Depends(bearer_scheme)):
    return dc_util.get_building_consumption(start_date=start_date, end_date=end_date)


@app.get("energy_production/")
async def get_energy_production(start_date: datetime.date, end_date:datetime.date, token=Depends(bearer_scheme)):
    return dc_util.get_energy_production(start_date=start_date, end_date=end_date)
