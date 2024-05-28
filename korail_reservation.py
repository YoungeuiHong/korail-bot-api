import sys
import time
from pydantic import BaseModel
from korail2 import Korail, AdultPassenger, TrainType, NoResultsError, KorailError
import os
from dotenv import load_dotenv

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

async def reserve_train(train: Train):
    k = Korail(KORAIL_ID, KORAIL_PW)
    if not k.login():
        print("login fail")
        exit(-1)
    while True:
        notFound = True
        while notFound:
            try:
                sys.stdout.write("Finding Seat %s ➜ %s              \r" % (train.departure, train.destination))
                sys.stdout.flush()
                trains = k.search_train_allday(train.departure, train.destination, train.date, train.time, passengers=PSGRS, train_type=TRAIN_TYPE)
                print(trains)
                print("Found!!")
                notFound = False
            except NoResultsError:
                sys.stdout.write("No Seats                               \r")
                sys.stdout.flush()
                time.sleep(2)
            except Exception as e:
                print(e)
                time.sleep(2)

        k.login()
        seat = None
        ok = False
        try:
            seat = k.reserve(trains[0], passengers=PSGRS)
            ok = True
        except KorailError as e:
            print(e)
            break

        if ok:
            print(seat)
            return seat
