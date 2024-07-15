"""main function to run autoflow controller"""

from datetime import datetime
from pathlib import Path
import json

import numpy as np
from havc_algorithm.data import StationData
from havc_algorithm.optimizer import Optimizer
from havc_algorithm.base import BaseConnector
from havc_algorithm.connector import (
    APIConnector,
    BackplaneConnector,
    EthernetConnector,
    VirtualConnector,
)

# from havc_algorithm.table import SQLModel, data2table


with open(
    Path(__file__).resolve().parents[0] / "config.json", "r", encoding="utf-8"
) as f:
    config = json.load(f)

PATH = config["PATH"]
SAMPLE_TIME = config["SAMPLE_TIME"]
MODE = config["MODE"]
connector: BaseConnector

match MODE:
    case "back":
        connector = BackplaneConnector(
            sample_time=SAMPLE_TIME,
            path=PATH,
        )
    case "virtual":
        from sqlmodel import Session, create_engine

        connector = VirtualConnector(
            sample_time=SAMPLE_TIME,
            path=PATH,
        )
        COUNTER = 0

        END_COUNT = 4320

        SQLITE_FILE_NAME = config["SQLITE_FILE_NAME"]
        sqlite_url = f"sqlite:///{SQLITE_FILE_NAME}"

        engine = create_engine(sqlite_url, echo=False)

        def create_db_and_tables():
            """Create database and tables from metadata."""
            # SQLModel.metadata.create_all(engine)

        # def save_to_sql(station: StationData, control: ControlData):
            """Save data to SQL.

            Parameters
            ----------
            station_data : StationData
                Data of pump station measurements.
            control_data : ControlData
                Data of control signals.
            """
        #     station_table, pump_table_list = data2table(
        #         station, control, n_pumps=N_PUMPS
        #     )
        #     with Session(engine) as session:
        #         session.add(station_table)

        #         for k in range(N_PUMPS):
        #             session.add(pump_table_list[k])

        #         session.commit()

        # create_db_and_tables()

    case "net":
        connector = EthernetConnector(
            sample_time=SAMPLE_TIME,
            path=PATH,
        )

    case "api":
        connector = APIConnector(
            sample_time=SAMPLE_TIME,
            path=PATH,
        )

    case _:
        raise KeyError(f"Cannot find the mode: {MODE}.")

# Call HVAC Algorithms
# 1. read input from plc back plate comm
# 2. map the wet buld temp from plc tag to python variable and using as input for algorithm
# 3. call the algorithm
# 4. map the return value to plc tag: cooling water return temperature
# 5. call the connector write function, using write_output function
input_dict = connector.read_input()

FLAG = True
while FLAG:
   print('Starting Progarm:...')
   input_dict = connector.read_input()
   input_formatted = StationData.model_validate(input_dict)
   wetBulbTemp = input_formatted.Tag_TW

   # Construt the AI Optimizer with wet buld temperature input
   optimizer = Optimizer(wetBulbTemp) 

   # Validate the input temperature
   inputValidated = optimizer.validateInput()
   if inputValidated:
    return_temp = optimizer.calculate_cooling_water_return_temperature()
    outputValidated = optimizer.validateOutput(return_temp)
    if outputValidated:
      input_formatted.Tag_CTW_SP = return_temp
      connector.write_input(input_formatted)
    else:
      print('Invalid cooling water return temperature')
   else:
    print('Invalid wet bulb temperature')
   print(input_formatted)
   connector.update()

