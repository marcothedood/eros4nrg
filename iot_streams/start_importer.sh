#!/bin/sh

set -u

DEBUG="${DEBUG:-0}"

while true; do
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$ts] Starting importer cycle (DEBUG=$DEBUG)"

  if [ "$DEBUG" = "1" ]; then
    set -ex
    python3 iot_streams/import_data.py \
      --url "https://emotion-projects.eu/api/vehicle-states/?ordering=-timestamp" \
      --drct "emotion" \
      --filename "vehicle_states"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] vehicle_states finished (debug)"

    python3 iot_streams/import_data.py \
      --url "https://emotion-projects.eu/api/tower-states/?ordering=-timestamp" \
      --drct "emotion" \
      --filename "tower_states"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] tower_states finished (debug)"
    set +ex
  else
    python3 iot_streams/import_data.py \
      --url "https://emotion-projects.eu/api/vehicle-states/?ordering=-timestamp" \
      --drct "emotion" \
      --filename "vehicle_states" &
    PID1=$!

    python3 iot_streams/import_data.py \
      --url "https://emotion-projects.eu/api/tower-states/?ordering=-timestamp" \
      --drct "emotion" \
      --filename "tower_states" &
    PID2=$!

    wait $PID1; EC1=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] vehicle_states exit=$EC1"

    wait $PID2; EC2=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] tower_states  exit=$EC2"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle completed. Sleeping 5 minutes..."
  sleep 300
done
