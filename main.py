import streamlit as st
import logging
import datetime

from src.producer import Producer
from src.visualization import (
    fetch_noaa_stations,
    fetch_data_from_dynamodb,
    create_plot,
    fetch_stations,
)

logger = logging.getLogger()


def setup():
    """
    Streamlit related setup. This has to be run for each page.
    """
    hide_streamlit_style = """
    
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # configure logging
    logging.basicConfig(level=logging.INFO)

    logger.info("Streamlit setup complete")


def home():
    """
    This is the home page of the app
    """
    st.title("Welcome to ClimaStream")

    # Introduction to the app
    st.write(
        """
    ## Empowering Weather Insights
    ClimaStream is a weather data processing and visualization tool designed to 
    bring you real-time insights from various weather stations across Maryland. 
    
    Utilizing the power of AWS Kinesis for live-streaming data and Streamlit for an 
    intuitive user interface, ClimaStream enables users to produce and visualize weather 
    data with unprecedented ease and precision.
    
    ### Navigate to:
    
    - **Producer**: Activate the data producer to retrieve and stream live weather data 
    from NOAA's API, process it, and dispatch it to the AWS Kinesis stream. The consumer will
    then store the data in a DynamoDB table automatically.
    
    - **Visualization**: Explore interactive visualizations of weather data, allowing 
    for in-depth analysis and pattern recognition.
    
    Select a page from the sidebar to begin your journey into weather data exploration.
    """
    )

    st.markdown(
        "Go to the **Producer** page to start streaming data or visit the **Visualization** page to view the data."
    )


def visualization(stations):
    """
    This page is responsible for visualizing the data that was retrived by the producer from the NOAA API. It will fetch the data from the DynamoDB table and plot it.
    """
    st.title("Weather Data Visualization")

    st.write(
        "This page is responsible for visualizing the data that was retrived by the producer from the NOAA API. It will fetch the data from the DynamoDB table and plot it."
    )
    st.write(
        "The data includes precipitation and temperature data for the state of Maryland. The data is measured in metric units."
    )
    st.write("Precipitation table includes the following data types: PRCP, SNOW")
    st.write("Temperature table includes the following data types: TOBS, TMAX, TMIN")
    table_name = st.selectbox("Select Table", ["Precipitation", "Temperature"])
    logger.info(f"Selected table: {table_name} for visualization")

    # Fetch the stations from the DynamoDB table
    station_ids = fetch_stations(table_name)

    # Fetch the station names from the NOAA API (cached)
    station_swapped = {v: k for k, v in stations.items()}
    station_names = [station_swapped.get(station_id, "") for station_id in station_ids]

    # remove empty strings
    station_names = [name for name in station_names if name]

    # sort the station names
    station_names.sort()

    # Select the station
    selected_stations = st.multiselect("Select Station(s)", station_names)
    if st.button("Fetch Data"):
        for location in selected_stations:
            with st.spinner(f"Fetching data for station: {location}"):
                logger.info(f"Fetching data for station: {location} from DynamoDB")
                data = fetch_data_from_dynamodb(table_name, stations[location])
                if data:
                    st.subheader(f"Data for station: {location}")
                    st.success(f"Fetched {len(data)} records for station: {location}")
                    # st.write(data) # uncomment to see the data for debugging

                    # Create the plot
                    if table_name == "Precipitation":
                        plot = create_plot(
                            data,
                            f"Precipitation for {location}",
                            "Precipitation",
                        )
                    else:
                        plot = create_plot(
                            data,
                            f"Temperature for {location}",
                            "Temperature",
                        )
                    st.plotly_chart(plot)
                    logger.info(f"Created plot for station: {location}")
                else:
                    st.write(f"No data found for station: {stations[location]}")
                    logger.error(f"No data found for station: {stations[location]}")

            # horizontal line
            st.write("---")


def producer(stations):
    st.title("Weather Data Producer")
    st.write(
        "This page is responsible for producing the data. It will fetch the data from the NOAA API and send it to the Kinesis stream."
    )

    form = st.form(key="producer_form")
    data_types = form.multiselect(
        "Select the data types to be fetched",
        ["TOBS", "PRCP", "SNOW", "TMAX", "TMIN"],
        ["TOBS", "PRCP", "SNOW", "TMAX", "TMIN"],
    )
    default_start_date = datetime.datetime(2021, 10, 1)
    default_end_date = datetime.datetime(2021, 10, 31)

    # Select the start and end date
    start_date = form.date_input("Select the start date", value=default_start_date)
    end_date = form.date_input("Select the end date", value=default_end_date)
    station_name_flag = False
    submit_button = form.form_submit_button(label="Submit")

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    if submit_button:
        with st.spinner("Fetching data from NOAA API"):
            # Create the producer
            producer = Producer(
                data_types, start_date, end_date, station_name_flag, stations
            )
            try:
                # Produce the data
                producer.produce()
                st.success("Data successfully produced")
            except Exception as e:
                st.error(f"Error while producing data: {e}")
                logger.error(f"Error while producing data: {e}")
                return


def main():
    """
    This is the main function that will be called by streamlit
    """
    setup()

    # Fetch the stations from the NOAA API
    stations = fetch_noaa_stations()

    st.sidebar.title("Select Page")
    page = st.sidebar.selectbox("Select Page", ["Home", "Producer", "Visualizer"])

    if page == "Producer":
        producer(stations)
    elif page == "Home":
        home()
    elif page == "Visualizer":
        visualization(stations)


if __name__ == "__main__":
    main()
