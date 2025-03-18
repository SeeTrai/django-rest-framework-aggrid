# drf-aggrid: ag-grid Filter Backend for Django REST Framework

[![PyPI version](https://badge.fury.io/py/drf-aggrid.svg)](https://badge.fury.io/py/drf-aggrid)
[![Tests](https://github.com/seetrai/drf-aggrid/actions/workflows/tests.yml/badge.svg)](https://github.com/seetrai/drf-aggrid/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This package provides a filter backend for ag-grid integration with Django REST Framework. It handles ag-grid's query parameters for filtering, sorting, and pagination, transforming them into Django ORM compatible filtering.

## Installation

```bash
pip install drf-aggrid
```

## Features

-   Filtering based on ag-grid's `filter` parameter
-   Sorting based on ag-grid's `sort` parameter
-   Pagination based on ag-grid's `startRow` and `endRow` parameters
-   Response formatting in the format expected by ag-grid
-   Support for `format=aggrid` query parameter to activate the filter backend
-   Automatic conversion of dot notation field names to Django ORM field names

## Components

-   `AgGridFilterBackend`: A filter backend that handles ag-grid's query parameters
-   `AgGridPaginationMixin`: A mixin for views that use the `AgGridFilterBackend`
-   `AgGridPagination`: A pagination class that handles ag-grid's pagination parameters
-   `AgGridRenderer`: A custom renderer for ag-grid responses

## Usage

### Basic Usage

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from your_app.models import YourModel
from your_app.serializers import YourModelSerializer
from drf_aggrid import AgGridFilterBackend, AgGridPagination, AgGridRenderer


class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        SearchFilter,
        AgGridFilterBackend,
    ]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, AgGridRenderer]
    search_fields = ["name"]
    pagination_class = AgGridPagination

```

### Router Configuration

```python
from rest_framework.routers import DefaultRouter

from your_app.views import YourModelViewSet

router = DefaultRouter()
router.register(
    r'your-model-ag-grid',
    YourModelViewSet,
    basename='your-model-ag-grid'
)

urlpatterns = router.urls
```

### URL Configuration

```python
from django.urls import path, include

from your_app.routers import router as ag_grid_router

urlpatterns = [
    # ... other URL patterns ...
    path("api/ag-grid/", include(ag_grid_router.urls)),
]
```

## Activation Methods

The filter backend and pagination can be activated in two ways:

1. By setting the `format` query parameter to `aggrid`:

    ```
    GET /api/ag-grid/your-model-ag-grid/?format=aggrid
    ```

2. By directly using ag-grid's query parameters:
    ```
    GET /api/ag-grid/your-model-ag-grid/?filter={"name":{"filterType":"text","type":"contains","filter":"example"}}
    ```

## Dot Notation Support

The filter backend automatically converts ag-grid's dot notation field names to Django ORM compatible field names. For example:

-   `event_type.name` in ag-grid becomes `event_type__name` in Django ORM
-   `user.profile.email` in ag-grid becomes `user__profile__email` in Django ORM

This conversion is applied to both filtering and sorting parameters, allowing you to use the same field names in your ag-grid configuration and Django models.

Example:

```
GET /api/ag-grid/your-model-ag-grid/?filter={"event_type.name":{"filterType":"text","type":"contains","filter":"example"}}&sort=[{"colId":"event_type.name","sort":"asc"}]
```

## Pagination

The pagination is handled by the `AgGridPagination` class, which uses the `startRow` and `endRow` parameters to paginate the queryset. For example:

```
GET /api/ag-grid/your-model-ag-grid/?startRow=0&endRow=100
```

This will return rows 0-99 (100 rows total). The pagination is applied at the database level for efficiency, and the response includes the total count of rows in the `totalCount` field.

### How Pagination Works

1. The `AgGridPagination` class extracts the `startRow` and `endRow` parameters from the request.
2. It applies these parameters to the queryset using Django's slice notation: `queryset[start_row:end_row]`.
3. The pagination is applied at the database level, which is more efficient than fetching all rows and then slicing them.
4. The response includes the total count of rows in the `totalCount` field and the filtered count in the `rowCount` field.

### Pagination Responsibilities

-   **AgGridFilterBackend**: Does NOT apply pagination. It only handles filtering and sorting.
-   **AgGridPagination**: Applies pagination when the view uses it as the pagination_class.
-   **AgGridRenderer**: Applies pagination only if the view doesn't have a paginator.

This separation of responsibilities ensures that pagination is applied correctly and only once.

## Response Format

The response format for ag-grid includes three main fields:

-   **totalCount**: The total number of rows in the dataset before any filtering is applied.
-   **rowCount**: The number of rows after filtering is applied (but before pagination).
-   **rows**: The actual data rows after pagination is applied.

This format allows ag-grid to properly display pagination information and handle server-side operations.

### Example Response

```json
{
    "rowCount": 50, // 50 rows match the filter criteria
    "totalCount": 1000, // 1000 total rows in the dataset
    "rows": [
        // Only the first 10 rows are returned due to pagination
        {
            "id": 1,
            "name": "Example 1",
            "event_type": {
                "name": "Conference"
            }
        }
        // ... more rows ...
    ]
}
```

## Supported Filter Types

The `AgGridFilterBackend` supports the following filter types:

### Text Filters

-   `equals`
-   `notEqual`
-   `contains`
-   `notContains`
-   `startsWith`
-   `endsWith`

### Number Filters

-   `equals`
-   `notEqual`
-   `lessThan`
-   `lessThanOrEqual`
-   `greaterThan`
-   `greaterThanOrEqual`
-   `inRange`

### Date Filters

-   `equals`
-   `notEqual`
-   `lessThan`
-   `greaterThan`
-   `inRange`

### Set Filters

-   `values` (list of values to filter by)

### Boolean Filters

-   `filter` (boolean value to filter by)

## Example Requests

### Using format=aggrid

```
GET /api/ag-grid/your-model-ag-grid/?format=aggrid&filter={"name":{"filterType":"text","type":"contains","filter":"example"}}&sort=[{"colId":"name","sort":"asc"}]&startRow=0&endRow=10
```

### Using direct parameters

```
GET /api/ag-grid/your-model-ag-grid/?filter={"name":{"filterType":"text","type":"contains","filter":"example"}}&sort=[{"colId":"name","sort":"asc"}]&startRow=0&endRow=10
```

### Using dot notation

```
GET /api/ag-grid/your-model-ag-grid/?filter={"event_type.name":{"filterType":"text","type":"contains","filter":"example"}}&sort=[{"colId":"event_type.name","sort":"asc"}]&startRow=0&endRow=10
```

## Custom Filtering

The `AgGridFilterBackend` provides a way to define custom filter functions for specific fields. This is useful when you need to implement complex filtering logic that isn't covered by the default filter types.

### How to Use Custom Filtering

1. Implement `get_aggrid_custom_filters` in your view:

```python
def get_aggrid_custom_filters(self):
    return {
        'field_name': self.filter_field_name,
        # Add more custom filters as needed
    }
```

2. Implement filter functions:

```python
def filter_field_name(self, field, filter_condition, queryset, request, view):
    # Custom filtering logic here
    # ...
    return filtered_queryset
```

### Example

```python
from rest_framework import viewsets
from django.db.models import Q
from drf_aggrid import AgGridFilterBackend, AgGridPagination

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [AgGridFilterBackend]
    pagination_class = AgGridPagination

    def get_aggrid_custom_filters(self):
        return {
            'internal_participants': self.filter_internal_participants,
        }

    def filter_internal_participants(self, field, filter_condition, queryset, request, view):
        filter_type = filter_condition.get('filterType')

        if filter_type == 'set':
            values = filter_condition.get('values', [])
            if not values:
                return queryset

            participant_q = Q()
            for value in values:
                participant_q |= Q(participants__is_internal=True, participants__id=value)

            return queryset.filter(participant_q).distinct()

        # Handle other filter types...

        return queryset
```

## Troubleshooting

### Empty Error with format=aggrid

If you're getting an empty error when using the `format=aggrid` parameter, make sure you've included the `AgGridRenderer` in your view's `renderer_classes`:

```python
renderer_classes = [JSONRenderer, BrowsableAPIRenderer, AgGridRenderer]
```

This renderer is responsible for properly formatting the response when the `format=aggrid` parameter is used.

### Pagination Issues

If you're experiencing pagination issues (e.g., getting more rows than requested), make sure:

1. You're using the `AgGridPagination` class as your pagination class:

    ```python
    pagination_class = AgGridPagination
    ```

2. You're providing both `startRow` and `endRow` parameters in your request:

    ```
    GET /api/ag-grid/your-model-ag-grid/?startRow=0&endRow=100
    ```

3. The `endRow` parameter is exclusive, meaning `startRow=0&endRow=100` will return rows 0-99 (100 rows total).

4. You've overridden the `get_paginated_response` method in your view to ensure proper formatting:

    ```python
    def get_paginated_response(self, data):
        if hasattr(self, 'paginator') and isinstance(self.paginator, AgGridPagination):
            return self.paginator.get_paginated_response(data)

        return Response({
            'rowCount': len(data),
            'totalCount': len(data),
            'rows': data
        })
    ```

5. The filter backend is not applying pagination. Only the pagination class or the renderer should apply pagination.

### rowCount and totalCount Issues

If `rowCount` and `totalCount` are showing the same value even when filters are applied, make sure:

1. The filter backend is properly setting both values:

    - `_ag_grid_total_count` should be set to the count of the base queryset before any filtering
    - `_ag_grid_filtered_count` should be set to the count of the queryset after filtering

2. The pagination class is using these values correctly:

    - `totalCount` should come from `_ag_grid_total_count`
    - `rowCount` should come from `_ag_grid_filtered_count`

3. You're not overriding these values elsewhere in your code.

### Field Name Issues

If you're experiencing issues with field names, make sure:

1. You're using the correct field names in your ag-grid configuration. The field names should match the serializer field names.

2. For nested fields, use dot notation in your ag-grid configuration (e.g., `event_type.name`). The filter backend will automatically convert these to Django ORM field names (e.g., `event_type__name`).

## Automatic Pagination for Ag-Grid Requests

If you want your views to automatically use `AgGridPagination` for ag-grid requests and standard pagination for other requests, you can use the `AutoAgGridPaginationMixin`:

```python
from drf_aggrid.mixins import AutoAgGridPaginationMixin
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

class MyViewSet(AutoAgGridPaginationMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    pagination_class = PageNumberPagination  # This will be used for non-aggrid requests
```

The `AutoAgGridPaginationMixin` will:

1. Use `AgGridPagination` for requests with `?format=aggrid`
2. Use your specified `pagination_class` for all other requests
3. Restore the original pagination class after the response is generated

You can also specify a different standard pagination class:

```python
class MyViewSet(AutoAgGridPaginationMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    pagination_class = DefaultPaginationClass
    standard_pagination_class = CustomPaginationClass  # This will override the default
```

This mixin makes it easy to support both ag-grid and standard API clients with the same view.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
