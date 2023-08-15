from typing import Union, Text, Optional, Any, Dict

import os
from pathlib import Path
from urllib.parse import urlparse

from aixplain.enums import StorageType
from aixplain.assets.base import BaseAsset
from aixplain.client import create_retry_session


class File(BaseAsset):
    """
    File class that extends the BaseAsset class.
    This class is responsible for handling file assets, including uploading
    files to S3.
    """

    asset_path = 'file'

    @classmethod
    def check_storage_type(cls, input_link: Any) -> StorageType:
        """
        Determine the storage type of the given input_link.

        The method returns one of three StorageType enumerations:
        - StorageType.FILE if the input_link points to an file on the fs.
        - StorageType.URL if the input_link is a valid URL.
        - StorageType.TEXT if the input_link doesn't match any criteria.

        :param input_link: The input link to be checked
        :return: One of the StorageType enumerations
        """
        result = urlparse(input_link)
        is_url = all([result.scheme, result.netloc])

        if os.path.exists(input_link):
            return StorageType.FILE
        elif is_url:
            return StorageType.URL
        else:
            return StorageType.TEXT

    @classmethod
    def batch_upload_to_s3(cls, obj: Union[Text, Dict]) -> Union[Text, Dict]:
        """
        Uploads the object to S3, handling both dictionaries and strings as
        input.

        - If the input is a dictionary, it will recursively handle the values,
        uploading any file paths to S3.
        - If the input is a string that is identified as a file, it will
        upload the file to S3.

        :param obj: The input object, either a dictionary or a string
        :return: The modified object with updated S3 links or the original
                input if no changes were made
        """
        if isinstance(obj, dict):
            dest = obj.copy()

            for k, v in obj.items():
                if isinstance(v, (str, dict)):
                    dest[k] = cls.batch_upload_to_s3(v)

            return dest

        elif (isinstance(obj, str) and
                cls.check_storage_type(obj) == StorageType.FILE):
            return cls.upload_to_s3(obj)

        else:
            return obj

    @classmethod
    def upload_to_s3(cls,
                     file_name: Union[Text, Path],
                     content_type: Text = 'text/csv',
                     content_encoding: Optional[Text] = None):
        """
        Uploads a file to Amazon S3.

        :param file_name: The path of the file to upload.
        :param content_type: The content type of the file
               (default is "text/csv").
        :param content_encoding: The content encoding of the file
               (default is None).
        :param client: Optional AixplainClient instance.

        :return: The S3 URL of the uploaded file.
        """

        response = cls.client.request('POST',
                                      f'sdk/{cls.asset_path}/upload/temp-url',
                                      json={'contentType': content_type,
                                            'originalName': file_name})
        payload = response.json()
        path = payload['key']
        presigned_url = payload['uploadUrl']

        headers = {'Content-Type': content_type}
        if content_encoding:
            headers['Content-Encoding'] = content_encoding

        with open(file_name, 'rb') as file:
            content = file.read()

        s3_session = create_retry_session()

        s3_response = s3_session.request('PUT',
                                         presigned_url,
                                         headers=headers,
                                         data=content)
        s3_response.raise_for_status()

        bucket_name = urlparse(presigned_url).netloc.split('.')[0]
        return f's3://{bucket_name}/{path}'
