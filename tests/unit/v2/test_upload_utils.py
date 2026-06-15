"""Unit tests for v2 upload_utils.S3Uploader.construct_s3_url (ENG-3148).

Regression coverage for the bucket-extraction bug: path-style presigned URLs
(returned by some backends, e.g. dev) were not recognised and silently fell
back to a hardcoded ``aixplain-uploads`` bucket, producing wrong-bucket links
that broke downstream file fetches (e.g. Docling parsing during index upsert).
"""

from aixplain.v2.upload_utils import S3Uploader

KEY = "1/sdk/1700000000-doc.pdf"


def test_path_style_url_extracts_real_bucket():
    """Path-style URL (the dev shape) must yield the real bucket, not the fallback."""
    url = (
        "https://s3.amazonaws.com/aixplain-platform-backend-temp-dev/"
        "1/sdk/1700000000-doc.pdf?AWSAccessKeyId=ABC&Expires=1&Signature=z"
    )
    assert S3Uploader.construct_s3_url(url, KEY) == f"s3://aixplain-platform-backend-temp-dev/{KEY}"


def test_path_style_regional_url():
    url = "https://s3.us-east-1.amazonaws.com/my-bucket/key?X=y"
    assert S3Uploader.construct_s3_url(url, KEY) == f"s3://my-bucket/{KEY}"


def test_virtual_hosted_url_preserved():
    url = "https://aixplain-uploads.s3.amazonaws.com/1/sdk/doc.pdf?sig=1"
    assert S3Uploader.construct_s3_url(url, KEY) == f"s3://aixplain-uploads/{KEY}"


def test_virtual_hosted_regional_url():
    """Regional virtual-hosted URLs were also unhandled by the old regex."""
    url = "https://my-bucket.s3.eu-west-1.amazonaws.com/key?sig=1"
    assert S3Uploader.construct_s3_url(url, KEY) == f"s3://my-bucket/{KEY}"


def test_unrecognized_url_falls_back():
    url = "https://example.com/whatever"
    assert S3Uploader.construct_s3_url(url, KEY) == f"s3://aixplain-uploads/{KEY}"
