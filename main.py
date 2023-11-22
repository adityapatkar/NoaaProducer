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


def main():
    """
    This is the main function that will be called by streamlit
    """
    setup()

    stations = fetch_noaa_stations()

    st.sidebar.title("Select Page")
    page = st.sidebar.selectbox("Select Page", ["Home", "Producer", "Visualizer"])

    if page == "Producer":
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

        start_date = form.date_input("Select the start date", value=default_start_date)
        end_date = form.date_input("Select the end date", value=default_end_date)
        station_name_flag = False
        submit_button = form.form_submit_button(label="Submit")

        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")

        if submit_button:
            with st.spinner("Fetching data from NOAA API"):
                producer = Producer(
                    data_types, start_date, end_date, station_name_flag, stations
                )
                try:
                    producer.produce()
                    st.success("Data successfully produced")
                except Exception as e:
                    st.error(f"Error while producing data: {e}")
                    return

    elif page == "Visualizer":
        st.title("Weather Data Visualization")
        table_name = st.selectbox("Select Table", ["Precipitation", "Temperature"])
        # stations = fetch_noaa_stations()
        # selected_stations = st.multiselect("Select Station(s)", list(stations.keys()))

        station_ids = fetch_stations(table_name)

        station_swapped = {v: k for k, v in stations.items()}
        station_names = [
            station_swapped.get(station_id, "") for station_id in station_ids
        ]

        selected_stations = st.multiselect("Select Station(s)", station_names)
        if st.button("Fetch Data"):
            for location in selected_stations:
                with st.spinner(f"Fetching data for station: {location}"):
                    data = fetch_data_from_dynamodb(table_name, stations[location])
                    # data = fetch_data_from_dynamodb(table_name, location)
                    if data:
                        st.success(
                            f"Fetched {len(data)} records for station: {location}"
                        )
                        # st.write(data)
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
                        st.pyplot(plot)
                    else:
                        st.write(f"No data found for station: {stations[location]}")

                # horizontal line
                st.write("---")


if __name__ == "__main__":
    main()
