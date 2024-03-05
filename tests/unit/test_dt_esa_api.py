import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from extensions.eda.plugins.event_source.dt_esa_api import (
    get_problems,
    get_client_session,
)


class MockServerTestCase(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_get('/api/v2/problems', self.handle_request)
        return app

    async def handle_request(self, request):
        return web.json_response({"message": "Service Unavailable"}, status=503)

    async def test_failed_request_in_get_problems(self):
        # Call the function with the mock server URL
        response = await get_problems(get_client_session(""),
                                      dt_host=self.server.make_url(''), proxy="")
        assert response is None


if __name__ == '__main__':
    pytest.main()
