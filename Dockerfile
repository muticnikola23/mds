FROM python:3.11


WORKDIR /app


RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy aiosqlite alembic


COPY dependencies /app/dependencies/
COPY migrations /app/migrations/
COPY models /app/models/
COPY tests /app/tests/
COPY alembic.ini /app/
COPY main.py /app/



EXPOSE 8000


CMD ["sh", "-c", "alembic upgrade 72458f51d92d && uvicorn main:app --host 0.0.0.0 --port 8000"]


