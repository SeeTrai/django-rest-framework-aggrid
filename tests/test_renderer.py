"""
Tests for the AgGridRenderer.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from drf_aggrid import AgGridRenderer


class AgGridRendererTestCase(TestCase):
    """
    Test case for the AgGridRenderer.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.renderer = AgGridRenderer()
        self.view = APIView()

    def test_render_with_aggrid_format(self):
        """
        Test that render returns the data in ag-grid format when it's already in that format.
        """
        data = {
            "rowCount": 5,
            "totalCount": 10,
            "rows": ["item1", "item2", "item3", "item4", "item5"],
        }
        request = self.factory.get("/", {"format": "aggrid"})
        renderer_context = {"request": request, "view": self.view}

        # Render the data
        result = self.renderer.render(data, None, renderer_context)

        # Parse the JSON result
        import json

        result_data = json.loads(result.decode("utf-8"))

        # Check that the result is in ag-grid format
        self.assertEqual(result_data["rowCount"], 5)
        self.assertEqual(result_data["totalCount"], 10)
        self.assertEqual(
            result_data["rows"], ["item1", "item2", "item3", "item4", "item5"]
        )

    def test_render_with_list_data(self):
        """
        Test that render wraps list data in ag-grid format.
        """
        data = ["item1", "item2", "item3", "item4", "item5"]
        request = self.factory.get("/", {"format": "aggrid"})
        renderer_context = {"request": request, "view": self.view}

        # Render the data
        result = self.renderer.render(data, None, renderer_context)

        # Parse the JSON result
        import json

        result_data = json.loads(result.decode("utf-8"))

        # Check that the result is in ag-grid format
        self.assertEqual(result_data["rowCount"], 5)
        self.assertEqual(result_data["totalCount"], 0)  # Default total count is 0
        self.assertEqual(
            result_data["rows"], ["item1", "item2", "item3", "item4", "item5"]
        )

    def test_render_with_dict_results(self):
        """
        Test that render extracts 'results' from dict data and wraps it in ag-grid format.
        """
        data = {
            "count": 5,
            "total_count": 10,
            "results": ["item1", "item2", "item3", "item4", "item5"],
        }
        request = self.factory.get("/", {"format": "aggrid"})
        renderer_context = {"request": request, "view": self.view}

        # Render the data
        result = self.renderer.render(data, None, renderer_context)

        # Parse the JSON result
        import json

        result_data = json.loads(result.decode("utf-8"))

        # Check that the result is in ag-grid format
        self.assertEqual(result_data["rowCount"], 5)
        self.assertEqual(result_data["totalCount"], 10)
        self.assertEqual(
            result_data["rows"], ["item1", "item2", "item3", "item4", "item5"]
        )

    def test_render_with_pagination(self):
        """
        Test that render applies pagination when startRow and endRow are provided.
        """
        data = ["item1", "item2", "item3", "item4", "item5"]
        request = self.factory.get(
            "/", {"format": "aggrid", "startRow": "1", "endRow": "3"}
        )
        renderer_context = {"request": request, "view": self.view}

        # Render the data
        result = self.renderer.render(data, None, renderer_context)

        # Parse the JSON result
        import json

        result_data = json.loads(result.decode("utf-8"))

        # Check that the result is in ag-grid format and paginated
        self.assertEqual(result_data["rowCount"], 5)
        self.assertEqual(result_data["totalCount"], 0)  # Default total count is 0
        self.assertEqual(result_data["rows"], ["item2", "item3"])
