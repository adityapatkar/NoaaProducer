# ClimaStream

ClimaStream is a weather data processing and visualization tool developed as a part of the MSML650 Cloud Computing course. This application is designed to fetch real-time weather data using NOAA's API, process it using AWS Kinesis, and visualize the data through an interactive Streamlit application. The application is containerized using Docker, allowing for easy deployment and scaling. The original deployment was done using AWS ECS, but the application can be deployed on any cloud platform that supports Docker. The application is designed to be used in conjunction with the consumer application, which can be a Lambda function or a separate Docker container. Lambda function code can be found under the `lambda` directory. The code is deployed using GitHub Actions, which can be found under the `.github/workflows` directory.

## Features

- Fetch and process weather data from NOAA's API.
- Stream data in real-time using AWS Kinesis.
- Consumer stores the data in Precipitation and Temperature tables in DynamoDB.
- Visualize weather data interactively with Streamlit.
- Dockerized for consistent deployment and scalability.

## Prerequisites

Before running the ClimaStream, ensure that you have the following prerequisites installed:

- Docker
- An AWS account with configured environment variables for access. (Check the [Environment Variables](#environment-variables) section for more information.

## Installation

ClimaStream can be set up using Docker or by running it directly. Please follow the instructions below for your preferred method of installation.

### Option 1: Using Docker

1. Clone the repository to your local machine:

```bash
git https://github.com/adityapatkar/NoaaProducer
cd NoaaProducer
```

2. Build the Docker image:

```bash
docker build -t NoaaProducer . # Don't forget the period at the end
```

3. Run the Docker container (replace `your-env-vars` with the required environment variables):

```bash
docker run -p 8501:8501 -e your-env-vars NoaaProducer
```

### Option 2: Running Directly

1. Set up a Python environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

2. Set up the environment variables (see the [Environment Variables](#environment-variables) section for more information).

3. Run the Streamlit application:

```bash
streamlit run app.py
```

## Environment Variables

To run ClimaStream, you will need to set the following environment variables:

- `AWS_ACCESS_KEY_ID`: Your AWS access key.
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
- `AWS_REGION`: The default AWS region for your Kinesis stream.
- `NOAA_TOKEN`: Your API key for the NOAA API.
- `DATA_URL` : The URL for the NOAA API. `https://www.ncdc.noaa.gov/cdo-web/api/v2/data`
- `STATION_URL` : The URL for the NOAA API. `https://www.ncdc.noaa.gov/cdo-web/api/v2/stations`
- `STREAM_NAME` : The name of the Kinesis stream.

## Usage

Once the application is running, navigate to `http://localhost:8501` in your web browser if using option 2 or `http://localhost:80` if using option 1. You can choose between the Producer and Visualization pages to either stream new data or visualize existing data.

## Automated Deployment with GitHub Actions

ClimaStream is configured for continuous deployment using GitHub Actions, ensuring that the latest version of the application is automatically built and deployed whenever changes are pushed to the repository.

### Workflow

The `.github/workflows` directory contains the CI/CD pipeline definitions, which orchestrate the following actions:

- **Build**: Compiles the Docker image based on the `Dockerfile` present in the repository.
- **Test**: Runs any tests defined in the application to ensure functionality remains consistent.
- **Push**: Upon successful build and test, the Docker image is pushed to an Amazon ECR repository.
- **Deploy**: The new Docker image is then deployed to an Amazon ECS service, which is monitored for health and auto-scaled based on predefined metrics.

### Steps to Enable GitHub Actions

To enable GitHub Actions for your own fork or copy of the repository, follow these steps:

1. Navigate to the 'Actions' tab of your GitHub repository.
2. If prompted, confirm that you want to enable GitHub Actions for the repository.
3. Add the necessary AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`) and your `NOAA_API_KEY` as secrets in your repository settings.

### Customizing the Workflow

You may customize the workflow as needed by editing the YAML files within the `.github/workflows` directory. Make sure to adjust resource names, paths, and environment variables to fit your deployment specifics.

### Monitoring Deployments

GitHub Actions provides detailed logs for each workflow execution. You can monitor the deployment process and troubleshoot any issues that arise directly from the GitHub repository interface.

## Contributions

We welcome contributions to the ClimaStream project. Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
