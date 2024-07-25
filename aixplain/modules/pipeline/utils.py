import json
from typing import Dict, Optional, Text, Union


def prepare_payload(data: Union[Text, Dict], data_asset: Optional[Union[Text, Dict]] = None) -> Dict:
    """Prepare pipeline execution payload, validating the input data

    Args:
        data (Union[Text, Dict]): input data
        data_asset (Optional[Union[Text, Dict]], optional): input data asset. Defaults to None.

    Returns:
        Dict: pipeline execution payload
    """
    from aixplain.factories import CorpusFactory, DatasetFactory, FileFactory

    # if an input data asset is provided, just handle the data
    if data_asset is None:
        # upload the data when a local path is provided
        data = FileFactory.to_link(data)
        if isinstance(data, dict):
            payload = data
            for key in payload:
                payload[key] = {"value": payload[key]}

            for node_label in payload:
                payload[node_label]["nodeId"] = node_label

            payload = {"data": list(payload.values())}
        else:
            try:
                payload = json.loads(data)
                if isinstance(payload, dict) is False:
                    if isinstance(payload, int) is True or isinstance(payload, float) is True:
                        payload = str(payload)
                    payload = {"data": payload}
            except Exception:
                payload = {"data": data}
    else:
        payload = {}
        if isinstance(data_asset, str) is True:
            data_asset = {"1": data_asset}

            # make sure data asset and data are provided in the same format,
            # mostly when in a multi-input scenario, where a dictionary should be provided.
            if isinstance(data, dict) is True:
                raise Exception(
                    'Pipeline Run Error: Similar to "data", please specify the node input label where the data asset should be set in "data_asset".'
                )
            else:
                data = {"1": data}
        elif isinstance(data, str) is True:
            raise Exception(
                'Pipeline Run Error: Similar to "data_asset", please specify the node input label where the data should be set in "data".'
            )

        # validate the existence of data asset and data
        for node_label in data_asset:
            asset_payload = {"dataAsset": {}}
            data_asset_found, data_found = True, False
            try:
                dasset = CorpusFactory.get(str(data_asset[node_label]))
                asset_payload["dataAsset"]["corpus_id"] = dasset.id
                if len([d for d in dasset.data if d.id == data[node_label]]) > 0:
                    data_found = True
            except Exception:
                try:
                    dasset = DatasetFactory.get(str(data_asset[node_label]))
                    asset_payload["dataAsset"]["dataset_id"] = dasset.id

                    if len([dfield for dfield in dasset.source_data if dasset.source_data[dfield].id == data[node_label]]) > 0:
                        data_found = True
                    else:
                        for target in dasset.target_data:
                            for target_row in dasset.target_data[target]:
                                if target_row.id == data[node_label]:
                                    data_found = True
                                    break
                            if data_found is True:
                                break
                except Exception:
                    data_asset_found = False
            if data_asset_found is False:
                raise Exception(
                    f'Pipeline Run Error: Data Asset "{data_asset[node_label]}" not found. Make sure this asset exists or you have access to it.'
                )
            elif data_found is False:
                raise Exception(
                    f'Pipeline Run Error: Data "{data[node_label]}" not found in Data Asset "{data_asset[node_label]}" not found.'
                )

            asset_payload["dataAsset"]["data_id"] = data[node_label]
            payload[node_label] = asset_payload

        if len(payload) > 1:
            for node_label in payload:
                payload[node_label]["nodeId"] = node_label
        payload = {"data": list(payload.values())}
    return payload
