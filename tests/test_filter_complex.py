"""
Complex tests for the AgGridFilterBackend.
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


class ComplexFilterView(APIView):
    """
    Test view with complex filter setup.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])

    def get_aggrid_custom_filters(self):
        """
        Return custom filters for testing.
        """
        return {
            "custom_field": lambda value, request: Q(name__contains=value),
            "complex_field": lambda value, request: Q(name__startswith=value)
            | Q(description__contains=value),
        }


class AgGridFilterBackendComplexTestCase(TestCase):
    """
    Complex test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = ComplexFilterView()

    def test_filter_queryset_with_aggrid_request(self):
        """
        Test that filter_queryset processes ag-grid request correctly.
        """
        # Create a request with ag-grid parameters
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": '{"name":{"filterType":"text","type":"contains","filter":"test"}}',
                "sort": '[{"colId":"name","sort":"asc"}]',
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

            # Check that the view has the total and filtered counts
            self.assertEqual(getattr(self.view, "_ag_grid_total_count", None), 5)
            self.assertEqual(getattr(self.view, "_ag_grid_filtered_count", None), 5)

            # Check that the queryset is returned
            self.assertEqual(filtered_queryset, queryset)

    def test_filter_queryset_with_non_aggrid_request(self):
        """
        Test that filter_queryset returns queryset as is for non-ag-grid request.
        """
        # Create a request without ag-grid parameters
        request = self.factory.get("/", {"page": "1"})

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filtering
        filtered_queryset = self.filter_backend.filter_queryset(
            request, queryset, self.view
        )

        # Check that the queryset is returned as is
        self.assertEqual(filtered_queryset, queryset)

    def test_build_filter_query_with_complex_filter(self):
        """
        Test that build_filter_query handles complex filter conditions.
        """
        # Complex filter with multiple conditions
        filter_model = {
            "name": {"filterType": "text", "type": "contains", "filter": "test"},
            "age": {"filterType": "number", "type": "greaterThan", "filter": 25},
            "status": {"filterType": "set", "values": ["active", "pending"]},
            "created_at": {
                "filterType": "date",
                "type": "inRange",
                "dateFrom": "2023-01-01",
                "dateTo": "2023-01-31",
            },
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Check that a Q object is returned
        self.assertIsInstance(q_obj, Q)

        # The Q object should have multiple conditions
        self.assertIn("name__icontains", str(q_obj))
        self.assertIn("age__gt", str(q_obj))
        self.assertIn("status__in", str(q_obj))
        self.assertIn("created_at__gte", str(q_obj))
        self.assertIn("created_at__lte", str(q_obj))

    def test_apply_filters_with_custom_filters(self):
        """
        Test that apply_filters applies custom filters correctly.
        """

        # Create a mock custom filter function with the correct signature
        def mock_custom_filter(field, filter_condition, queryset, request, view):
            return queryset

        # Filter model with a custom field
        filter_model = {
            "custom_field": {"filterType": "text", "type": "contains", "filter": "test"}
        }

        # Get the queryset
        queryset = self.view.get_queryset()

        # Create custom filters dictionary with the mock function
        custom_filters = {"custom_field": mock_custom_filter}

        # Create a request
        request = self.factory.get("/")

        # Apply filters
        filtered_queryset = self.filter_backend.apply_filters(
            filter_model, queryset, custom_filters, request, self.view
        )

        # Check that the queryset is returned
        self.assertEqual(filtered_queryset, queryset)

    def test_build_filter_query_with_unknown_filter_type(self):
        """
        Test that build_filter_query handles unknown filter types.
        """
        # Filter with unknown type
        filter_model = {"name": {"filterType": "unknown", "filter": "test"}}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The actual implementation returns None for unknown filter types
        self.assertIsNone(q_obj)

    def test_get_filter_model_with_invalid_json(self):
        """
        Test that get_filter_model handles invalid JSON.
        """
        # Create a request with invalid JSON
        request = self.factory.get("/", {"filter": "invalid json"})

        # Get filter model
        filter_model = self.filter_backend.get_filter_model(request)

        # Should return None
        self.assertIsNone(filter_model)

    def test_get_sort_model_with_invalid_json(self):
        """
        Test that get_sort_model handles invalid JSON.
        """
        # Create a request with invalid JSON
        request = self.factory.get("/", {"sort": "invalid json"})

        # Get sort model
        sort_model = self.filter_backend.get_sort_model(request)

        # Should return None
        self.assertIsNone(sort_model)

    def test_get_pagination_params_with_missing_params(self):
        """
        Test that get_pagination_params handles missing parameters.
        """
        # Create a request without pagination parameters
        request = self.factory.get("/")

        # Get pagination parameters
        start_row, end_row = self.filter_backend.get_pagination_params(request)

        # Should return None, None
        self.assertIsNone(start_row)
        self.assertIsNone(end_row)
