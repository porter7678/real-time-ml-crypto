# real-time-ml-crypto
A full-stack data science / MLOps tool for predicting crypto prices in real-time


## TODO
 - [x] trade producer
    - [x] extract config params
    - [x] dockerize
 - [x] trade to ohlcv service
 - [x] topic to feature store service
 - [X] historical backfill
    - [X] Implement a Kraken Historical data reader (trade producer)
    - [X] Adjust timestmps used to bucket trades into windows (trade to ohlcv)
    - [X] Save historical ohlcv features in batches to the offline store (topic to feature store)

 - [X] Dockerize real-time feature pipeline
 - [X] Dockerize backfill feature pipeline (generate training data)
 - [X] Start on training pipeline
   - [X] Read data from store (write a class)
   - [X] Build a baseline model
   - [X] Integrate training with CometML
 - [X] Build an ML model
    - [X] Add an xgboost model
    - [X] Engineer features
    - [X] Tune hyperparameter
    - [X] Push model to registry
 - [X] Dockerize training service
 - [X] Make the trade producer produce data for multiple product ids

 - [ ] Fix a bug where it doesn't look like stuff is being pushed to the online feature store from the live pipeline