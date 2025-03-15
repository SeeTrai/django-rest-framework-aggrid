"""
Tests for the AgGridPagination.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from drf_aggrid import AgGridPagination


class AgGridPaginationTestCase(TestCase):
    """
    Test case for the AgGridPagination.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.pagination = AgGridPagination()
        self.view = APIView()

    def test_is_aggrid_request_with_format(self):
        """
        Test that is_aggrid_request returns True when format=aggrid.
        """
        request = self.factory.get("/", {"format": "aggrid"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_filter(self):
        """
        Test that is_aggrid_request returns True when filter parameter is present.
        """
        request = self.factory.get("/", {"filter": "{}"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_sort(self):
        """
        Test that is_aggrid_request returns True when sort parameter is present.
        """
        request = self.factory.get("/", {"sort": "[]"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_with_pagination(self):
        """
        Test that is_aggrid_request returns True when startRow and endRow parameters are present.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "10"})
        self.assertTrue(self.pagination.is_aggrid_request(request))

    def test_is_aggrid_request_without_aggrid_params(self):
        """
        Test that is_aggrid_request returns False when no ag-grid parameters are present.
        """
        request = self.factory.get("/", {"page": "1"})
        self.assertFalse(self.pagination.is_aggrid_request(request))

    def test_paginate_queryset_with_startrow_endrow(self):
        """
        Test that paginate_queryset paginates the queryset correctly with startRow and endRow.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "2"})
        queryset = ["item1", "item2", "item3", "item4", "item5"]

        # Set up the pagination
        self.pagination.request = request

        # Paginate the queryset
        result = self.pagination.paginate_queryset(queryset, request, self.view)

        # Check that the result is paginated correctly
        self.assertEqual(result, ["item1", "item2"])

        # Check that the counts are set correctly
        self.assertEqual(self.pagination.count, 5)
        self.assertEqual(self.pagination.total_count, 5)

    def test_paginate_queryset_with_startrow_greater_than_count(self):
        """
        Test that paginate_queryset returns an empty list when startRow is greater than the count.
        """
        request = self.factory.get("/", {"startRow": "10", "endRow": "20"})
        queryset = ["item1", "item2", "item3", "item4", "item5"]

        # Set up the pagination
        self.pagination.request = request

        # Paginate the queryset
        result = self.pagination.paginate_queryset(queryset, request, self.view)

        # Check that the result is an empty list
        self.assertEqual(result, [])

        # Check that the counts are set correctly
        self.assertEqual(self.pagination.count, 5)
        self.assertEqual(self.pagination.total_count, 5)

    def test_paginate_queryset_with_endrow_greater_than_count(self):
        """
        Test that paginate_queryset returns the correct slice when endRow is greater than the count.
        """
        request = self.factory.get("/", {"startRow": "3", "endRow": "10"})
        queryset = ["item1", "item2", "item3", "item4", "item5"]

        # Set up the pagination
        self.pagination.request = request

        # Paginate the queryset
        result = self.pagination.paginate_queryset(queryset, request, self.view)

        # Check that the result is paginated correctly
        self.assertEqual(result, ["item4", "item5"])

        # Check that the counts are set correctly
        self.assertEqual(self.pagination.count, 5)
        self.assertEqual(self.pagination.total_count, 5)
