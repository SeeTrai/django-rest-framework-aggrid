"""
Special case tests for the AgGridFilterBackend.
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


class SpecialCaseView(APIView):
    """
    Test view for special cases.
    """

    def get_queryset(self):
        """
        Return a mock queryset for testing.
        """
        return MockQuerySet(["item1", "item2", "item3", "item4", "item5"])


class AgGridFilterBackendSpecialCaseTestCase(TestCase):
    """
    Special case test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = SpecialCaseView()

    def test_build_filter_query_with_set_filter_with_empty_values(self):
        """
        Test that build_filter_query handles set filter with empty values.
        """
        # Set filter with empty values
        filter_model = {"name": {"filterType": "set", "values": []}}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns an empty Q object, not None
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q()))

    def test_build_filter_query_with_number_filter_with_empty_values(self):
        """
        Test that build_filter_query handles number filter with empty values.
        """
        # Number filter with empty values
        filter_model = {"age": {"filterType": "number", "type": "equals", "filter": ""}}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns a Q object with the empty value
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q(age="")))

    def test_build_filter_query_with_date_filter_with_empty_values(self):
        """
        Test that build_filter_query handles date filter with empty values.
        """
        # Date filter with empty values
        filter_model = {
            "created_at": {"filterType": "date", "type": "equals", "dateFrom": ""}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns an empty Q object
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q()))

    def test_build_filter_query_with_text_filter_with_empty_values(self):
        """
        Test that build_filter_query handles text filter with empty values.
        """
        # Text filter with empty values
        filter_model = {
            "name": {"filterType": "text", "type": "contains", "filter": ""}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns an empty Q object
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q()))

    def test_build_filter_query_with_boolean_filter_with_empty_values(self):
        """
        Test that build_filter_query handles boolean filter with empty values.
        """
        # Boolean filter with empty values
        filter_model = {"is_active": {"filterType": "boolean", "value": None}}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns an empty Q object
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q()))

    def test_build_filter_query_with_multiple_filters_some_empty(self):
        """
        Test that build_filter_query handles multiple filters with some empty.
        """
        # Multiple filters with some empty
        filter_model = {
            "name": {"filterType": "text", "type": "contains", "filter": "test"},
            "age": {"filterType": "number", "type": "equals", "filter": ""},
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # Should return a Q object for the non-empty filter
        self.assertIsNotNone(q_obj)
        self.assertIsInstance(q_obj, Q)

    def test_build_filter_query_with_invalid_filter_type(self):
        """
        Test that build_filter_query handles invalid filter type.
        """
        # Invalid filter type
        filter_model = {
            "name": {"filterType": "invalid", "type": "contains", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns None for invalid filter type
        self.assertIsNone(q_obj)

    def test_build_filter_query_with_missing_filter_type(self):
        """
        Test that build_filter_query handles missing filter type.
        """
        # Missing filter type
        filter_model = {"name": {"type": "contains", "filter": "test"}}

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns None for missing filter type
        self.assertIsNone(q_obj)

    def test_build_filter_query_with_missing_filter_field(self):
        """
        Test that build_filter_query handles missing filter field.
        """
        # Missing filter field
        filter_model = {
            "": {"filterType": "text", "type": "contains", "filter": "test"}
        }

        # Build filter query
        q_obj = self.filter_backend.build_filter_query(filter_model)

        # The implementation returns a Q object with the empty field
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), str(Q(**{"__icontains": "test"})))

    def test_apply_filters_with_custom_filter_function(self):
        """
        Test that apply_filters handles custom filter function.
        """

        # Define a custom filter function
        def custom_filter(field, filter_condition, queryset, request, view):
            # This is a simple custom filter function that just returns the queryset
            return queryset

        # Filter model
        filter_model = {
            "name": {"filterType": "text", "type": "contains", "filter": "test"}
        }

        # Custom filters dictionary with callable function
        custom_filters = {"name": custom_filter}

        # Get the queryset
        queryset = self.view.get_queryset()

        # Apply filters with custom filter function
        filtered_queryset = self.filter_backend.apply_filters(
            filter_model, queryset, custom_filters, None, self.view
        )

        # Should return the filtered queryset
        self.assertEqual(filtered_queryset, queryset)
