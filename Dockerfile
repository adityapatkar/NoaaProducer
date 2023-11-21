FROM python:3.9


WORKDIR /app

COPY requirements.txt .


RUN pip install -r requirements.txt

COPY . .


CMD ["streamlit", "run", "main.py"]


# docker build -t NoaaProducer:latest .

# docker run -p 8501:8501 streamlit:latest