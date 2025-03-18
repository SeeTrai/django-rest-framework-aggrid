"""
Tests for the AgGridPagination.
"""

from django.test import TestCase
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import QuerySet
from unittest.mock import MagicMock
import pytest

from drf_aggrid import AgGridPagination


class MockQuerySet(list):
    """
    Mock QuerySet for testing.
    """

    def __init__(self, items):
        super().__init__(items)
        self.items = items
        self.query = MagicMock()

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args):
        return self

    def count(self):
        return len(self.items)


class SampleView(APIView):
    """
    Sample view for pagination.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])


class SampleViewWithoutPagination(APIView):
    """
    Sample view without pagination.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])


class SampleViewWithCustomStandard(APIView):
    """
    Sample view with custom standard pagination.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])


class AgGridPaginationTestCase(TestCase):
    """
    Test case for the AgGridPagination.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pagination = AgGridPagination()
        self.view = SampleView()

    def test_is_aggrid_request_with_format(self):
        """
        Test that is_aggrid_request returns True when format is aggrid.
        """
        request = self.factory.get("/", {"format": "aggrid"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_filter(self):
        """
        Test that is_aggrid_request returns True when filter is present.
        """
        request = self.factory.get("/", {"filter": "{}"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_sort(self):
        """
        Test that is_aggrid_request returns True when sort is present.
        """
        request = self.factory.get("/", {"sort": "[]"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_pagination(self):
        """
        Test that is_aggrid_request returns True when startRow and endRow are present.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "10"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_none(self):
        """
        Test that is_aggrid_request returns False when no aggrid parameters are present.
        """
        request = self.factory.get("/", {})
        self.assertFalse(self.pagination.is_aggrid_request(request))

    def test_paginate_queryset_with_non_aggrid_request(self):
        """
        Test that paginate_queryset returns None when not an aggrid request.
        """
        request = self.factory.get("/", {})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertIsNone(result)

    def test_paginate_queryset_with_aggrid_request(self):
        """
        Test that paginate_queryset returns a slice of the queryset when an aggrid request.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "2"})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertEqual(result, ["item1", "item2"])

    def test_paginate_queryset_with_startrow_greater_than_count(self):
        """
        Test that paginate_queryset returns an empty list when startRow is greater than count.
        """
        request = self.factory.get("/", {"startRow": "10", "endRow": "20"})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertEqual(result, [])

    def test_paginate_queryset_with_endrow_greater_than_count(self):
        """
        Test that paginate_queryset returns a slice of the queryset when endRow is greater than count.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "10"})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertEqual(result, ["item1", "item2", "item3", "item4", "item5"])

    def test_paginate_queryset_with_invalid_startrow(self):
        """
        Test that paginate_queryset handles invalid startRow.
        """
        request = self.factory.get("/", {"startRow": "invalid", "endRow": "10"})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertIsNone(result)

    def test_paginate_queryset_with_invalid_endrow(self):
        """
        Test that paginate_queryset handles invalid endRow.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "invalid"})
        queryset = self.view.get_queryset()
        result = self.pagination.paginate_queryset(queryset, request, self.view)
        self.assertIsNone(result)

    def test_get_paginated_response(self):
        """
        Test that get_paginated_response returns a Response with the correct format.
        """
        self.pagination.count = 5
        self.pagination.total_count = 10
        data = ["item1", "item2", "item3", "item4", "item5"]
        response = self.pagination.get_paginated_response(data)
        self.assertEqual(
            response.data,
            {
                "rowCount": 5,
                "totalCount": 10,
                "rows": ["item1", "item2", "item3", "item4", "item5"],
            },
        )
