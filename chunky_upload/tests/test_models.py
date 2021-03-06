#!/usr/bin/env python3
"""Setups a test for Django"""

__author__ = "Jaryd Rester"
__copyright__ = "2022-03-23"

# stdlib
import hashlib
from io import BytesIO
from datetime import datetime
from unittest.mock import Mock, patch, PropertyMock

# django
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from django.test import TestCase

# local django
from chunky_upload.constants import COMPLETE
from chunky_upload.models import ChunkedUpload
from chunky_upload.models.abstract_models import AbstractChunkedUpload
from chunky_upload.settings import EXPIRATION_DELTA

# thirdparty
from model_bakery import baker


class ChunkedUploadAbstractTestModelTests(TestCase):
    @patch(
        "django.utils.timezone.now",
        Mock(return_value=datetime(2000, 1, 1, tzinfo=timezone.utc)),
    )
    def test__marking_chunked_upload_complete_works_as_expected(self):
        # assign
        model_instance = baker.make(ChunkedUpload)

        # act
        model_instance.complete_upload()
        model_instance.refresh_from_db()

        # assert
        self.assertEqual(model_instance.status, COMPLETE)
        self.assertEqual(
            model_instance.completed_on, datetime(2000, 1, 1, tzinfo=timezone.utc)
        )

    def test__user_field_exists_on_ChunkedUpload_model(self):
        # assign
        model_instance = baker.make(ChunkedUpload)

        # act

        # assert
        self.assertTrue(hasattr(model_instance, "user"))

    def test__expires_on_property_on_ChunkedUpload_model_works_as_expected(self):
        # assign
        model_instance = baker.make(ChunkedUpload)

        # assert
        self.assertEqual(
            model_instance.expires_on,
            model_instance.created_on + EXPIRATION_DELTA,
        )

    @patch(
        "django.utils.timezone.now",
        Mock(return_value=datetime(2020, 1, 1, tzinfo=timezone.utc)),
    )
    @patch(
        "chunky_upload.models.ChunkedUpload.expires_on",
        PropertyMock(return_value=datetime(2000, 1, 1, tzinfo=timezone.utc)),
    )
    def test__expired_on_property_on_ChunkedUpload_model_returns_expired_as_expected(
        self,
    ):
        # assign
        model_instance = baker.make(ChunkedUpload)

        # assert
        self.assertTrue(model_instance.expired)

    @patch(
        "django.utils.timezone.now",
        Mock(return_value=datetime(2008, 1, 1, tzinfo=timezone.utc)),
    )
    @patch(
        "chunky_upload.models.ChunkedUpload.expires_on",
        PropertyMock(return_value=datetime(2010, 1, 1, tzinfo=timezone.utc)),
    )
    def test__expired_on_property_on_ChunkedUpload_model_returns_nonexpired_as_expected(
        self,
    ):
        # assign
        model_instance = baker.make(ChunkedUpload)

        # assert
        self.assertFalse(model_instance.expired)

    def test__md5_property_on_ChunkedUpload_model_works_as_expected(self):
        # assign
        binary_data = BytesIO(b"test file")
        binary_hash = hashlib.md5()
        content_file = ContentFile(binary_data.read(), "testfile.txt")
        binary_hash.update(content_file.read())
        model_instance = baker.make(ChunkedUpload, file=content_file)

        # act
        checksum = model_instance.md5

        # assert
        self.assertEqual(binary_hash.hexdigest(), checksum)

    def test__append_chunk_works_as_expected(self):
        # assign
        binary_data = BytesIO(b"test file")
        chunk_data = BytesIO(b" new data")
        content_file = ContentFile(binary_data.read(), "testfile.txt")
        model_instance = baker.make(ChunkedUpload, file=content_file)

        # act
        model_instance.append_chunk(UploadedFile(chunk_data), chunk_size=40)
        model_instance.refresh_from_db()

        # assert
        self.assertEqual(
            model_instance.file.read(), BytesIO(b"test file new data").read()
        )
        self.assertEqual(model_instance.offset, 40)

    @patch("chunky_upload.signals.chunky_upload_complete.send_robust")
    def test__marking_upload_as_complete_dispatches_the_chunky_upload_complete_signal(
        self, mocked_chunked_upload_complete
    ):
        # assign
        binary_data = BytesIO(b"test file")
        content_file = ContentFile(binary_data.read(), "testfile.txt")
        model_instance = baker.make(ChunkedUpload, file=content_file)

        # act
        model_instance.complete_upload()

        # assert
        mocked_chunked_upload_complete.assert_called()


class ChunkedUploadTest(TestCase):
    def test__ChunkedUpload_is_subclass_of_AbstractChunkedUpload(self):
        # assert
        self.assertTrue(issubclass(ChunkedUpload, AbstractChunkedUpload))

    def test__ChunkedUpload_has_a_user_field_as_expected(self):
        # assert
        self.assertTrue(hasattr(ChunkedUpload, "user"))
