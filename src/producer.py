""" 
    This file contains the producer class
"""

# required imports
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
    STREAM_NAME,
)

# configure logging
logger = logging.getLogger()


class Producer:
    """
    This class is responsible for producing the data
    """

    def __init__(self, data_types, start_date, end_date, station_name_flag, stations):
        """
        Initialize the producer class
        """

        logger.info("Initializing Producer")

        # initialize kinesis client
        self.kinesis_client = boto3.client(
            "kinesis",
            region_name=AWS_REGION,
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )

        # initialize class variables
        self.station_name_flag = station_name_flag
        self.station_cache = {v: k for k, v in stations.items()}
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
        Get the station information from the station url (deprecated, using st cache now. Find in visualization.py)
        """
        logger.info(f"Getting station {station_id}")

        # check if station is in cache
        if station_id in self.station_cache:
            logger.info(f"Station {station_id} found in cache")
            return self.station_cache[station_id]

        # get station from NOAA
        station = requests.get(
            f"{STATION_URL}/{station_id}", headers=self.headers, timeout=15
        )

        # check if station is found
        if station.status_code == 200:
            logger.info(f"Station {station_id} found in NOAA")
            station_data = station.json()
            self.station_cache[station_id] = station_data.get("name", "")
            return station_data.get("name", "")

        logger.error(
            f"Station {station_id} not found in NOAA, error: {station.status_code}"
        )

        # if station not found, return unknown
        self.station_cache[station_id] = "Unknown"
        return "Unknown"

    def get_data(self, limit, offset, station_name_flag, stations):
        """
        Get the data from the data url
        """

        logger.info(f"Getting data with limit {limit} and offset {offset}")

        # set limit and offset
        self.params["limit"] = limit
        self.params["offset"] = offset

        # get data from NOAA
        data = requests.get(
            DATA_URL, headers=self.headers, params=self.params, timeout=90
        )

        # check if data is found
        if data.status_code == 200:
            data = data.json()
            logger.info(f"Data found with limit {limit} and offset {offset}")
            results = data.get("results", [])
            count = data.get("metadata", {}).get("resultset", {}).get("count", 0)
            logger.info(f"Data found with count {count}")
            clean_results = []

            # format the data
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
                formatted_record["station_name"] = (
                    stations[formatted_record["station"]]
                    if formatted_record["station"] in stations
                    else "Unknown"
                )
                clean_results.append(formatted_record)

            # return the data
            return clean_results

        logger.error(
            f"Data not found with limit {limit} and offset {offset}, error: {data.status_code}"
        )

        # if data not found, return empty list
        return []

    def put_record(self, record):
        """
        Put the record in the kinesis stream
        """

        # call kinesis client to put the record
        response = self.kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(record),
            PartitionKey=record["station"],
        )

    def produce(self):
        """
        Produce the data
        """
        logger.info("Producing data")
        limit = 1000
        offset = 1

        while True:
            # get the data
            data = self.get_data(
                limit, offset, self.station_name_flag, self.station_cache
            )
            if not data:
                logger.info("No data found, exiting")
                break

            # put the data in the stream
            for record in data:
                self.put_record(record)

            # update the offset
            offset += limit

            # check if all data is produced
            if len(data) < limit:
                logger.info("All data produced, exiting")
                break

        logger.info("Data produced")
