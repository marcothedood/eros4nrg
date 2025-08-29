FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /EROS4NRG

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl \
    && rm -rf /var/lib/apt/lists/*


COPY iot_streams/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY clients ./clients
COPY config  ./config
COPY iot_streams ./iot_streams


RUN chmod +x ./iot_streams/start_importer.sh


ENV PYTHONPATH="/EROS4NRG"


ENTRYPOINT ["sh", "./iot_streams/start_importer.sh"]