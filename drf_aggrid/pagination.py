"""
Pagination classes for ag-grid integration with Django REST Framework.
"""

import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AgGridPagination(PageNumberPagination):
    """
    Pagination class for ag-grid integration with Django REST Framework.

    This pagination class handles ag-grid's startRow and endRow parameters
    and returns a response in the format expected by ag-grid.

    The pagination can be activated by either:
    1. Setting the 'format' query parameter to 'aggrid'
    2. Directly using the pagination parameters (startRow, endRow)

    Supported ag-grid parameters:
    - filter: JSON string containing filter criteria
    - sort: JSON string containing sort criteria
    - startRow: Start row for pagination
    - endRow: End row for pagination
    """

    page_size_query_param = "page_size"
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset for ag-grid.

        This method uses startRow and endRow parameters from the request
        to paginate the queryset.
        """
        # Check if this is an ag-grid request
        if not self.is_aggrid_request(request):
            return super().paginate_queryset(queryset, request, view)

        # Get startRow and endRow parameters
        start_row = request.query_params.get("startRow")
        end_row = request.query_params.get("endRow")

        # If startRow and endRow are not provided, use default pagination
        if start_row is None or end_row is None:
            return super().paginate_queryset(queryset, request, view)

        try:
            start_row = int(start_row)
            end_row = int(end_row)
        except ValueError:
            return super().paginate_queryset(queryset, request, view)

        # Store the total count (before any filtering)
        # This should be the count of the base queryset before any filters are applied
        if hasattr(view, "_ag_grid_total_count"):
            self.total_count = getattr(view, "_ag_grid_total_count")
        else:
            # If the view doesn't have a total count, use the queryset count
            # This might be after filtering, but it's the best we can do
            self.total_count = self.get_count(queryset)

        # Store the filtered count (after filtering)
        # This is the count of the queryset after filters are applied
        self.count = self.get_count(queryset)

        # Store the view for later use
        self.request = request
        self.view = view

        # Store counts on the view for the renderer to use
        if view:
            # Only set the total count if it's not already set
            if not hasattr(view, "_ag_grid_total_count"):
                setattr(view, "_ag_grid_total_count", self.total_count)
            # Always set the filtered count
            setattr(view, "_ag_grid_filtered_count", self.count)

        # Store the pagination parameters for later use
        self.start_row = start_row
        self.end_row = end_row

        # Ensure we're not exceeding the queryset size
        if start_row >= self.count:
            return []

        # Calculate the actual end row (don't exceed the queryset size)
        actual_end_row = min(end_row, self.count)

        # Log pagination parameters for debugging
        logger.debug(
            "Paginating queryset: startRow=%s, endRow=%s, actualEndRow=%s, filteredCount=%s, totalCount=%s",
            start_row,
            end_row,
            actual_end_row,
            self.count,
            self.total_count,
        )

        # Paginate the queryset
        # Make sure to use a slice of the queryset to avoid evaluating the entire queryset
        paginated_queryset = queryset[start_row:actual_end_row]

        # Convert to list to ensure the queryset is evaluated
        return list(paginated_queryset)

    def is_aggrid_request(self, request):
        """
        Check if the request is for ag-grid.

        The request is considered for ag-grid if:
        1. The 'format' query parameter is set to 'aggrid'
        2. Any of the ag-grid specific parameters are present (filter, sort, startRow, endRow)
        """
        format_param = request.query_params.get("format")
        if format_param and format_param.lower() == "aggrid":
            return True

        # Check for ag-grid specific parameters
        aggrid_params = ["filter", "sort", "startRow", "endRow"]
        for param in aggrid_params:
            if param in request.query_params:
                return True

        return False

    def get_paginated_response(self, data):
        """
        Return a paginated response in the format expected by ag-grid.
        """
        # Get total and filtered counts
        total_count = getattr(self, "total_count", self.count)
        filtered_count = getattr(self, "count", len(data))

        # Log response data for debugging
        logger.debug(
            "Paginated response: totalCount=%s, filteredCount=%s, dataLength=%s",
            total_count,
            filtered_count,
            len(data),
        )

        # Check if the request format is 'aggrid'
        format_param = self.request.query_params.get("format")
        if format_param and format_param.lower() == "aggrid":
            # For format=aggrid, let the renderer handle the formatting
            return Response(data)

        # For direct ag-grid parameters, format the response here
        response_data = {
            "rowCount": filtered_count,
            "totalCount": total_count,
            "rows": data,
        }

        return Response(response_data)

    def get_count(self, queryset):
        """
        Get the count of the queryset.
        """
        return queryset.count()
