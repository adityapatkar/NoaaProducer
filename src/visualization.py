""" 
This module contains functions to fetch data from DynamoDB and create visualizations
"""

# required imports
import boto3
import streamlit as st
from boto3.dynamodb.conditions import Key
import pandas as pd
import plotly.express as px
import requests
import os
import logging

from src.constants import AWS_REGION, STATION_URL, API_KEY

# configure logging
logger = logging.getLogger()


# Function to initialize DynamoDB client
def init_dynamodb_client(aws_region, aws_secret_access_key, aws_access_key_id):
    """
    Initialize the DynamoDB client
    """
    return boto3.resource(
        "dynamodb",
        region_name=aws_region,
        aws_secret_access_key=aws_secret_access_key,
        aws_access_key_id=aws_access_key_id,
    )


def fetch_stations(table_name):
    """
    Fetch all the stations from the DynamoDB table
    """
    dynamodb = init_dynamodb_client(
        AWS_REGION, os.environ["AWS_SECRET_ACCESS_KEY"], os.environ["AWS_ACCESS_KEY_ID"]
    )
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

    # set up the base url, headers, and params
    base_url = STATION_URL
    headers = {"token": API_KEY}
    params = {"locationid": f"FIPS:24", "limit": 1000}  # FIPS code for Maryland
    stations = {}

    while True:
        # make the request
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(
                f"Error while fetching stations from NOAA API, error: {response.status_code}"
            )
            break

        # parse the response
        data = response.json()
        logger.info(f"Fetched {len(data['results'])} stations from NOAA API")
        for result in data["results"]:
            stations[result["name"]] = result["id"]

        # check if all records have been fetched
        if "metadata" in data and "resultset" in data["metadata"]:
            offset = data["metadata"]["resultset"].get("offset", 0)
            count = data["metadata"]["resultset"].get("count", 0)
            if offset + params["limit"] >= count:
                break  # Exit loop if all records have been fetched

        # update the offset
        params["offset"] = offset + params["limit"]

    return stations


def fetch_data_from_dynamodb(table_name, location):
    """
    Fetch data from the DynamoDB table for the given station
    """
    logger.info(f"Fetching data for station: {location}")

    dynamodb = init_dynamodb_client(
        AWS_REGION, os.environ["AWS_SECRET_ACCESS_KEY"], os.environ["AWS_ACCESS_KEY_ID"]
    )
    # Fetch data from the table
    table = dynamodb.Table(table_name)
    response = table.query(KeyConditionExpression=Key("station").eq(location))

    # Check if data is found
    if "Items" not in response:
        logger.error(f"Error while fetching data for station: {location}")
        return []
    logger.info(f"Fetched {len(response['Items'])} records for station: {location}")

    # Return the data
    return response["Items"]


def create_plot(data, title, y_label):
    """
    Create a plotly plot for the given data
    """

    # Convert data to pandas dataframe
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

    # Create the plot
    fig = px.scatter(
        df, x="date", y="value", color="datatype", color_discrete_map=colors
    )

    # Update the plot
    fig.update_layout(
        title=title,
        xaxis_title="timestamp",
        yaxis_title=y_label,
        legend_title="datatype",
    )
    fig.update_xaxes(tickangle=45)

    # Return the plot
    return fig
