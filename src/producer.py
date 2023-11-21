""" 
    This file contains the producer class
"""

import json
import boto3
import requests
import os
import logging

from src.constants import (
    API_KEY,
    DATA_URL,
    STATION_URL,
    AWS_REGION,
    LOG_LEVEL,
    STREAM_NAME,
)

logger = logging.getLogger()


class Producer:
    """
    This class is responsible for producing the data
    """

    def __init__(self, data_types, start_date, end_date, station_name_flag):
        logger.info("Initializing Producer")
        self.kinesis_client = boto3.client(
            "kinesis",
            region_name=AWS_REGION,
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        self.station_name_flag = station_name_flag
        self.station_cache = {}
        self.headers = {"token": API_KEY}
        self.data_types = data_types
        self.params = {
            "datasetid": "GHCND",
            "startdate": start_date,
            "enddate": end_date,
            "locationid": "FIPS:24",
            "datatypeid": ",".join(self.data_types),
            "limit": 1000,
            "offset": 1,
            "units": "metric",
        }
        logger.info("Producer initialized")

    def get_station(self, station_id):
        """
        Get the station information from the station url
        """
        logger.info(f"Getting station {station_id}")
        if station_id in self.station_cache:
            logger.info(f"Station {station_id} found in cache")
            return self.station_cache[station_id]

        station = requests.get(
            f"{STATION_URL}/{station_id}", headers=self.headers, timeout=15
        )
        if station.status_code == 200:
            logger.info(f"Station {station_id} found in NOAA")
            station_data = station.json()
            self.station_cache[station_id] = station_data.get("name", "")
            return station_data.get("name", "")

        logger.error(
            f"Station {station_id} not found in NOAA, error: {station.status_code}"
        )
        self.station_cache[station_id] = "Unknown"
        return "Unknown"

    def get_data(self, limit, offset, station_name_flag):
        """
        Get the data from the data url
        """
        logger.info(f"Getting data with limit {limit} and offset {offset}")
        self.params["limit"] = limit
        self.params["offset"] = offset

        data = requests.get(
            DATA_URL, headers=self.headers, params=self.params, timeout=90
        )
        if data.status_code == 200:
            data = data.json()
            logger.info(f"Data found with limit {limit} and offset {offset}")
            results = data.get("results", [])
            count = data.get("metadata", {}).get("resultset", {}).get("count", 0)
            logger.info(f"Data found with count {count}")
            clean_results = []
            for record in results:
                formatted_record = {
                    "date": record["date"],
                    "datatype": record["datatype"],
                    "station": record["station"],
                    "value": record["value"],
                }
                if station_name_flag:
                    station_name = self.get_station(formatted_record["station"])
                    formatted_record["station_name"] = station_name
                clean_results.append(formatted_record)

            return clean_results

        logger.error(
            f"Data not found with limit {limit} and offset {offset}, error: {data.status_code}"
        )
        return []

    def put_record(self, record):
        """
        Put the record in the kinesis stream
        """
        logger.info(f"Putting record in kinesis stream")
        response = self.kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(record),
            PartitionKey=record["station"],
        )
        logger.info(
            f"Record put in kinesis stream with response {response['ResponseMetadata']['HTTPStatusCode']}"
        )

    def produce(self):
        """
        Produce the data
        """
        logger.info("Producing data")
        limit = 1000
        offset = 1
        while True:
            data = self.get_data(limit, offset, self.station_name_flag)
            if not data:
                logger.info("No data found, exiting")
                break

            for record in data:
                self.put_record(record)
            offset += limit

            # stop on keybord interrupt
            if KeyboardInterrupt:
                break

            if len(data) < limit:
                logger.info("All data produced, exiting")
                break
        logger.info("Data produced")
