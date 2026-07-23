"""
Coverage tests for previously uncovered branches in async_client.py.

Targets the following uncovered areas:
- authenticate() with otp_code (True branch)
- complete_authentication() both paths
- Mobile login methods (get_user_status_mobile, begin_login_mobile,
  complete_login_mobile)
- Core method error paths (get_devices, get_iot_credentials, get_pending_release,
  trigger_firmware_update)
- All robot/device method non-401 HTTP error paths and parse error paths
"""

from unittest.mock import Mock, patch

import httpx
import pytest

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

SERIAL = "AB1-CD-EF234567"
MAP_ID = "pm-001"
ZONE_ID = "zone-A"
CLEAN_ID = "cr-007"

LOGIN_INFO_RESPONSE = {
    "account": "12345678-1234-5678-1234-567812345678",
    "token": "mobile_test_token_123",
    "tokenType": "Bearer",
}


def _ok(json_data: object) -> Mock:
    """Return a mock HTTP response with the given JSON body."""
    r = Mock()
    r.raise_for_status.return_value = None
    r.json.return_value = json_data
    r.status_code = 200
    return r


def _server_error() -> httpx.HTTPStatusError:
    """Return an HTTPStatusError for a 500 Internal Server Error."""
    mock_response = Mock()
    mock_response.status_code = 500
    return httpx.HTTPStatusError(
        "Internal Server Error", request=Mock(), response=mock_response
    )


def _json_error(mock_response: Mock) -> Mock:
    """Configure mock_response so that .json() raises ValueError."""
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("invalid json")
    return mock_response


# ---------------------------------------------------------------------------
# authenticate() with otp_code — True branch (lines ~676-678)
# ---------------------------------------------------------------------------


class TestAuthenticateWithOtpCode:
    @patch("libdyson_rest.async_client.AsyncDysonClient.complete_login")
    @patch("libdyson_rest.async_client.AsyncDysonClient.begin_login")
    @pytest.mark.asyncio
    async def test_with_otp_code_completes_login_and_returns_true(
        self, mock_begin: Mock, mock_complete: Mock
    ) -> None:
        mock_challenge = Mock()
        mock_challenge.challenge_id = "ch-001"
        mock_begin.return_value = mock_challenge
        mock_complete.return_value = Mock()

        client = AsyncDysonClient(email="test@example.com", password="pw")
        result = await client.authenticate(otp_code="654321")

        assert result is True
        mock_begin.assert_called_once()
        mock_complete.assert_called_once_with("ch-001", "654321")
        await client.close()


# ---------------------------------------------------------------------------
# complete_authentication() — both paths (lines ~689-714)
# ---------------------------------------------------------------------------


class TestCompleteAuthentication:
    @pytest.mark.asyncio
    async def test_no_pending_challenge_raises_auth_error(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="No pending"):
            await client.complete_authentication("123456")
        await client.close()

    @patch("libdyson_rest.async_client.AsyncDysonClient.complete_login")
    @pytest.mark.asyncio
    async def test_success_clears_challenge_and_returns_true(
        self, mock_complete: Mock
    ) -> None:
        mock_complete.return_value = Mock()

        client = AsyncDysonClient(email="test@example.com", password="pw")
        client._current_challenge_id = "ch-pending"

        result = await client.complete_authentication("999888")

        assert result is True
        assert client._current_challenge_id is None
        mock_complete.assert_called_once_with("ch-pending", "999888")
        await client.close()


# ---------------------------------------------------------------------------
# Mobile login methods
# ---------------------------------------------------------------------------


class TestGetUserStatusMobile:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_success_returns_user_status(self, mock_post: Mock) -> None:
        mock_post.return_value = _ok(
            {"accountStatus": "ACTIVE", "authenticationMethod": "EMAIL_PWD_2FA"}
        )
        client = AsyncDysonClient()
        result = await client.get_user_status_mobile(mobile="+8613800000000")
        assert result is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_no_mobile_raises_auth_error(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Mobile number required"):
            await client.get_user_status_mobile()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_request_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = httpx.RequestError("timeout")
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.get_user_status_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_http_status_error_raises_connection_error(
        self, mock_post: Mock
    ) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.get_user_status_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient()
        with pytest.raises(DysonAPIError):
            await client.get_user_status_mobile(mobile="+8613800000000")
        await client.close()


class TestBeginLoginMobile:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_success_returns_challenge(self, mock_post: Mock) -> None:
        mock_post.return_value = _ok(
            {"challengeId": "12345678-1234-5678-9abc-123456789abc"}
        )
        client = AsyncDysonClient()
        challenge = await client.begin_login_mobile(mobile="+8613800000000")
        assert challenge is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_no_mobile_raises_auth_error(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Mobile number required"):
            await client.begin_login_mobile()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, mock_post: Mock) -> None:
        mock_r = Mock()
        mock_r.status_code = 401
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_r
        )
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Invalid mobile number"):
            await client.begin_login_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_400_raises_auth_error(self, mock_post: Mock) -> None:
        mock_r = Mock()
        mock_r.status_code = 400
        mock_r.text = "Bad Request"
        mock_r.url = "https://api.example.com/mobile/auth"
        mock_post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_r
        )
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Bad request"):
            await client.begin_login_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.begin_login_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_request_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = httpx.RequestError("timeout")
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.begin_login_mobile(mobile="+8613800000000")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient()
        with pytest.raises(DysonAPIError):
            await client.begin_login_mobile(mobile="+8613800000000")
        await client.close()


class TestCompleteLoginMobile:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_success_stores_token(self, mock_post: Mock) -> None:
        mock_post.return_value = _ok(LOGIN_INFO_RESPONSE)
        client = AsyncDysonClient()
        login_info = await client.complete_login_mobile(
            "ch-001", "123456", mobile="+8613800000000"
        )
        assert login_info is not None
        assert client.auth_token == "mobile_test_token_123"
        await client.close()

    @pytest.mark.asyncio
    async def test_no_mobile_raises_auth_error(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Mobile number is required"):
            await client.complete_login_mobile("ch-001", "123456")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, mock_post: Mock) -> None:
        mock_r = Mock()
        mock_r.status_code = 401
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_r
        )
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Invalid credentials"):
            await client.complete_login_mobile(
                "ch-001", "123456", mobile="+8613800000000"
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_400_raises_auth_error(self, mock_post: Mock) -> None:
        mock_r = Mock()
        mock_r.status_code = 400
        mock_r.text = "Bad Request"
        mock_r.url = "https://api.example.com/mobile/verify"
        mock_post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_r
        )
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError, match="Bad request"):
            await client.complete_login_mobile(
                "ch-001", "123456", mobile="+8613800000000"
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.complete_login_mobile(
                "ch-001", "123456", mobile="+8613800000000"
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_request_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = httpx.RequestError("timeout")
        client = AsyncDysonClient()
        with pytest.raises(DysonConnectionError):
            await client.complete_login_mobile(
                "ch-001", "123456", mobile="+8613800000000"
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient()
        with pytest.raises(DysonAPIError):
            await client.complete_login_mobile(
                "ch-001", "123456", mobile="+8613800000000"
            )
        await client.close()


# ---------------------------------------------------------------------------
# Core data method error paths
# ---------------------------------------------------------------------------


class TestGetDevicesErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_devices()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_non_list_response_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _ok({"error": "unexpected"})
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list"):
            await client.get_devices()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_devices()
        await client.close()


class TestGetIotCredentialsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_iot_credentials(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_iot_credentials(SERIAL)
        await client.close()


class TestGetPendingReleaseErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_pending_release(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_pending_release(SERIAL)
        await client.close()


class TestTriggerFirmwareUpdateErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_404_raises_api_error(self, mock_post: Mock) -> None:
        mock_r = Mock()
        mock_r.status_code = 404
        mock_post.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_r
        )
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="not found"):
            await client.trigger_firmware_update(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_non_204_raises_api_error(self, mock_post: Mock) -> None:
        mock_r = _ok(None)
        mock_r.status_code = 200  # not 204
        mock_post.return_value = mock_r
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Unexpected response"):
            await client.trigger_firmware_update(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_connection_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.trigger_firmware_update(SERIAL)
        await client.close()


# ---------------------------------------------------------------------------
# set_auth_token with initialized client (lines ~1037)
# ---------------------------------------------------------------------------


class TestSetAuthTokenWithClient:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_set_auth_token_updates_initialized_client_headers(
        self, mock_get: Mock
    ) -> None:
        mock_get.return_value = _ok("1.0")
        client = AsyncDysonClient()
        await client.provision()  # initializes self._client
        client.set_auth_token("new-token-123")
        assert client.auth_token == "new-token-123"
        await client.close()


# ---------------------------------------------------------------------------
# Original robot method error paths (lines 1091–1491)
# ---------------------------------------------------------------------------


class TestGetCleanMapsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_maps(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_maps(SERIAL, api_version=2)
        await client.close()


class TestGetPersistentMapMetadataErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_persistent_map_metadata(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_persistent_map_metadata(SERIAL, api_version=2)
        await client.close()


class TestGetPersistentMapErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)
        await client.close()


class TestGetRecommendedCleansErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_recommended_cleans(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_recommended_cleans(SERIAL)
        await client.close()


class TestSetZoneBehaviourErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, "auto")
        await client.close()


class TestGetDailyEnvironmentDataErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_daily_environment_data(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_daily_environment_data(SERIAL)
        await client.close()


class TestGetScheduledEventsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_scheduled_events(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_scheduled_events(SERIAL)
        await client.close()


class TestGetOutdoorEnvironmentDataErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_outdoor_environment_data(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_outdoor_environment_data(SERIAL)
        await client.close()


# ---------------------------------------------------------------------------
# New robot method error paths (lines 1499–2035)
# ---------------------------------------------------------------------------


class TestGetCleanMapDataErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
        await client.close()


class TestUpdatePersistentMapErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.update_persistent_map(SERIAL, MAP_ID)
        await client.close()


class TestDeletePersistentMapErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.delete")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_delete: Mock) -> None:
        mock_delete.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.delete_persistent_map(SERIAL, MAP_ID)
        await client.close()


class TestUpdateMapMetadataErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.update_map_metadata(SERIAL, MAP_ID)
        await client.close()


class TestGetCleanEstimationErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_estimation(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_clean_estimation(SERIAL, MAP_ID)
        await client.close()


class TestGetRestrictionsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_restrictions(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_restrictions(SERIAL, MAP_ID)
        await client.close()


class TestUpdateRestrictionsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.update_restrictions(SERIAL, MAP_ID, {})
        await client.close()


class TestDivideZoneErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.divide_zone(SERIAL, MAP_ID, {})
        await client.close()


class TestMergeZonesErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.merge_zones(SERIAL, MAP_ID, {})
        await client.close()


class TestGetLiveMapCleaningErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_live_map_cleaning(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_live_map_cleaning(SERIAL)
        await client.close()


class TestGetLiveMapMappingErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_live_map_mapping(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_live_map_mapping(SERIAL)
        await client.close()


class TestSetScheduledEventsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.set_scheduled_events(SERIAL, True, [])
        await client.close()


class TestGetScheduleBinaryErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_schedule_binary(SERIAL)
        await client.close()


# ---------------------------------------------------------------------------
# New device method error paths (lines 2036–2762)
# ---------------------------------------------------------------------------


class TestGetTimezoneErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_timezone(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_timezone(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_non_dict_response_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _ok(["not", "a", "dict"])
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_timezone(SERIAL)
        await client.close()


class TestSetTimezoneErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.set_timezone(SERIAL, "UTC")
        await client.close()


class TestGetOtaInfoErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_ota_info(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_ota_info(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_non_dict_response_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _ok(["not", "a", "dict"])
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_ota_info(SERIAL)
        await client.close()


class TestIsBannedMachineErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.is_banned_machine(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.is_banned_machine(SERIAL)
        await client.close()


class TestGetFeatureSupportErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_feature_support()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_feature_support()
        await client.close()


class TestGetVoiceLanguagesErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_voice_languages(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_voice_languages(SERIAL)
        await client.close()


class TestGetEnvironmentHistoryErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_environment_history(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_environment_history(SERIAL)
        await client.close()


class TestGetEnergyInsightsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_energy_insights(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_energy_insights(SERIAL)
        await client.close()


class TestGetProductFaultsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_faults(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_faults(SERIAL)
        await client.close()


class TestGetProductGuideErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_guide(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_guide(SERIAL)
        await client.close()


class TestGetProductVoiceCommandsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_voice_commands(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_product_voice_commands(SERIAL)
        await client.close()


class TestRegisterPushTokenErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.register_push_token("app-001", "token123", "android")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_post: Mock) -> None:
        mock_post.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.register_push_token("app-001", "token123", "android")
        await client.close()


class TestGetNotificationPermissionsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_notification_permissions("app-001", SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_notification_permissions("app-001", SERIAL)
        await client.close()


class TestUpdateNotificationPermissionsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.update_notification_permissions("app-001", SERIAL, {})
        await client.close()


class TestGetRegisteredProductsErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_registered_products()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_parse_error_raises_api_error(self, mock_get: Mock) -> None:
        mock_get.return_value = _json_error(Mock())
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.get_registered_products()
        await client.close()


class TestRegisterNcpErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.register_ncp({})
        await client.close()


class TestRegisterNspErrorPaths:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_server_error_raises_api_error(self, mock_put: Mock) -> None:
        mock_put.side_effect = _server_error()
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError):
            await client.register_nsp({})
        await client.close()
