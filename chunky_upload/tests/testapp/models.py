#!/usr/bin/env python3
"""Setups a series of models to test chunked_upload models."""

__author__ = "Jaryd Rester"
__copyright__ = "2022-03-23"

# stdlib

# django

# local django
from chunky_upload.models import AbstractChunkedUpload

# thirdparty

TEST_CHUNKED_UPLOAD_MODEL = "testapp.ChunkedUploadAbstractTestModel"


class ChunkedUploadAbstractTestModel(AbstractChunkedUpload):
    pass
