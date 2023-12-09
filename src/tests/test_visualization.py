""" 
Test the visualization functions
"""

import unittest
from unittest.mock import Mock, patch
from src.visualization import (
    fetch_stations,
    fetch_noaa_stations,
    fetch_data_from_dynamodb,
    create_plot,
)


class TestVisualization(unittest.TestCase):
    """
    Test the visualization functions
    """

    @patch("src.visualization.init_dynamodb_client")
    def test_fetch_stations(self, mock_dynamodb_client):
        """
        Test the fetch_stations function
        """
        mock_table = Mock()
        mock_table.scan.return_value = {
            "Items": [{"station": "Station1"}, {"station": "Station2"}]
        }
        mock_dynamodb_client.return_value.Table.return_value = mock_table

        result = fetch_stations("Temperature")
        self.assertEqual(
            result,
            ["Station2", "Station1"]
            if result[0] == "Station2"
            else ["Station1", "Station2"],
        )

    @patch("src.visualization.requests.get")
    def test_fetch_noaa_stations(self, mock_get):
        """
        Test the fetch_noaa_stations function
        """
        # Mocking the requests.get response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"name": "Station1", "id": "ID1"},
                {"name": "Station2", "id": "ID2"},
            ],
            "metadata": {"resultset": {"offset": 1, "count": 2}},
        }
        mock_get.return_value = mock_response

        result = fetch_noaa_stations()
        self.assertEqual(result, {"Station1": "ID1", "Station2": "ID2"})

    @patch("src.visualization.init_dynamodb_client")
    def test_fetch_data_from_dynamodb(self, mock_dynamodb_client):
        """
        Test the fetch_data_from_dynamodb function
        """
        mock_table = Mock()
        mock_table.query.return_value = {
            "Items": [
                {"station": "Station1", "data": "Data1"},
                {"station": "Station2", "data": "Data2"},
            ]
        }
        mock_dynamodb_client.return_value.Table.return_value = mock_table

        result = fetch_data_from_dynamodb("Temperature", "Station1")
        self.assertEqual(
            result,
            [
                {"station": "Station1", "data": "Data1"},
                {"station": "Station2", "data": "Data2"},
            ]
            if result[0]["station"] == "Station1"
            else [
                {"station": "Station2", "data": "Data2"},
                {"station": "Station1", "data": "Data1"},
            ],
        )

    def test_create_plot(self):
        """
        Test the create_plot function
        """
        # Sample data for testing
        data = [
            {"date": "2021-01-01", "value": 10, "datatype": "TOBS"},
            {"date": "2021-01-02", "value": 15, "datatype": "TOBS"},
        ]
        title = "Test Plot"
        y_label = "Value"

        # Call the function under test
        fig = create_plot(data, title, y_label)

        # Basic checks on the plot
        self.assertIsNotNone(fig)
        self.assertIn(title, fig.layout.title.text)
        self.assertEqual(fig.layout.yaxis.title.text, y_label)


if __name__ == "__main__":
    unittest.main()
