#!/bin/sh

# wait 10 minutes until some data are processed
sleep 600s
python3 training_environment/facebook_prophet.py
python3 training_environment/regressors.py
wait