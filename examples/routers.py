"""
Router configuration for the example ag-grid views.
"""

from rest_framework.routers import DefaultRouter

from examples.views import (
    ExampleModelAgGridViewSet,
    ExampleModelWithCustomFiltersViewSet,
)

# Create a router for the ag-grid examples
router = DefaultRouter()
router.register(
    r"example-model-ag-grid",
    ExampleModelAgGridViewSet,
    basename="example-model-ag-grid",
)
router.register(
    r"example-model-custom-filters",
    ExampleModelWithCustomFiltersViewSet,
    basename="example-model-custom-filters",
)

# The format suffix patterns are added by the router automatically
# No need to manually modify the URL patterns

urlpatterns = router.urls
