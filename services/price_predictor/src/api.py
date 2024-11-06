from fastapi import FastAPI, HTTPException, Query
from loguru import logger

from src.config import config
from src.price_predictor import PricePredictor
from src.utils import log_prediction_to_elasticsearch

app = FastAPI()

# we have one object per product id
predictors: dict[str, PricePredictor] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/predict")
def predict(product_id: str = Query(..., description="The product ID to predict")):
    logger.info(f"Received request for product id: {product_id}")

    try:
        if product_id not in config.api_supported_product_ids:
            raise HTTPException(status_code=400, detail="Product ID not supported")

        # if we don't have the predictor for this product id, we create it
        if product_id not in predictors:
            logger.debug(f"Attempting to create predictor for product id: {product_id}")
            predictors[product_id] = PricePredictor.from_model_registry(
                product_id=product_id,
                # these are read from the config file
                # the end user doesn't have to provide them
                ohlc_window_sec=config.ohlcv_window_sec,
                forecast_steps=config.forecast_steps,
                status=config.ml_model_status,
            )
            logger.debug(f"Successfully created predictor for product id: {product_id}")
        else:
            logger.debug(f"Using existing predictor for product id: {product_id}")

        # extract the predictor object for this product id
        predictor = predictors[product_id]

        # the ML magic happens here
        logger.debug("Predicting...")
        prediction = predictor.predict()
        log_prediction_to_elasticsearch(prediction)

        logger.debug("Returning prediction")
        return {"prediction": prediction.to_json()}
        # return prediction.to_json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
