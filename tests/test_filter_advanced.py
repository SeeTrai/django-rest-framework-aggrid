"""
Advanced tests for the AgGridFilterBackend.
"""

import json
from django.test import TestCase
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from drf_aggrid import AgGridFilterBackend


class CustomFiltersView(APIView):
    """
    Test view with custom filters.
    """

    def get_aggrid_custom_filters(self):
        """
        Return custom filters for testing.
        """
        return {
            "custom_field": lambda value, request: Q(name__contains=value),
            "complex_field": lambda value, request: Q(name__startswith=value)
            | Q(description__contains=value),
        }


class AgGridFilterBackendAdvancedTestCase(TestCase):
    """
    Advanced test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = APIView()
        self.custom_view = CustomFiltersView()

    def test_get_custom_filters(self):
        """
        Test that get_custom_filters returns custom filters from the view.
        """
        custom_filters = self.filter_backend.get_custom_filters(self.custom_view)
        self.assertIsInstance(custom_filters, dict)
        self.assertIn("custom_field", custom_filters)
        self.assertIn("complex_field", custom_filters)

        # Test with a view that doesn't have custom filters
        custom_filters = self.filter_backend.get_custom_filters(self.view)
        self.assertEqual(custom_filters, {})

    def test_convert_field_name(self):
        """
        Test that convert_field_name converts dot notation to Django ORM notation.
        """
        # Test simple field name
        field_name = "name"
        converted = self.filter_backend.convert_field_name(field_name)
        self.assertEqual(converted, "name")

        # Test nested field name
        field_name = "user.profile.name"
        converted = self.filter_backend.convert_field_name(field_name)
        self.assertEqual(converted, "user__profile__name")

        # Test with already converted field name
        field_name = "user__profile__name"
        converted = self.filter_backend.convert_field_name(field_name)
        self.assertEqual(converted, "user__profile__name")

    def test_build_text_filter_contains(self):
        """
        Test that _build_text_filter builds a contains filter correctly.
        """
        field = "name"
        filter_condition = {"type": "contains", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('name__icontains', 'test'))")

    def test_build_text_filter_not_contains(self):
        """
        Test that _build_text_filter builds a not contains filter correctly.
        """
        field = "name"
        filter_condition = {"type": "notContains", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(NOT (AND: ('name__icontains', 'test')))")

    def test_build_text_filter_equals(self):
        """
        Test that _build_text_filter builds an equals filter correctly.
        """
        field = "name"
        filter_condition = {"type": "equals", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('name__exact', 'test'))")

    def test_build_text_filter_not_equals(self):
        """
        Test that _build_text_filter builds a not equals filter correctly.
        """
        field = "name"
        filter_condition = {"type": "notEqual", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(NOT (AND: ('name__exact', 'test')))")

    def test_build_text_filter_starts_with(self):
        """
        Test that _build_text_filter builds a starts with filter correctly.
        """
        field = "name"
        filter_condition = {"type": "startsWith", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('name__istartswith', 'test'))")

    def test_build_text_filter_ends_with(self):
        """
        Test that _build_text_filter builds an ends with filter correctly.
        """
        field = "name"
        filter_condition = {"type": "endsWith", "filter": "test"}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('name__iendswith', 'test'))")

    def test_build_text_filter_blank(self):
        """
        Test that _build_text_filter handles blank filter values.
        """
        field = "name"
        filter_condition = {"type": "contains", "filter": ""}
        q_obj = self.filter_backend._build_text_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: )")

    def test_build_number_filter_equals(self):
        """
        Test that _build_number_filter builds an equals filter correctly.
        """
        field = "age"
        filter_condition = {"type": "equals", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age', 25))")

    def test_build_number_filter_not_equals(self):
        """
        Test that _build_number_filter builds a not equals filter correctly.
        """
        field = "age"
        filter_condition = {"type": "notEqual", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(NOT (AND: ('age', 25)))")

    def test_build_number_filter_greater_than(self):
        """
        Test that _build_number_filter builds a greater than filter correctly.
        """
        field = "age"
        filter_condition = {"type": "greaterThan", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age__gt', 25))")

    def test_build_number_filter_greater_than_or_equal(self):
        """
        Test that _build_number_filter builds a greater than or equal filter correctly.
        """
        field = "age"
        filter_condition = {"type": "greaterThanOrEqual", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age__gte', 25))")

    def test_build_number_filter_less_than(self):
        """
        Test that _build_number_filter builds a less than filter correctly.
        """
        field = "age"
        filter_condition = {"type": "lessThan", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age__lt', 25))")

    def test_build_number_filter_less_than_or_equal(self):
        """
        Test that _build_number_filter builds a less than or equal filter correctly.
        """
        field = "age"
        filter_condition = {"type": "lessThanOrEqual", "filter": 25}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age__lte', 25))")

    def test_build_number_filter_in_range(self):
        """
        Test that _build_number_filter builds an in range filter correctly.
        """
        field = "age"
        filter_condition = {"type": "inRange", "filter": 25, "filterTo": 30}
        q_obj = self.filter_backend._build_number_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('age__gte', 25), ('age__lte', 30))")

    def test_build_date_filter_equals(self):
        """
        Test that _build_date_filter builds an equals filter correctly.
        """
        field = "created_at"
        filter_condition = {"type": "equals", "dateFrom": "2023-01-01"}
        q_obj = self.filter_backend._build_date_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('created_at__date', '2023-01-01'))")

    def test_build_date_filter_not_equals(self):
        """
        Test that _build_date_filter builds a not equals filter correctly.
        """
        field = "created_at"
        filter_condition = {"type": "notEqual", "dateFrom": "2023-01-01"}
        q_obj = self.filter_backend._build_date_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(NOT (AND: ('created_at__date', '2023-01-01')))")

    def test_build_date_filter_greater_than(self):
        """
        Test that _build_date_filter builds a greater than filter correctly.
        """
        field = "created_at"
        filter_condition = {"type": "greaterThan", "dateFrom": "2023-01-01"}
        q_obj = self.filter_backend._build_date_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('created_at__gt', '2023-01-01'))")

    def test_build_date_filter_less_than(self):
        """
        Test that _build_date_filter builds a less than filter correctly.
        """
        field = "created_at"
        filter_condition = {"type": "lessThan", "dateFrom": "2023-01-01"}
        q_obj = self.filter_backend._build_date_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('created_at__lt', '2023-01-01'))")

    def test_build_date_filter_in_range(self):
        """
        Test that _build_date_filter builds an in range filter correctly.
        """
        field = "created_at"
        filter_condition = {
            "type": "inRange",
            "dateFrom": "2023-01-01",
            "dateTo": "2023-01-31",
        }
        q_obj = self.filter_backend._build_date_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(
            str(q_obj),
            "(AND: ('created_at__gte', '2023-01-01'), ('created_at__lte', '2023-01-31'))",
        )

    def test_build_set_filter(self):
        """
        Test that _build_set_filter builds a set filter correctly.
        """
        field = "status"
        filter_condition = {"values": ["active", "pending"]}
        q_obj = self.filter_backend._build_set_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: ('status__in', ['active', 'pending']))")

    def test_build_boolean_filter(self):
        """
        Test that _build_boolean_filter builds a boolean filter correctly.
        """
        field = "is_active"
        filter_condition = {"value": True}
        q_obj = self.filter_backend._build_boolean_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: )")

        # Test with false value
        filter_condition = {"value": False}
        q_obj = self.filter_backend._build_boolean_filter(field, filter_condition)
        self.assertIsInstance(q_obj, Q)
        self.assertEqual(str(q_obj), "(AND: )")

    def test_build_ordering(self):
        """
        Test that build_ordering builds ordering correctly.
        """
        # Test single sort
        sort_model = [{"colId": "name", "sort": "asc"}]
        ordering = self.filter_backend.build_ordering(sort_model)
        self.assertEqual(ordering, ["name"])

        # Test multiple sort
        sort_model = [
            {"colId": "name", "sort": "asc"},
            {"colId": "age", "sort": "desc"},
        ]
        ordering = self.filter_backend.build_ordering(sort_model)
        self.assertEqual(ordering, ["name", "-age"])

        # Test with nested field
        sort_model = [{"colId": "user.profile.name", "sort": "asc"}]
        ordering = self.filter_backend.build_ordering(sort_model)
        self.assertEqual(ordering, ["user__profile__name"])

        # Test with empty sort model
        sort_model = []
        ordering = self.filter_backend.build_ordering(sort_model)
        self.assertEqual(ordering, [])
