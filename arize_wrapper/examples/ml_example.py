"""Classical ML batch-prediction logging example."""

import pandas as pd
from arize.utils.types import Environments, ModelTypes

from arize_wrapper import ArizeConfig, configure_default_logging
from arize_wrapper.ml import init_ml_client, log_predictions

configure_default_logging()
config = ArizeConfig.from_env()
client = init_ml_client(config)

predictions = pd.DataFrame(
    {
        "prediction_id": ["txn-1001", "txn-1002"],
        "amount": [42.50, 998.10],
        "prediction_label": ["not_fraud", "fraud"],
        "prediction_score": [0.02, 0.91],
    }
)

response = log_predictions(
    client=client,
    config=config,
    dataframe=predictions,
    schema_kwargs={
        "prediction_id_column_name": "prediction_id",
        "feature_column_names": ["amount"],
        "prediction_label_column_name": "prediction_label",
        "prediction_score_column_name": "prediction_score",
    },
    model_type=ModelTypes.SCORE_CATEGORICAL,
    environment=Environments.PRODUCTION,
)
print(response)
