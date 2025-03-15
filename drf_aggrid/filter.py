"""
Filter backend for ag-grid integration with Django REST Framework.

This filter backend handles ag-grid's query parameters for filtering, sorting, and pagination.
It transforms ag-grid's filter criteria into Django ORM compatible filtering.
"""

import json
import logging
import operator
from functools import reduce

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

logger = logging.getLogger(__name__)


class AgGridFilterBackend(BaseFilterBackend):
    """
    Filter backend for ag-grid integration with Django REST Framework.

    This filter backend handles ag-grid's query parameters for filtering, sorting, and pagination.
    It transforms ag-grid's filter criteria into Django ORM compatible filtering.

    Supported ag-grid parameters:
    - filter: JSON string containing filter criteria (replaces filterModel)
    - sort: JSON string containing sort criteria (replaces sortModel)
    - startRow: Start row for pagination
    - endRow: End row for pagination

    The filter backend can be activated by either:
    1. Setting the 'format' query parameter to 'aggrid'
    2. Directly using the filter parameters (filter, sort, startRow, endRow)

    Field names in ag-grid often use dot notation (e.g., 'event_type.name').
    This filter backend automatically converts these to Django ORM compatible field names
    (e.g., 'event_type__name').

    For custom field filtering, views can implement a method named 'get_aggrid_custom_filters'
    that returns a dictionary mapping field names to filter functions.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter the queryset based on ag-grid parameters.

        This method handles:
        1. Filtering based on filter parameter
        2. Sorting based on sort parameter
        3. Pagination based on startRow and endRow
        """
        logger.debug("AgGridFilterBackend filter_queryset %s", request.query_params)
        # Check if this request is for ag-grid
        if not self.is_aggrid_request(request):
            return queryset

        # Get the base queryset (before any filtering)
        base_queryset = (
            view.get_queryset() if hasattr(view, "get_queryset") else queryset
        )

        # Store the total count before filtering
        # This is the count of the base queryset before any filters are applied
        total_count = base_queryset.count()
        setattr(view, "_ag_grid_total_count", total_count)

        # Apply filtering
        filter_model = self.get_filter_model(request)
        if filter_model:
            # Get custom filters from the view if available
            custom_filters = self.get_custom_filters(view)

            # Process standard and custom filters
            queryset = self.apply_filters(
                filter_model, queryset, custom_filters, request, view
            )

        # Store the filtered count
        # This is the count of the queryset after filters are applied
        filtered_count = queryset.count()
        setattr(view, "_ag_grid_filtered_count", filtered_count)

        # Apply sorting
        sort_model = self.get_sort_model(request)
        if sort_model:
            ordering = self.build_ordering(sort_model)
            if ordering:
                queryset = queryset.order_by(*ordering)

        # IMPORTANT: We should NOT apply pagination here
        # Pagination should be handled by the pagination class or the renderer
        # This avoids double pagination issues

        # Log the queryset for debugging
        logger.debug(
            "Filter backend: totalCount=%s, filteredCount=%s, query=%s",
            total_count,
            filtered_count,
            str(queryset.query),
        )

        return queryset

    def get_custom_filters(self, view):
        """
        Get custom filter functions from the view.

        The view can implement a method named 'get_aggrid_custom_filters'
        that returns a dictionary mapping field names to filter functions.

        Each filter function should accept the following parameters:
        - field: The field name (converted to Django ORM format)
        - filter_condition: The filter condition from ag-grid
        - queryset: The current queryset
        - request: The current request
        - view: The current view

        The function should return a filtered queryset.
        """
        if hasattr(view, "get_aggrid_custom_filters"):
            return view.get_aggrid_custom_filters()
        return {}

    def apply_filters(self, filter_model, queryset, custom_filters, request, view):
        """
        Apply both standard and custom filters to the queryset.

        This method processes each filter in the filter model and applies either
        a custom filter function (if available) or the standard filter logic.
        """
        if not filter_model:
            return queryset

        standard_filters = {}

        # Separate custom filters from standard filters
        for field, filter_condition in filter_model.items():
            if field in custom_filters:
                # Apply custom filter directly
                queryset = custom_filters[field](
                    field=self.convert_field_name(field),
                    filter_condition=filter_condition,
                    queryset=queryset,
                    request=request,
                    view=view,
                )
            else:
                # Collect standard filters for batch processing
                standard_filters[field] = filter_condition

        # Process standard filters if any
        if standard_filters:
            filter_q = self.build_filter_query(standard_filters)
            if filter_q:
                queryset = queryset.filter(filter_q).distinct()

        return queryset

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

    def get_filter_model(self, request):
        """
        Parse the filter parameter from the request.

        The filter is a JSON string containing filter criteria.
        """
        filter_model_str = request.query_params.get("filter")
        if not filter_model_str:
            return None

        try:
            return json.loads(filter_model_str)
        except json.JSONDecodeError:
            return None

    def get_sort_model(self, request):
        """
        Parse the sort parameter from the request.

        The sort is a JSON string containing sort criteria.
        """
        sort_model_str = request.query_params.get("sort")
        if not sort_model_str:
            return None

        try:
            return json.loads(sort_model_str)
        except json.JSONDecodeError:
            return None

    def get_pagination_params(self, request):
        """
        Parse the startRow and endRow parameters from the request.

        These parameters are used for pagination.
        """
        start_row = request.query_params.get("startRow")
        end_row = request.query_params.get("endRow")

        try:
            start_row = int(start_row) if start_row is not None else None
            end_row = int(end_row) if end_row is not None else None
            return start_row, end_row
        except ValueError:
            return None, None

    def convert_field_name(self, field_name):
        """
        Convert ag-grid field name to Django ORM field name.

        Ag-grid uses dot notation for nested fields (e.g., 'event_type.name'),
        while Django ORM uses double underscore notation (e.g., 'event_type__name').
        """
        return field_name.replace(".", "__")

    def build_filter_query(self, filter_model):
        """
        Build a Django Q object from the ag-grid filter model.

        The filter model is a dictionary where keys are field names and values are filter conditions.
        """
        if not filter_model:
            return None

        q_objects = []

        for field, filter_condition in filter_model.items():
            # Convert field name from dot notation to Django ORM format
            django_field = self.convert_field_name(field)

            filter_type = filter_condition.get("filterType")

            if filter_type == "text":
                q_objects.append(
                    self._build_text_filter(django_field, filter_condition)
                )
            elif filter_type == "number":
                q_objects.append(
                    self._build_number_filter(django_field, filter_condition)
                )
            elif filter_type == "date":
                q_objects.append(
                    self._build_date_filter(django_field, filter_condition)
                )
            elif filter_type == "set":
                q_objects.append(self._build_set_filter(django_field, filter_condition))
            elif filter_type == "boolean":
                q_objects.append(
                    self._build_boolean_filter(django_field, filter_condition)
                )

        if not q_objects:
            return None

        # Combine all Q objects with AND
        return reduce(operator.and_, q_objects)

    def _build_text_filter(self, field, filter_condition):
        """
        Build a Q object for text filter conditions.

        Supported filter types:
        - equals
        - notEqual
        - contains
        - notContains
        - startsWith
        - endsWith
        """
        filter_type = filter_condition.get("type")
        filter_value = filter_condition.get("filter")

        if not filter_value:
            return Q()

        if filter_type == "equals":
            return Q(**{f"{field}__exact": filter_value})
        elif filter_type == "notEqual":
            return ~Q(**{f"{field}__exact": filter_value})
        elif filter_type == "contains":
            return Q(**{f"{field}__icontains": filter_value})
        elif filter_type == "notContains":
            return ~Q(**{f"{field}__icontains": filter_value})
        elif filter_type == "startsWith":
            return Q(**{f"{field}__istartswith": filter_value})
        elif filter_type == "endsWith":
            return Q(**{f"{field}__iendswith": filter_value})

        return Q()

    def _build_number_filter(self, field, filter_condition):
        """
        Build a Q object for number filter conditions.

        Supported filter types:
        - equals
        - notEqual
        - lessThan
        - lessThanOrEqual
        - greaterThan
        - greaterThanOrEqual
        - inRange
        """
        filter_type = filter_condition.get("type")
        filter_value = filter_condition.get("filter")

        if filter_value is None:
            return Q()

        if filter_type == "equals":
            return Q(**{f"{field}": filter_value})
        elif filter_type == "notEqual":
            return ~Q(**{f"{field}": filter_value})
        elif filter_type == "lessThan":
            return Q(**{f"{field}__lt": filter_value})
        elif filter_type == "lessThanOrEqual":
            return Q(**{f"{field}__lte": filter_value})
        elif filter_type == "greaterThan":
            return Q(**{f"{field}__gt": filter_value})
        elif filter_type == "greaterThanOrEqual":
            return Q(**{f"{field}__gte": filter_value})
        elif filter_type == "inRange":
            filter_to = filter_condition.get("filterTo")
            if filter_to is not None:
                return Q(**{f"{field}__gte": filter_value}) & Q(
                    **{f"{field}__lte": filter_to}
                )

        return Q()

    def _build_date_filter(self, field, filter_condition):
        """
        Build a Q object for date filter conditions.

        Supported filter types:
        - equals
        - notEqual
        - lessThan
        - greaterThan
        - inRange
        """
        filter_type = filter_condition.get("type")
        filter_value = filter_condition.get("dateFrom")

        if not filter_value:
            return Q()

        if filter_type == "equals":
            return Q(**{f"{field}__date": filter_value})
        elif filter_type == "notEqual":
            return ~Q(**{f"{field}__date": filter_value})
        elif filter_type == "lessThan":
            return Q(**{f"{field}__lt": filter_value})
        elif filter_type == "greaterThan":
            return Q(**{f"{field}__gt": filter_value})
        elif filter_type == "inRange":
            filter_to = filter_condition.get("dateTo")
            if filter_to:
                return Q(**{f"{field}__gte": filter_value}) & Q(
                    **{f"{field}__lte": filter_to}
                )

        return Q()

    def _build_set_filter(self, field, filter_condition):
        """
        Build a Q object for set filter conditions.

        The set filter is used for filtering on a set of values.
        """
        values = filter_condition.get("values", [])

        if not values:
            return Q()

        return Q(**{f"{field}__in": values})

    def _build_boolean_filter(self, field, filter_condition):
        """
        Build a Q object for boolean filter conditions.
        """
        filter_value = filter_condition.get("filter")

        if filter_value is None:
            return Q()

        return Q(**{field: filter_value})

    def build_ordering(self, sort_model):
        """
        Build a list of ordering fields from the ag-grid sort model.

        The sort model is a list of dictionaries with 'colId' and 'sort' keys.
        """
        if not sort_model:
            return []

        ordering = []

        for sort_item in sort_model:
            col_id = sort_item.get("colId")
            sort_direction = sort_item.get("sort")

            if not col_id or not sort_direction:
                continue

            # Convert field name from dot notation to Django ORM format
            django_field = self.convert_field_name(col_id)

            if sort_direction == "desc":
                ordering.append(f"-{django_field}")
            else:
                ordering.append(django_field)

        return ordering


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
