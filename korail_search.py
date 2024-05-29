import os

from dotenv import load_dotenv
from korail2 import Korail, AdultPassenger, TrainType
from pydantic import BaseModel

load_dotenv()

KORAIL_ID = os.getenv("KORAIL_ID")
KORAIL_PW = os.getenv("KORAIL_PW")
PSGRS = [AdultPassenger(1)]
TRAIN_TYPE = TrainType.KTX

class Train(BaseModel):
    departure: str
    destination: str
    date: str
    time: str

async def search_train(train: Train):
    k = Korail(KORAIL_ID, KORAIL_PW)
    if not k.login():
        print("login fail")
        exit(-1)
    trains = k.search_train(train.departure, train.destination, train.date, train.time, passengers=PSGRS, train_type=TRAIN_TYPE)
    return trains
