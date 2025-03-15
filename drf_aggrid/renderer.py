"""
Renderer for ag-grid integration with Django REST Framework.
"""

import logging
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)


class AgGridRenderer(JSONRenderer):
    """
    Custom renderer for ag-grid responses.

    This renderer is used to identify ag-grid requests by the 'format=aggrid' parameter.
    It formats the response data in the way expected by ag-grid.
    """

    format = "aggrid"
    media_type = "application/json"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the data as JSON for ag-grid.

        If the data is already in the ag-grid format (has 'rows', 'rowCount', 'totalCount'),
        return it as is. Otherwise, wrap it in the ag-grid format.
        """
        # Check if the data is already in the ag-grid format
        if isinstance(data, dict) and all(
            key in data for key in ["rows", "rowCount", "totalCount"]
        ):
            # Data is already in ag-grid format, render it as JSON
            return super().render(data, accepted_media_type, renderer_context)

        # Data is not in ag-grid format, wrap it
        view = renderer_context.get("view") if renderer_context else None
        request = renderer_context.get("request") if renderer_context else None

        # Get total and filtered counts from the view if available
        total_count = getattr(view, "_ag_grid_total_count", 0) if view else 0
        filtered_count = getattr(view, "_ag_grid_filtered_count", 0) if view else 0

        # If data is a list, use it as rows
        if isinstance(data, list):
            rows = data
            # If we don't have a filtered count yet, use the length of the rows
            if filtered_count == 0:
                filtered_count = len(rows)
        # If data is a dict with 'results', use that as rows
        elif isinstance(data, dict) and "results" in data:
            rows = data["results"]
            # Try to get counts from the data if available
            if "count" in data:
                filtered_count = data["count"]
                total_count = data.get("total_count", filtered_count)
        else:
            # Otherwise, just use the data as is
            rows = data
            # If we don't have a filtered count yet, use the length of the rows
            if filtered_count == 0:
                filtered_count = len(rows) if hasattr(rows, "__len__") else 0

        # Check if we need to apply pagination here
        # Only apply pagination if the view doesn't have a paginator or if the paginator didn't handle it
        if request and not hasattr(view, "paginator"):
            # Get pagination parameters
            start_row = request.query_params.get("startRow")
            end_row = request.query_params.get("endRow")

            if start_row is not None and end_row is not None:
                try:
                    start_row = int(start_row)
                    end_row = int(end_row)

                    # Ensure we're not exceeding the rows size
                    if start_row < len(rows):
                        # Calculate the actual end row (don't exceed the rows size)
                        actual_end_row = min(end_row, len(rows))

                        # Log pagination parameters for debugging
                        logger.debug(
                            "Renderer paginating: startRow=%s, endRow=%s, actualEndRow=%s, rowsLength=%s",
                            start_row,
                            end_row,
                            actual_end_row,
                            len(rows),
                        )

                        # Apply pagination to the rows
                        rows = rows[start_row:actual_end_row]
                except ValueError:
                    pass

        # Create the ag-grid response format
        ag_grid_data = {
            "rowCount": filtered_count,
            "totalCount": total_count,
            "rows": rows,
        }

        # Log the response data for debugging
        logger.debug(
            "Renderer response: totalCount=%s, filteredCount=%s, rowsLength=%s",
            total_count,
            filtered_count,
            len(rows),
        )

        # Render the ag-grid data as JSON
        return super().render(ag_grid_data, accepted_media_type, renderer_context)
