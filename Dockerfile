FROM python:3.9


WORKDIR /app

COPY requirements.txt .


RUN pip install -r requirements.txt

COPY . .

#run on port 80
CMD ["streamlit", "run", "main.py", "--server.port", "80"]

# docker build -t NoaaProducer:latest .

# docker run -p 8501:8501 streamlit:latest