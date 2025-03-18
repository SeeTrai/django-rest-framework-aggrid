"""
Tests for the AgGridPaginationMixin.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
import pytest

from drf_aggrid import AgGridPaginationMixin


class SampleView(APIView, AgGridPaginationMixin):
    """
    Sample view for mixins.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return ["item1", "item2", "item3", "item4", "item5"]


class AgGridPaginationMixinTestCase(TestCase):
    """
    Test case for the AgGridPaginationMixin.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = SampleView()

    def test_get_paginated_response_with_aggrid_format(self):
        """
        Test that get_paginated_response returns data as is when format=aggrid.
        """
        # Create a request with format=aggrid
        request = self.factory.get("/", {"format": "aggrid"})
        self.view.request = request

        # Set up test data
        data = ["item1", "item2", "item3"]

        # Set total and filtered counts
        setattr(self.view, "_ag_grid_total_count", 10)
        setattr(self.view, "_ag_grid_filtered_count", 3)

        # Get paginated response
        response = self.view.get_paginated_response(data)

        # For format=aggrid, the data should be returned as is
        self.assertEqual(response, data)

    def test_get_paginated_response_without_aggrid_format(self):
        """
        Test that get_paginated_response formats the response correctly without format=aggrid.
        """
        # Create a request without format=aggrid
        request = self.factory.get("/")
        self.view.request = request

        # Set up test data
        data = ["item1", "item2", "item3"]

        # Set total and filtered counts
        setattr(self.view, "_ag_grid_total_count", 10)
        setattr(self.view, "_ag_grid_filtered_count", 3)

        # Get paginated response
        response = self.view.get_paginated_response(data)

        # The response should be formatted for ag-grid
        self.assertIsInstance(response, dict)
        self.assertEqual(response["rowCount"], 3)
        self.assertEqual(response["totalCount"], 10)
        self.assertEqual(response["rows"], data)

    def test_get_paginated_response_without_request(self):
        """
        Test that get_paginated_response works without a request.
        """
        # Set up test data
        data = ["item1", "item2", "item3"]

        # Set total and filtered counts
        setattr(self.view, "_ag_grid_total_count", 10)
        setattr(self.view, "_ag_grid_filtered_count", 3)

        # Get paginated response without setting request
        self.view.request = None
        response = self.view.get_paginated_response(data)

        # The response should be formatted for ag-grid
        self.assertIsInstance(response, dict)
        self.assertEqual(response["rowCount"], 3)
        self.assertEqual(response["totalCount"], 10)
        self.assertEqual(response["rows"], data)

    def test_get_paginated_response_without_counts(self):
        """
        Test that get_paginated_response works without counts.
        """
        # Create a request without format=aggrid
        request = self.factory.get("/")
        self.view.request = request

        # Set up test data
        data = ["item1", "item2", "item3"]

        # Don't set total and filtered counts
        if hasattr(self.view, "_ag_grid_total_count"):
            delattr(self.view, "_ag_grid_total_count")
        if hasattr(self.view, "_ag_grid_filtered_count"):
            delattr(self.view, "_ag_grid_filtered_count")

        # Get paginated response
        response = self.view.get_paginated_response(data)

        # The response should be formatted for ag-grid with default counts
        self.assertIsInstance(response, dict)
        self.assertEqual(response["rowCount"], 0)
        self.assertEqual(response["totalCount"], 0)
        self.assertEqual(response["rows"], data)
