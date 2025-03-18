"""
Mixins for ag-grid integration with Django REST Framework.
"""

from rest_framework.response import Response
import logging
from rest_framework.pagination import PageNumberPagination

from .pagination import AgGridPagination

logger = logging.getLogger(__name__)


class AgGridPaginationMixin:
    """
    Mixin for views that use the AgGridFilterBackend.

    This mixin adds methods for handling ag-grid pagination and response formatting.
    """

    def get_paginated_response(self, data):
        """
        Return a paginated response in the format expected by ag-grid.
        """
        # Get total and filtered counts
        total_count = getattr(self, "_ag_grid_total_count", 0)
        filtered_count = getattr(self, "_ag_grid_filtered_count", 0)

        # Check if the request format is 'aggrid'
        request = getattr(self, "request", None)
        if request:
            format_param = request.query_params.get("format")
            if format_param and format_param.lower() == "aggrid":
                # For format=aggrid, let the renderer handle the formatting
                return data

        # For direct ag-grid parameters, format the response here
        return {"rowCount": filtered_count, "totalCount": total_count, "rows": data}


class AgGridAutoPaginationMixin:
    """
    Mixin that automatically switches between standard pagination and AgGridPagination
    based on the request format.

    Usage:
    ```
    class MyViewSet(AutoAgGridPaginationMixin, viewsets.ModelViewSet):
        # Your view implementation
        # Define standard_pagination_class if you want to override the default
        standard_pagination_class = PageNumberPagination
    ```
    """

    # The pagination class to use for ag-grid requests
    aggrid_pagination_class = AgGridPagination

    # The pagination class to use for standard requests
    # Can be overridden in subclasses
    standard_pagination_class = None

    # Store the original pagination class
    _original_pagination_class = None

    def initial(self, request, *args, **kwargs):
        """
        Runs before the view method is called.
        Dynamically sets the pagination class based on the request format.
        """
        # Store the original pagination class if not already stored
        if (
            not hasattr(self, "_original_pagination_class")
            or self._original_pagination_class is None
        ):
            self._original_pagination_class = getattr(self, "pagination_class", None)

        # Determine if this is an ag-grid request
        is_aggrid = request.query_params.get("format") == "aggrid"

        # Set the appropriate pagination class
        if is_aggrid:
            self.pagination_class = self.aggrid_pagination_class
        else:
            # Use the standard pagination class if specified, otherwise use the original
            self.pagination_class = (
                self.standard_pagination_class or self._original_pagination_class
            )

        # Call the parent initial method if it exists
        parent_initial = getattr(super(), "initial", None)
        if parent_initial:
            parent_initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Restore the original pagination class after the response is generated.
        """
        # Restore the original pagination class
        if hasattr(self, "_original_pagination_class"):
            self.pagination_class = self._original_pagination_class

        # Call the parent finalize_response method if it exists
        parent_finalize = getattr(super(), "finalize_response", None)
        if parent_finalize:
            return parent_finalize(request, response, *args, **kwargs)

        return response
