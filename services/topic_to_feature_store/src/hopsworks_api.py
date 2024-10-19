from typing import List

import hopsworks
from loguru import logger
import pandas as pd

from src.config import hopsworks_config as config


class HopsworksAPI:
    def __init__(self):
        # Connect to Hopsworks project during initialization
        self.project = hopsworks.login(
            # project=config.hopsworks_project_name,
            api_key_value=config.hopsworks_api_key,
        )
        # Get a handle to the Feature Store
        self.feature_store = self.project.get_feature_store()

    def push_value_to_feature_group(
        self,
        value: List[dict],
        feature_group_name: str,
        feature_group_version: int,
        feature_group_primary_keys: List[str],
        feature_group_event_time: str,
        start_offline_materialization: bool = False,
    ):
        """
        Pushes the given `value` to the specified Feature Group in the Feature Store.

        Args:
            value (List[dict]): The value to push to the Feature Store
            feature_group_name (str): The name of the Feature Group
            feature_group_version (int): The version of the Feature Group
            feature_group_primary_keys (List[str]): The primary key of the Feature Group
            feature_group_event_time (str): The event time of the Feature Group
            start_offline_materialization (bool): Whether to start the offline
                materialization or not when we save the `value` to the feature group

        Returns:
            None
        """
        # Get or create the feature group
        feature_group = self.feature_store.get_or_create_feature_group(
            name=feature_group_name,
            version=feature_group_version,
            primary_key=feature_group_primary_keys,
            event_time=feature_group_event_time,
            online_enabled=True,
        )

        # Convert the value to a pandas DataFrame
        value_df = pd.DataFrame(value)

        # Insert the value into the feature group
        result = feature_group.insert(
            value_df,
            write_options={
                "start_offline_materialization": start_offline_materialization
            },
        )
