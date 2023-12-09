""" 
Test the Producer class
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from src.producer import Producer


class TestProducer(unittest.TestCase):
    """
    Test the Producer class
    """

    @patch("src.producer.requests.get")
    def test_get_data(self, mock_get):
        """
        Test the get_data method
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "date": "2023-01-01",
                    "datatype": "PRCP",
                    "station": "STATION1",
                    "value": 10,
                },
                {
                    "date": "2023-01-02",
                    "datatype": "TMAX",
                    "station": "STATION2",
                    "value": 20,
                },
            ],
            "metadata": {"resultset": {"count": 2}},
        }
        mock_get.return_value = mock_response

        # Creating an instance of Producer
        producer = Producer(
            data_types=["PRCP", "TMAX"],
            start_date="2023-01-01",
            end_date="2023-01-02",
            station_name_flag=True,
            stations={"STATION1": "Station One", "STATION2": "Station Two"},
        )

        # Call get_data method
        result = producer.get_data(
            limit=2,
            offset=1,
            station_name_flag=True,
            stations={"STATION1": "Station One", "STATION2": "Station Two"},
        )

        # Assert that the results are as expected
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["station_name"], "Station One")
        self.assertEqual(result[1]["station_name"], "Station Two")

    @patch("src.producer.boto3.client")
    def test_put_record(self, mock_boto3_client):
        """
        Test the put_record method
        """
        # Mocking the boto3 Kinesis client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Creating an instance of Producer
        producer = Producer(
            data_types=[],
            start_date="",
            end_date="",
            station_name_flag=False,
            stations={},
        )

        # Prepare a record to put
        record = {
            "date": "2023-01-01",
            "datatype": "PRCP",
            "station": "STATION1",
            "value": 10,
        }

        # Call put_record method
        producer.put_record(record)

        # Assert that boto3 client's put_record was called with expected parameters
        mock_client.put_record.assert_called_with(
            StreamName="NoaaStream",
            Data=json.dumps(record),
            PartitionKey="STATION1",
        )


if __name__ == "__main__":
    unittest.main()
