"""
Example usage of the AgGridFilterBackend and AgGridPagination.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from drf_aggrid import AgGridFilterBackend, AgGridPagination, AgGridRenderer
from drf_aggrid.mixins import AgGridAutoPaginationMixin


class ExampleModelWithAutoPaginationViewSet(
    AgGridAutoPaginationMixin, viewsets.ModelViewSet
):
    """
    ViewSet example using AutoAgGridPaginationMixin.

    This ViewSet demonstrates how to use the AutoAgGridPaginationMixin to automatically
    switch between standard pagination and AgGridPagination based on the request format.
    """

    # Replace with your model and serializer
    # queryset = YourModel.objects.all()
    # serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        SearchFilter,
        AgGridFilterBackend,
    ]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, AgGridRenderer]
    search_fields = ["name"]


class ExampleModelAgGridViewSet(viewsets.ModelViewSet):
    """
    ViewSet example using ag-grid filter backend and pagination.

    This ViewSet demonstrates how to use the AgGridFilterBackend and AgGridPagination
    to handle ag-grid's query parameters for filtering, sorting, and pagination.
    """

    # Replace with your model and serializer
    # queryset = YourModel.objects.all()
    # serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AgGridPagination
    filter_backends = [
        SearchFilter,
        AgGridFilterBackend,
    ]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, AgGridRenderer]
    search_fields = ["name"]

    def get_paginated_response(self, data):
        """
        Return a paginated response in the format expected by ag-grid.
        """
        if hasattr(self, "paginator") and isinstance(self.paginator, AgGridPagination):
            return self.paginator.get_paginated_response(data)

        return Response({"rowCount": len(data), "totalCount": len(data), "rows": data})


class ExampleModelWithCustomFiltersViewSet(viewsets.ModelViewSet):
    """
    ViewSet example using ag-grid filter backend with custom filters.

    This ViewSet demonstrates how to use custom filter functions with the AgGridFilterBackend.
    """

    # Replace with your model and serializer
    # queryset = YourModel.objects.all()
    # serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AgGridPagination
    filter_backends = [AgGridFilterBackend]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, AgGridRenderer]

    def get_aggrid_custom_filters(self):
        """
        Return a dictionary of custom filter functions.

        Each key is a field name, and each value is a filter function.
        """
        return {
            "custom_field": self.filter_custom_field,
        }

    def filter_custom_field(self, field, filter_condition, queryset, request, view):
        """
        Custom filter function for the 'custom_field' field.

        This is just an example. You would implement your own filtering logic here.
        """
        filter_type = filter_condition.get("filterType")

        if filter_type == "text":
            filter_value = filter_condition.get("filter")
            filter_type = filter_condition.get("type")

            if filter_type == "contains" and filter_value:
                # Example: Custom contains filter that searches in multiple fields
                return queryset.filter(
                    # Replace with your actual field names
                    # name__icontains=filter_value
                )

        # Return the original queryset if no filtering was applied
        return queryset
