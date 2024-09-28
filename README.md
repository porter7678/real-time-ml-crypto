# real-time-ml-crypto
A full-stack data science / MLOps tool for predicting crypto prices in real-time


## TODO
 - [x] trade producer
    - [x] extract config params
    - [x] dockerize
 - [x] trade to ohlcv service
 - [x] topic to feature store service
 - [ ] historical backfill
    - [X] Implement a Kraken Historical data reader (trade producer)
    - [X] Adjust timestmps used to bucket trades into windows (trade to ohlcv)
    - [ ] Save historical ohlcv features in batches to the offline store (topic to feature store)






  - [ ] Make the trade producer produce data for multiple product ids