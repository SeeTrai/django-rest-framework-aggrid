"""
Tests for the AgGridFilterBackend.
"""

from django.test import TestCase
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from drf_aggrid import AgGridFilterBackend


class AgGridFilterBackendTestCase(TestCase):
    """
    Test case for the AgGridFilterBackend.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.filter_backend = AgGridFilterBackend()
        self.view = APIView()

    def test_is_aggrid_request_with_format(self):
        """
        Test that is_aggrid_request returns True when format=aggrid.
        """
        request = self.factory.get("/", {"format": "aggrid"})
        self.assertTrue(self.filter_backend.is_aggrid_request(request))

    def test_is_aggrid_request_with_filter(self):
        """
        Test that is_aggrid_request returns True when filter parameter is present.
        """
        request = self.factory.get("/", {"filter": "{}"})
        self.assertTrue(self.filter_backend.is_aggrid_request(request))

    def test_is_aggrid_request_with_sort(self):
        """
        Test that is_aggrid_request returns True when sort parameter is present.
        """
        request = self.factory.get("/", {"sort": "[]"})
        self.assertTrue(self.filter_backend.is_aggrid_request(request))

    def test_is_aggrid_request_with_pagination(self):
        """
        Test that is_aggrid_request returns True when startRow and endRow parameters are present.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "10"})
        self.assertTrue(self.filter_backend.is_aggrid_request(request))

    def test_is_aggrid_request_without_aggrid_params(self):
        """
        Test that is_aggrid_request returns False when no ag-grid parameters are present.
        """
        request = self.factory.get("/", {"page": "1"})
        self.assertFalse(self.filter_backend.is_aggrid_request(request))

    def test_convert_field_name(self):
        """
        Test that convert_field_name converts dot notation to double underscore notation.
        """
        self.assertEqual(
            self.filter_backend.convert_field_name("event_type.name"),
            "event_type__name",
        )
        self.assertEqual(
            self.filter_backend.convert_field_name("user.profile.email"),
            "user__profile__email",
        )
        self.assertEqual(self.filter_backend.convert_field_name("name"), "name")

    def test_get_filter_model(self):
        """
        Test that get_filter_model parses the filter parameter correctly.
        """
        request = self.factory.get(
            "/",
            {
                "filter": '{"name":{"filterType":"text","type":"contains","filter":"test"}}'
            },
        )
        filter_model = self.filter_backend.get_filter_model(request)
        self.assertEqual(
            filter_model,
            {"name": {"filterType": "text", "type": "contains", "filter": "test"}},
        )

    def test_get_sort_model(self):
        """
        Test that get_sort_model parses the sort parameter correctly.
        """
        request = self.factory.get("/", {"sort": '[{"colId":"name","sort":"asc"}]'})
        sort_model = self.filter_backend.get_sort_model(request)
        self.assertEqual(sort_model, [{"colId": "name", "sort": "asc"}])

    def test_get_pagination_params(self):
        """
        Test that get_pagination_params parses the startRow and endRow parameters correctly.
        """
        request = self.factory.get("/", {"startRow": "0", "endRow": "10"})
        start_row, end_row = self.filter_backend.get_pagination_params(request)
        self.assertEqual(start_row, 0)
        self.assertEqual(end_row, 10)

    def test_build_ordering(self):
        """
        Test that build_ordering builds the ordering list correctly.
        """
        sort_model = [
            {"colId": "name", "sort": "asc"},
            {"colId": "event_type.name", "sort": "desc"},
        ]
        ordering = self.filter_backend.build_ordering(sort_model)
        self.assertEqual(ordering, ["name", "-event_type__name"])
