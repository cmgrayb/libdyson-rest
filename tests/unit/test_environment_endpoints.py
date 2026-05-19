"""Unit tests for EC air purifier client endpoints (sync and async)."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import requests

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError
from libdyson_rest.models import DailyAirQualityData, ScheduledEventsData

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SERIAL = "AB1-CD-EF234567"
PRODUCT_TYPE = "438K"

DAILY_ENV_RESPONSE = {
    "start_time": "2024-01-01T00:00:00Z",
    "resolution": 15,
    "aqlm": [1.0, 2.0, None, 3.0, 4.0],
}

SCHEDULED_EVENTS_RESPONSE = {
    "enabled": True,
    "events": [
        {"enabled": True, "days": ["Monday", "Wednesday"], "startTime": "08:00"},
        {"enabled": False, "days": ["Saturday"], "startTime": "10:00"},
    ],
}


# ===========================================================================
# Synchronous client tests
# ===========================================================================


class TestSyncGetDailyEnvironmentData:
    @patch("requests.Session.get")
    def test_success_returns_daily_air_quality_data(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = DAILY_ENV_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        data = client.get_daily_environment_data(SERIAL)

        assert isinstance(data, DailyAirQualityData)
        assert data.start_time == "2024-01-01T00:00:00Z"
        assert data.resolution_minutes == 15
        # The list has 5 entries; one None value
        assert len(data.samples) == 5
        assert data.latest_sample == pytest.approx(4.0)

    @patch("requests.Session.get")
    def test_correct_url_used(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = DAILY_ENV_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_daily_environment_data(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/messageprocessor/devices/{SERIAL}/environmentdata/daily" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_daily_environment_data(SERIAL)

    @patch("requests.Session.get")
    def test_raises_auth_error_on_401(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = requests.HTTPError(response=mock_response)

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.get_daily_environment_data(SERIAL)

    @patch("requests.Session.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.ConnectionError("no connection")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_daily_environment_data(SERIAL)

    @patch("requests.Session.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [DAILY_ENV_RESPONSE]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_daily_environment_data(SERIAL)


class TestSyncGetScheduledEvents:
    @patch("requests.Session.get")
    def test_success_returns_scheduled_events_data(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        data = client.get_scheduled_events(SERIAL)

        assert isinstance(data, ScheduledEventsData)
        assert data.schedule_enabled is True
        assert len(data.events) == 2
        assert len(data.active_events) == 1

    @patch("requests.Session.get")
    def test_product_type_included_in_params_when_provided(
        self, mock_get: Mock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_scheduled_events(SERIAL, product_type=PRODUCT_TYPE)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {"productType": PRODUCT_TYPE}

    @patch("requests.Session.get")
    def test_product_type_omitted_when_none(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_scheduled_events(SERIAL)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {}

    @patch("requests.Session.get")
    def test_correct_url_used(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_scheduled_events(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/unifiedscheduler/{SERIAL}/events" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_scheduled_events(SERIAL)

    @patch("requests.Session.get")
    def test_raises_auth_error_on_401(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = requests.HTTPError(response=mock_response)

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.get_scheduled_events(SERIAL)

    @patch("requests.Session.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.ConnectionError("timeout")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_scheduled_events(SERIAL)

    @patch("requests.Session.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [SCHEDULED_EVENTS_RESPONSE]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_scheduled_events(SERIAL)


# ===========================================================================
# Asynchronous client tests
# ===========================================================================


class TestAsyncGetDailyEnvironmentData:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_daily_air_quality_data(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = DAILY_ENV_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        data = await client.get_daily_environment_data(SERIAL)

        assert isinstance(data, DailyAirQualityData)
        assert data.start_time == "2024-01-01T00:00:00Z"
        assert data.latest_sample == pytest.approx(4.0)
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_daily_environment_data(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_auth_error_on_401(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            await client.get_daily_environment_data(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("timeout")

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_daily_environment_data(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_dict_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_daily_environment_data(SERIAL)
        await client.close()


class TestAsyncGetScheduledEvents:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_scheduled_events_data(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        data = await client.get_scheduled_events(SERIAL)

        assert isinstance(data, ScheduledEventsData)
        assert data.schedule_enabled is True
        assert len(data.events) == 2
        assert len(data.active_events) == 1
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_product_type_included_in_params_when_provided(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_scheduled_events(SERIAL, product_type=PRODUCT_TYPE)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {"productType": PRODUCT_TYPE}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_product_type_omitted_when_none(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SCHEDULED_EVENTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_scheduled_events(SERIAL)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {}
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_scheduled_events(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_auth_error_on_401(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            await client.get_scheduled_events(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("timeout")

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_scheduled_events(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_dict_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [SCHEDULED_EVENTS_RESPONSE]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_scheduled_events(SERIAL)
        await client.close()
