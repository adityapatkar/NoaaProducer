import streamlit as st
import logging
import datetime

from src.producer import Producer


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
    station_name_flag = form.checkbox("Include station name in the data")
    submit_button = form.form_submit_button(label="Submit")

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    if submit_button:
        with st.spinner("Fetching data from NOAA API"):
            producer = Producer(data_types, start_date, end_date, station_name_flag)
            try:
                producer.produce()
                st.success("Data successfully produced")
            except Exception as e:
                st.error(f"Error while producing data: {e}")
                return


if __name__ == "__main__":
    main()
