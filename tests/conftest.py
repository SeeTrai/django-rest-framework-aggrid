"""
Pytest configuration for testing drf-aggrid.
"""

import pytest
from django.http import HttpRequest
from drf_aggrid.pagination import AgGridPagination


# Patch the HttpRequest class to add query_params property
def pytest_configure():
    """
    Configure pytest for testing drf-aggrid.
    """
    # Add query_params property to HttpRequest
    HttpRequest.query_params = property(lambda self: self.GET)

    # Patch the get_count method for tests
    original_get_count = AgGridPagination.get_count

    def patched_get_count(self, queryset):
        """
        Patched get_count method that works with lists.
        """
        if isinstance(queryset, list):
            return len(queryset)
        return original_get_count(self, queryset)

    AgGridPagination.get_count = patched_get_count
