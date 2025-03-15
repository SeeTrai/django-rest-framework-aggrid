"""
Mixins for ag-grid integration with Django REST Framework.
"""

from rest_framework.response import Response


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
