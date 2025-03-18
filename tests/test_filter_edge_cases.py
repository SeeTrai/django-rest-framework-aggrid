"""
Edge case tests for the AgGridFilterBackend.
"""

import json
from django.test import TestCase
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q, QuerySet
from unittest.mock import MagicMock, patch

from drf_aggrid import AgGridFilterBackend


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


class EdgeCaseView(APIView):
    """
    Test view for edge cases.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])


class AgGridFilterBackendEdgeCaseTestCase(TestCase):
    """
    Edge case test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = EdgeCaseView()

    def test_filter_queryset_with_empty_filter_model(self):
        """
        Test that filter_queryset handles empty filter model.
        """
        # Create a request with empty filter
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": "{}",
                "sort": '[{"colId":"name","sort":"asc"}]',
                "startRow": "0",
                "endRow": "10",
            },
        )

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filtering
        filtered_queryset = self.filter_backend.filter_queryset(
            request, queryset, self.view
        )

        # Check that the queryset is returned as is
        self.assertEqual(filtered_queryset, queryset)

        # Check that the view has the total and filtered counts
        self.assertEqual(getattr(self.view, "_ag_grid_total_count", None), 5)
        self.assertEqual(getattr(self.view, "_ag_grid_filtered_count", None), 5)

    def test_filter_queryset_with_null_filter_model(self):
        """
        Test that filter_queryset handles null filter model.
        """
        # Create a request with null filter
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": "null",
                "sort": '[{"colId":"name","sort":"asc"}]',
                "startRow": "0",
                "endRow": "10",
            },
        )

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filtering
        filtered_queryset = self.filter_backend.filter_queryset(
            request, queryset, self.view
        )

        # Check that the queryset is returned as is
        self.assertEqual(filtered_queryset, queryset)

        # Check that the view has the total and filtered counts
        self.assertEqual(getattr(self.view, "_ag_grid_total_count", None), 5)
        self.assertEqual(getattr(self.view, "_ag_grid_filtered_count", None), 5)

    def test_filter_queryset_with_empty_sort_model(self):
        """
        Test that filter_queryset handles empty sort model.
        """
        # Create a request with empty sort
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": '{"name":{"filterType":"text","type":"contains","filter":"test"}}',
                "sort": "[]",
                "startRow": "0",
                "endRow": "10",
            },
        )

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filtering
        with patch.object(AgGridFilterBackend, "apply_filters", return_value=queryset):
            filtered_queryset = self.filter_backend.filter_queryset(
                request, queryset, self.view
            )

            # Check that the queryset is returned
            self.assertEqual(filtered_queryset, queryset)

    def test_filter_queryset_with_null_sort_model(self):
        """
        Test that filter_queryset handles null sort model.
        """
        # Create a request with null sort
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": '{"name":{"filterType":"text","type":"contains","filter":"test"}}',
                "sort": "null",
                "startRow": "0",
                "endRow": "10",
            },
        )

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filtering
        with patch.object(AgGridFilterBackend, "apply_filters", return_value=queryset):
            filtered_queryset = self.filter_backend.filter_queryset(
                request, queryset, self.view
            )

            # Check that the queryset is returned
            self.assertEqual(filtered_queryset, queryset)

    def test_build_filter_query_with_empty_filter_model(self):
        """
        Test that build_filter_query handles empty filter model.
        """
        # Empty filter model
        filter_model = {}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return None for empty filter model
        self.assertIsNone(q_obj)

    def test_build_ordering_with_invalid_sort_model(self):
        """
        Test that build_ordering handles invalid sort model.
        """
        # Invalid sort model (missing colId)
        sort_model = [{"sort": "asc"}]

        # Build ordering
        ordering = self.filter_backend.build_ordering(sort_model)

        # Should return empty list for invalid sort model
        self.assertEqual(ordering, [])

    def test_get_pagination_params_with_invalid_values(self):
        """
        Test that get_pagination_params handles invalid values.
        """
        # Create a request with non-numeric values
        request = self.factory.get("/", {"startRow": "abc", "endRow": "def"})

        # Get pagination parameters
        start_row, end_row = self.filter_backend.get_pagination_params(request)

        # Should return None, None for invalid values
        self.assertIsNone(start_row)
        self.assertIsNone(end_row)

    def test_apply_filters_with_empty_filter_model(self):
        """
        Test that apply_filters handles empty filter model.
        """
        # Empty filter model
        filter_model = {}

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filters
        filtered_queryset = self.filter_backend.apply_filters(
            filter_model, queryset, {}, None, self.view
        )

        # Should return the queryset as is
        self.assertEqual(filtered_queryset, queryset)
