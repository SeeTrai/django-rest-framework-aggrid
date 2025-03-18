"""
Advanced tests for the AgGridPagination class.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import QuerySet
from unittest.mock import MagicMock, patch

from drf_aggrid.pagination import AgGridPagination


class MockQuerySet:
    """
    Mock QuerySet for testing.
    """

    def __init__(self, items):
        self.items = items

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.items[key.start : key.stop]
        return self.items[key]

    def count(self):
        return len(self.items)


class AgGridPaginationAdvancedTestCase(TestCase):
    """
    Advanced test case for the AgGridPagination class.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pagination = AgGridPagination()
        self.view = APIView()

    def test_paginate_queryset_with_non_aggrid_request(self):
        """
        Test that paginate_queryset returns None for non-aggrid requests.
        """
        # Create a request without ag-grid parameters
        request = self.factory.get("/", {"page": "1"})

        # Mock the is_aggrid_request method to return False
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=False):
            queryset = ["item1", "item2", "item3", "item4", "item5"]
            result = self.pagination.paginate_queryset(queryset, request, self.view)
            self.assertIsNone(result)

    def test_paginate_queryset_with_invalid_startrow(self):
        """
        Test that paginate_queryset handles invalid startRow parameter.
        """
        # Create a request with invalid startRow
        request = self.factory.get("/", {"startRow": "invalid", "endRow": "5"})

        # Mock the is_aggrid_request method to return True
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=True):
            queryset = ["item1", "item2", "item3", "item4", "item5"]

            # Set up the pagination
            self.pagination.request = request

            # The actual implementation returns None for invalid parameters
            result = self.pagination.paginate_queryset(queryset, request, self.view)
            self.assertIsNone(result)

    def test_paginate_queryset_with_invalid_endrow(self):
        """
        Test that paginate_queryset handles invalid endRow parameter.
        """
        # Create a request with invalid endRow
        request = self.factory.get("/", {"startRow": "0", "endRow": "invalid"})

        # Mock the is_aggrid_request method to return True
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=True):
            queryset = ["item1", "item2", "item3", "item4", "item5"]

            # Set up the pagination
            self.pagination.request = request

            # The actual implementation returns None for invalid parameters
            result = self.pagination.paginate_queryset(queryset, request, self.view)
            self.assertIsNone(result)

    def test_paginate_queryset_with_negative_startrow(self):
        """
        Test that paginate_queryset handles negative startRow parameter.
        """
        # Create a request with negative startRow
        request = self.factory.get("/", {"startRow": "-1", "endRow": "5"})

        # Mock the is_aggrid_request method to return True
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=True):
            queryset = ["item1", "item2", "item3", "item4", "item5"]

            # Set up the pagination
            self.pagination.request = request

            # The actual implementation treats negative startRow as is
            result = self.pagination.paginate_queryset(queryset, request, self.view)
            # It will return the last item because startRow is -1 and endRow is 5
            self.assertEqual(result, ["item5"])
            self.assertEqual(self.pagination.start_row, -1)
            self.assertEqual(self.pagination.end_row, 5)

    def test_paginate_queryset_with_negative_endrow(self):
        """
        Test that paginate_queryset handles negative endRow parameter.
        """
        # Create a request with negative endRow
        request = self.factory.get("/", {"startRow": "0", "endRow": "-1"})

        # Mock the is_aggrid_request method to return True
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=True):
            queryset = ["item1", "item2", "item3", "item4", "item5"]

            # Set up the pagination
            self.pagination.request = request

            # The actual implementation treats negative endRow as is
            result = self.pagination.paginate_queryset(queryset, request, self.view)
            # It will return items from 0 to -1, which is all but the last item
            self.assertEqual(result, ["item1", "item2", "item3", "item4"])
            self.assertEqual(self.pagination.start_row, 0)
            self.assertEqual(self.pagination.end_row, -1)

    def test_paginate_queryset_with_startrow_greater_than_endrow(self):
        """
        Test that paginate_queryset handles startRow greater than endRow.
        """
        # Create a request with startRow > endRow
        request = self.factory.get("/", {"startRow": "10", "endRow": "5"})

        # Mock the is_aggrid_request method to return True
        with patch.object(AgGridPagination, "is_aggrid_request", return_value=True):
            queryset = ["item1", "item2", "item3", "item4", "item5"]

            # Set up the pagination
            self.pagination.request = request

            # Paginate the queryset
            result = self.pagination.paginate_queryset(queryset, request, self.view)

            # Should return empty list when startRow > endRow
            self.assertEqual(result, [])
            self.assertEqual(self.pagination.start_row, 10)
            self.assertEqual(self.pagination.end_row, 5)

    def test_get_count_with_queryset(self):
        """
        Test that get_count returns the correct count for a queryset.
        """
        # Create a mock queryset
        queryset = MockQuerySet(["item1", "item2", "item3", "item4", "item5"])

        # Get count
        count = self.pagination.get_count(queryset)

        # Should return the count from the queryset
        self.assertEqual(count, 5)

    def test_get_paginated_response_with_format_aggrid(self):
        """
        Test that get_paginated_response returns data in the ag-grid format when format=aggrid.
        """
        # Create a request with format=aggrid
        request = self.factory.get("/", {"format": "aggrid"})
        self.pagination.request = request

        # Set up test data
        data = ["item1", "item2", "item3"]

        # Set total and filtered counts
        self.pagination.total_count = 10
        self.pagination.count = 3

        # Get paginated response
        response = self.pagination.get_paginated_response(data)

        # For format=aggrid, the data should be returned in the ag-grid format
        self.assertIsInstance(response, Response)
        self.assertEqual(
            response.data,
            {
                "rowCount": 3,
                "totalCount": 10,
                "rows": ["item1", "item2", "item3"],
            },
        )

    def test_get_paginated_response_without_format_aggrid(self):
        """
        Test that get_paginated_response formats the response correctly without format=aggrid.
        """
        # Create a request without format=aggrid
        request = self.factory.get("/")
        self.pagination.request = request

        # Set up test data
        data = ["item1", "item2", "item3"]

        # Set total and filtered counts
        self.pagination.total_count = 10
        self.pagination.count = 3

        # Get paginated response
        response = self.pagination.get_paginated_response(data)

        # The response should be formatted for ag-grid
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data["rowCount"], 3)
        self.assertEqual(response.data["totalCount"], 10)
        self.assertEqual(response.data["rows"], data)
