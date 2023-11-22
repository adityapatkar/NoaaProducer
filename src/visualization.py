import boto3
import streamlit as st
from boto3.dynamodb.conditions import Key
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
import logging

from src.constants import AWS_REGION, STATION_URL, API_KEY

logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
)


def fetch_stations(table_name):
    """
    Fetch all the stations from the DynamoDB table
    """
    table = dynamodb.Table(table_name)
    response = table.scan(ProjectionExpression="station")
    stations = {item["station"] for item in response["Items"]}
    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="station",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        stations.update({item["station"] for item in response["Items"]})
    return list(stations)


@st.cache_data
def fetch_noaa_stations():
    """
    Fetch all the stations from the NOAA API
    """
    base_url = STATION_URL
    headers = {"token": API_KEY}
    params = {"locationid": f"FIPS:24", "limit": 1000}  # FIPS code for Maryland

    stations = {}
    while True:
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(
                f"Error while fetching stations from NOAA API, error: {response.status_code}"
            )
            break  # Handle errors or rate limiting as needed

        data = response.json()
        logger.info(f"Fetched {len(data['results'])} stations from NOAA API")
        for result in data["results"]:
            stations[result["name"]] = result["id"]

        if "metadata" in data and "resultset" in data["metadata"]:
            offset = data["metadata"]["resultset"].get("offset", 0)
            count = data["metadata"]["resultset"].get("count", 0)
            if offset + params["limit"] >= count:
                break  # Exit loop if all records have been fetched

        params["offset"] = offset + params["limit"]

    return stations


def fetch_data_from_dynamodb(table_name, location):
    logger.info(f"Fetching data for station: {location}")
    table = dynamodb.Table(table_name)
    response = table.query(KeyConditionExpression=Key("station").eq(location))
    if "Items" not in response:
        logger.error(f"Error while fetching data for station: {location}")
        return []
    logger.info(f"Fetched {len(response['Items'])} records for station: {location}")
    return response["Items"]


def create_plot(data, title, y_label):
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    # Define colors for each datatype
    colors = {
        "TOBS": "blue",
        "PRCP": "green",
        "SNOW": "cyan",
        "TMAX": "red",
        "TMIN": "purple",
    }

    plt.figure(figsize=(10, 6))

    # Plot each datatype in a different color
    for datatype, group in df.groupby("datatype"):
        plt.scatter(
            group["date"],
            group["value"],
            label=datatype,
            color=colors.get(datatype, "black"),
        )
    plt.xlabel("timestamp")
    plt.xticks(rotation=45)
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()

    return plt
