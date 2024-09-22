import hopsworks
import pandas as pd
from src.config import hopsworks_config as config


def push_value_to_feature_group(
    value: dict,
    feature_group_name: str,
    feature_group_version: int,
    feature_group_primary_keys: list[str],
    feature_group_event_time: str,
    start_offline_materialization: bool,
):
    """
    Pushes a value to a feature group.

    Args:
        value: The value to push.
        feature_group_name: The name of the feature group.
        feature_group_version: The version of the feature group.
        feature_group_primary_key: The primary key of the feature group.
        feature_group_event_time: The event time of the feature group.
        start_offline_materialization: Whether to start the offline materialization job.

    Returns:
        None
    """
    project = hopsworks.login(
        project=config.hopsworks_project_name,
        api_key_value=config.hopsworks_api_key,
    )

    feature_store = project.get_feature_store()

    feature_group = feature_store.get_or_create_feature_group(
        name=feature_group_name,
        version=feature_group_version,
        primary_key=feature_group_primary_keys,
        event_time=feature_group_event_time,
        online_enabled=True,
    )

    # Transform the value dict into a pandas dataframe
    value_df = pd.DataFrame([value])

    feature_group.insert(
        value_df,
        write_options={"start_offline_materialization": start_offline_materialization},
    )
