"""
Final tests for the AgGridFilterBackend to cover remaining uncovered lines.
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


class FinalTestView(APIView):
    """
    Test view for final tests.
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
        return getattr(self, "ag_grid_filter_lookup", {})


class AgGridFilterBackendFinalTestCase(TestCase):
    """
    Final test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = FinalTestView()

    def test_filter_queryset_with_invalid_json(self):
        """
        Test that filter_queryset handles invalid JSON.
        """
        # Create a request with invalid JSON
        request = self.factory.get(
            "/",
            {
                "format": "aggrid",
                "filter": "{invalid_json",
                "sort": "[{invalid_json",
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

    def test_filter_queryset_with_non_aggrid_request(self):
        """
        Test that filter_queryset handles non-aggrid request.
        """
        # Create a non-aggrid request
        request = self.factory.get(
            "/",
            {
                "format": "json",
                "filter": "{}",
                "sort": "[]",
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

    def test_filter_queryset_with_custom_filter_lookup(self):
        """
        Test that filter_queryset handles custom filter lookup.
        """
        # Create a request with filter
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

        # Define a custom filter function that uses a lookup
        def custom_filter_with_lookup(field, filter_condition, queryset, request, view):
            # This is a simple custom filter function that just returns the queryset
            return queryset

        # Set custom filter function on the view
        self.view.ag_grid_filter_lookup = {"name": custom_filter_with_lookup}

        # Apply filtering
        filtered_queryset = self.filter_backend.filter_queryset(
            request, queryset, self.view
        )

        # Check that the queryset is returned
        self.assertEqual(filtered_queryset, queryset)

    def test_filter_queryset_with_custom_filter_function(self):
        """
        Test that filter_queryset handles custom filter function.
        """
        # Create a request with filter
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

        # Define a custom filter function
        def custom_filter(field, filter_condition, queryset, request, view):
            return queryset

        # Set custom filter function on the view
        self.view.ag_grid_filter_lookup = {"name": custom_filter}

        # Apply filtering
        filtered_queryset = self.filter_backend.filter_queryset(
            request, queryset, self.view
        )

        # Check that the queryset is returned
        self.assertEqual(filtered_queryset, queryset)

    def test_build_filter_query_with_text_filter_not_contains(self):
        """
        Test that build_filter_query handles text filter with not contains.
        """
        # Text filter with not contains
        filter_model = {
            "name": {"filterType": "text", "type": "notContains", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the not contains filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_text_filter_equals(self):
        """
        Test that build_filter_query handles text filter with equals.
        """
        # Text filter with equals
        filter_model = {
            "name": {"filterType": "text", "type": "equals", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the equals filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_text_filter_not_equals(self):
        """
        Test that build_filter_query handles text filter with not equals.
        """
        # Text filter with not equals
        filter_model = {
            "name": {"filterType": "text", "type": "notEqual", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the not equals filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_text_filter_starts_with(self):
        """
        Test that build_filter_query handles text filter with starts with.
        """
        # Text filter with starts with
        filter_model = {
            "name": {"filterType": "text", "type": "startsWith", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the starts with filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_text_filter_ends_with(self):
        """
        Test that build_filter_query handles text filter with ends with.
        """
        # Text filter with ends with
        filter_model = {
            "name": {"filterType": "text", "type": "endsWith", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the ends with filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_number_filter_greater_than(self):
        """
        Test that build_filter_query handles number filter with greater than.
        """
        # Number filter with greater than
        filter_model = {
            "age": {"filterType": "number", "type": "greaterThan", "filter": 18}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the greater than filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_number_filter_greater_than_or_equal(self):
        """
        Test that build_filter_query handles number filter with greater than or equal.
        """
        # Number filter with greater than or equal
        filter_model = {
            "age": {"filterType": "number", "type": "greaterThanOrEqual", "filter": 18}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the greater than or equal filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_number_filter_less_than(self):
        """
        Test that build_filter_query handles number filter with less than.
        """
        # Number filter with less than
        filter_model = {
            "age": {"filterType": "number", "type": "lessThan", "filter": 18}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the less than filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_number_filter_less_than_or_equal(self):
        """
        Test that build_filter_query handles number filter with less than or equal.
        """
        # Number filter with less than or equal
        filter_model = {
            "age": {"filterType": "number", "type": "lessThanOrEqual", "filter": 18}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the less than or equal filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_number_filter_in_range(self):
        """
        Test that build_filter_query handles number filter with in range.
        """
        # Number filter with in range
        filter_model = {
            "age": {
                "filterType": "number",
                "type": "inRange",
                "filter": 18,
                "filterTo": 30,
            }
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object with the in range filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)
