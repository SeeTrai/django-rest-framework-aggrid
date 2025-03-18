"""
Tests for the AutoAgGridPaginationMixin.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.pagination import PageNumberPagination
from unittest.mock import MagicMock

from drf_aggrid.mixins import AgGridAutoPaginationMixin
from drf_aggrid.pagination import AgGridPagination


class AutoAgGridPaginationMixinTestCase(TestCase):
    """
    Test case for AutoAgGridPaginationMixin.
    """

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_standard_request_uses_original_pagination(self):
        """
        Test that a standard request uses the original pagination class.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = PageNumberPagination
        view._original_pagination_class = None

        # Create a request
        request = self.factory.get("/")

        # Call initial
        view.initial(request)

        # Check that the pagination class is the original one
        self.assertEqual(view.pagination_class, PageNumberPagination)

    def test_aggrid_request_uses_aggrid_pagination(self):
        """
        Test that an ag-grid request uses AgGridPagination.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = PageNumberPagination
        view._original_pagination_class = PageNumberPagination

        # Create a request with format=aggrid
        request = self.factory.get("/", {"format": "aggrid"})

        # Call initial
        view.initial(request)

        # Check that the pagination class is AgGridPagination
        self.assertEqual(view.pagination_class, AgGridPagination)

    def test_view_without_pagination_class(self):
        """
        Test that a view without a pagination class still works.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = None
        view._original_pagination_class = None

        # Create a request
        request = self.factory.get("/")

        # Call initial
        view.initial(request)

        # Check that the pagination class is None
        self.assertIsNone(view.pagination_class)

    def test_view_without_pagination_class_with_aggrid_request(self):
        """
        Test that a view without a pagination class uses AgGridPagination for ag-grid requests.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = None
        view._original_pagination_class = None

        # Create a request with format=aggrid
        request = self.factory.get("/", {"format": "aggrid"})

        # Call initial
        view.initial(request)

        # Check that the pagination class is AgGridPagination
        self.assertEqual(view.pagination_class, AgGridPagination)

    def test_view_with_custom_standard_pagination(self):
        """
        Test that a view with a custom standard pagination class uses it for standard requests.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = PageNumberPagination
        view._original_pagination_class = PageNumberPagination
        view.standard_pagination_class = PageNumberPagination

        # Create a request
        request = self.factory.get("/")

        # Call initial
        view.initial(request)

        # Check that the pagination class is the custom standard one
        self.assertEqual(view.pagination_class, PageNumberPagination)

    def test_original_pagination_class_restored(self):
        """
        Test that the original pagination class is restored after the response is generated.
        """
        # Create a view instance with the mixin
        view = AgGridAutoPaginationMixin()
        view.pagination_class = PageNumberPagination
        view._original_pagination_class = PageNumberPagination

        # Create a request with format=aggrid
        request = self.factory.get("/", {"format": "aggrid"})

        # Call initial to set the pagination class to AgGridPagination
        view.initial(request)

        # Check that the pagination class is AgGridPagination
        self.assertEqual(view.pagination_class, AgGridPagination)

        # Create a mock response
        response = MagicMock()

        # Call finalize_response to restore the original pagination class
        view.finalize_response(request, response)

        # Check that the pagination class is restored to the original
        self.assertEqual(view.pagination_class, PageNumberPagination)
