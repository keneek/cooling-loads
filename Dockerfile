FROM python:3.13-slim

WORKDIR /app

# Copy only the necessary files first
COPY pyproject.toml poetry.lock ./
COPY app.py ashrae_data.csv ./
COPY .streamlit .streamlit

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-root

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"] 