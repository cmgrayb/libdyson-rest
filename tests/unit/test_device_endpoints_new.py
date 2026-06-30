"""Unit tests for device management, product support, push notification,
and smart home (NCP/NSP) endpoints added in v0.16+."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SERIAL = "AB1-CD-EF234567"
APP_ID = "my-app-001"

TIMEZONE_RESPONSE = {"timezone": "Europe/London"}
OTA_RESPONSE = {"currentFirmware": "1.2.3", "latestFirmware": "1.3.0"}
FEATURE_SUPPORT_RESPONSE = {"featureA": True, "featureB": False}
ENV_HISTORY_RESPONSE = {"days": [{"date": "2024-06-01", "aql": 1.0}]}
ENERGY_INSIGHTS_RESPONSE = {"year": 2024, "month": 6, "totalKwh": 4.5}
PRODUCT_FAULTS_RESPONSE = {
    "faults": [{"code": "F001", "description": "Filter clogged"}]
}
PRODUCT_GUIDE_RESPONSE = {"sections": [{"title": "Getting started", "content": "..."}]}
VOICE_COMMANDS_RESPONSE = {
    "commands": [{"phrase": "Start cleaning", "action": "clean"}]
}
PUSH_REG_RESPONSE = {"registrationId": "reg-001"}
NOTIF_PERMS_RESPONSE = {"alerts": True, "updates": False}
NCP_PRODUCTS_RESPONSE = {"products": [{"serial": SERIAL, "type": "vacuum"}]}


# ===========================================================================
# Synchronous client — Device management
# ===========================================================================


class TestSyncGetTimezone:
    @patch("httpx.Client.get")
    def test_success_returns_timezone_string(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = TIMEZONE_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_timezone(SERIAL)

        assert result == "Europe/London"

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = TIMEZONE_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_timezone(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/machine/{SERIAL}/timezone" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_timezone(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_auth_error_on_401(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.get_timezone(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_timezone(SERIAL)

    @patch("httpx.Client.get")
    def test_returns_none_when_no_timezone_key(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_timezone(SERIAL)

        assert result is None


class TestSyncSetTimezone:
    @patch("httpx.Client.put")
    def test_success_sends_timezone_in_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_timezone(SERIAL, "America/New_York")

        assert mock_put.call_args.kwargs["json"] == {"timezone": "America/New_York"}

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_timezone(SERIAL, "UTC")

        url = mock_put.call_args.args[0]
        assert f"/v1/machine/{SERIAL}/timezone" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.set_timezone(SERIAL, "UTC")

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.set_timezone(SERIAL, "UTC")


class TestSyncGetOtaInfo:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = OTA_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_ota_info(SERIAL)

        assert isinstance(result, dict)
        assert result["latestFirmware"] == "1.3.0"

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = OTA_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_ota_info(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/assets/devices/{SERIAL}/ota" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_ota_info(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_ota_info(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_ota_info(SERIAL)


class TestSyncIsBannedMachine:
    @patch("httpx.Client.get")
    def test_returns_true_when_banned_key_true(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"banned": True}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        assert client.is_banned_machine(SERIAL) is True

    @patch("httpx.Client.get")
    def test_returns_false_when_not_banned(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"banned": False}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        assert client.is_banned_machine(SERIAL) is False

    @patch("httpx.Client.get")
    def test_returns_false_when_key_missing(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        assert client.is_banned_machine(SERIAL) is False

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"banned": False}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.is_banned_machine(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/bannedmachine/{SERIAL}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.is_banned_machine(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.is_banned_machine(SERIAL)


class TestSyncGetFeatureSupport:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = FEATURE_SUPPORT_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_feature_support()

        assert isinstance(result, dict)
        assert result["featureA"] is True

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = FEATURE_SUPPORT_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_feature_support()

        url = mock_get.call_args.args[0]
        assert "/v1/featuresupport" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_feature_support()

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_feature_support()

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_feature_support()


class TestSyncGetVoiceLanguages:
    @patch("httpx.Client.get")
    def test_success_returns_list_directly(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ["en-GB", "fr-FR"]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_voice_languages(SERIAL)

        assert result == ["en-GB", "fr-FR"]

    @patch("httpx.Client.get")
    def test_success_unwraps_dict_with_languages_key(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"languages": ["de-DE", "es-ES"]}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_voice_languages(SERIAL)

        assert result == ["de-DE", "es-ES"]

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_voice_languages(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/package/voice/{SERIAL}/languages" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_voice_languages(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_voice_languages(SERIAL)


# ===========================================================================
# Synchronous client — EC additional
# ===========================================================================


class TestSyncGetEnvironmentHistory:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENV_HISTORY_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_environment_history(SERIAL)

        assert isinstance(result, dict)
        assert "days" in result

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENV_HISTORY_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_environment_history(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/messageprocessor/devices/{SERIAL}/environmentdailyhistory" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_environment_history(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_environment_history(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_environment_history(SERIAL)


class TestSyncGetEnergyInsights:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_energy_insights(SERIAL)

        assert isinstance(result, dict)
        assert result["totalKwh"] == 4.5

    @patch("httpx.Client.get")
    def test_year_and_month_sent_as_params(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_energy_insights(SERIAL, year=2024, month=6)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["params"] == {"year": "2024", "month": "6"}

    @patch("httpx.Client.get")
    def test_no_params_when_not_provided(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_energy_insights(SERIAL)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["params"] == {}

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_energy_insights(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/insights/ec/{SERIAL}/monthly" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_energy_insights(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_energy_insights(SERIAL)


# ===========================================================================
# Synchronous client — Product support
# ===========================================================================


class TestSyncGetProductFaults:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_FAULTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_product_faults(SERIAL)

        assert isinstance(result, dict)
        assert "faults" in result

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_FAULTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_product_faults(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-faults/{SERIAL}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_product_faults(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_product_faults(SERIAL)


class TestSyncGetProductGuide:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_GUIDE_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_product_guide(SERIAL)

        assert isinstance(result, dict)

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_GUIDE_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_product_guide(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-guide/{SERIAL}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_product_guide(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_product_guide(SERIAL)


class TestSyncGetProductVoiceCommands:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = VOICE_COMMANDS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_product_voice_commands(SERIAL)

        assert isinstance(result, dict)

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = VOICE_COMMANDS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_product_voice_commands(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-voice-commands/{SERIAL}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_product_voice_commands(SERIAL)


# ===========================================================================
# Synchronous client — Push notifications
# ===========================================================================


class TestSyncRegisterPushToken:
    @patch("httpx.Client.post")
    def test_success_returns_dict(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.register_push_token(APP_ID, "my-token", "ios")

        assert isinstance(result, dict)
        assert result["registrationId"] == "reg-001"

    @patch("httpx.Client.post")
    def test_correct_body_without_serial_numbers(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.register_push_token(APP_ID, "tok-abc", "android")

        body = mock_post.call_args.kwargs["json"]
        assert body["applicationId"] == APP_ID
        assert body["token"] == "tok-abc"
        assert body["platform"] == "android"
        assert "serialNumbers" not in body

    @patch("httpx.Client.post")
    def test_serial_numbers_included_when_provided(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.register_push_token(APP_ID, "tok", "ios", serial_numbers=[SERIAL])

        body = mock_post.call_args.kwargs["json"]
        assert body["serialNumbers"] == [SERIAL]

    @patch("httpx.Client.post")
    def test_correct_url(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.register_push_token(APP_ID, "tok", "ios")

        url = mock_post.call_args.args[0]
        assert "/v1/notifier/applications" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.register_push_token(APP_ID, "tok", "ios")

    @patch("httpx.Client.post")
    def test_raises_connection_error_on_network_failure(self, mock_post: Mock) -> None:
        mock_post.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.register_push_token(APP_ID, "tok", "ios")


class TestSyncGetNotificationPermissions:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NOTIF_PERMS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_notification_permissions(APP_ID, SERIAL)

        assert isinstance(result, dict)

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NOTIF_PERMS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_notification_permissions(APP_ID, SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v2/notifier/applications/{APP_ID}/permissions/{SERIAL}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_notification_permissions(APP_ID, SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_notification_permissions(APP_ID, SERIAL)


class TestSyncUpdateNotificationPermissions:
    @patch("httpx.Client.put")
    def test_success_sends_serial_and_permissions(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        perms = {"alerts": True, "updates": False}
        client = DysonClient(auth_token="tok")
        client.update_notification_permissions(APP_ID, SERIAL, perms)

        body = mock_put.call_args.kwargs["json"]
        assert body["serialNumber"] == SERIAL
        assert body["alerts"] is True

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_notification_permissions(APP_ID, SERIAL, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/notifier/applications/{APP_ID}/permissions" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.update_notification_permissions(APP_ID, SERIAL, {})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.update_notification_permissions(APP_ID, SERIAL, {})


# ===========================================================================
# Synchronous client — Smart home (NCP/NSP)
# ===========================================================================


class TestSyncGetRegisteredProducts:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NCP_PRODUCTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_registered_products()

        assert isinstance(result, dict)
        assert "products" in result

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NCP_PRODUCTS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_registered_products()

        url = mock_get.call_args.args[0]
        assert "/v1/ncp/product/registered" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_registered_products()

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_registered_products()


class TestSyncRegisterNcp:
    @patch("httpx.Client.put")
    def test_success_sends_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"deviceId": "dev-001"}
        client = DysonClient(auth_token="tok")
        client.register_ncp(body)

        assert mock_put.call_args.kwargs["json"] == body

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.register_ncp({})

        url = mock_put.call_args.args[0]
        assert "/v1/ncp/register" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.register_ncp({})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.register_ncp({})


class TestSyncRegisterNsp:
    @patch("httpx.Client.put")
    def test_success_sends_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"deviceId": "dev-002"}
        client = DysonClient(auth_token="tok")
        client.register_nsp(body)

        assert mock_put.call_args.kwargs["json"] == body

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.register_nsp({})

        url = mock_put.call_args.args[0]
        assert "/v1/nsp/register" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.register_nsp({})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.register_nsp({})


# ===========================================================================
# Asynchronous client — Device management
# ===========================================================================


class TestAsyncGetTimezone:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_timezone_string(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = TIMEZONE_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_timezone(SERIAL)

        assert result == "Europe/London"
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = TIMEZONE_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_timezone(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/machine/{SERIAL}/timezone" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_timezone(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_timezone(SERIAL)
        await client.close()


class TestAsyncSetTimezone:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_timezone_in_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_timezone(SERIAL, "Asia/Tokyo")

        assert mock_put.call_args.kwargs["json"] == {"timezone": "Asia/Tokyo"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_timezone(SERIAL, "UTC")

        url = mock_put.call_args.args[0]
        assert f"/v1/machine/{SERIAL}/timezone" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.set_timezone(SERIAL, "UTC")
        await client.close()


class TestAsyncGetOtaInfo:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = OTA_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_ota_info(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = OTA_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_ota_info(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/assets/devices/{SERIAL}/ota" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_ota_info(SERIAL)
        await client.close()


class TestAsyncIsBannedMachine:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_returns_true_when_banned(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"banned": True}
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        assert await client.is_banned_machine(SERIAL) is True
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_returns_false_when_not_banned(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"banned": False}
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        assert await client.is_banned_machine(SERIAL) is False
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.is_banned_machine(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/bannedmachine/{SERIAL}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.is_banned_machine(SERIAL)
        await client.close()


class TestAsyncGetFeatureSupport:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = FEATURE_SUPPORT_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_feature_support()

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = FEATURE_SUPPORT_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_feature_support()

        url = mock_get.call_args.args[0]
        assert "/v1/featuresupport" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_feature_support()
        await client.close()


class TestAsyncGetVoiceLanguages:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_list(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ["en-GB", "fr-FR"]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_voice_languages(SERIAL)

        assert result == ["en-GB", "fr-FR"]
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_voice_languages(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/package/voice/{SERIAL}/languages" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_voice_languages(SERIAL)
        await client.close()


# ===========================================================================
# Asynchronous client — EC additional
# ===========================================================================


class TestAsyncGetEnvironmentHistory:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENV_HISTORY_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_environment_history(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENV_HISTORY_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_environment_history(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/messageprocessor/devices/{SERIAL}/environmentdailyhistory" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_environment_history(SERIAL)
        await client.close()


class TestAsyncGetEnergyInsights:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_energy_insights(SERIAL, year=2024, month=6)

        assert isinstance(result, dict)
        assert mock_get.call_args.kwargs["params"] == {"year": "2024", "month": "6"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = ENERGY_INSIGHTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_energy_insights(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/insights/ec/{SERIAL}/monthly" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_energy_insights(SERIAL)
        await client.close()


# ===========================================================================
# Asynchronous client — Product support
# ===========================================================================


class TestAsyncGetProductFaults:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_FAULTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_product_faults(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_FAULTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_product_faults(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-faults/{SERIAL}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_product_faults(SERIAL)
        await client.close()


class TestAsyncGetProductGuide:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_GUIDE_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_product_guide(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PRODUCT_GUIDE_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_product_guide(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-guide/{SERIAL}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_product_guide(SERIAL)
        await client.close()


class TestAsyncGetProductVoiceCommands:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = VOICE_COMMANDS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_product_voice_commands(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = VOICE_COMMANDS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_product_voice_commands(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/support/product-voice-commands/{SERIAL}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_product_voice_commands(SERIAL)
        await client.close()


# ===========================================================================
# Asynchronous client — Push notifications
# ===========================================================================


class TestAsyncRegisterPushToken:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_post: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.register_push_token(APP_ID, "tok-abc", "ios")

        assert isinstance(result, dict)
        body = mock_post.call_args.kwargs["json"]
        assert body["applicationId"] == APP_ID
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_post: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PUSH_REG_RESPONSE
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.register_push_token(APP_ID, "tok", "android")

        url = mock_post.call_args.args[0]
        assert "/v1/notifier/applications" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.register_push_token(APP_ID, "tok", "ios")
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_post: AsyncMock
    ) -> None:
        mock_post.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.register_push_token(APP_ID, "tok", "ios")
        await client.close()


class TestAsyncGetNotificationPermissions:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NOTIF_PERMS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_notification_permissions(APP_ID, SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NOTIF_PERMS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_notification_permissions(APP_ID, SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v2/notifier/applications/{APP_ID}/permissions/{SERIAL}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_notification_permissions(APP_ID, SERIAL)
        await client.close()


class TestAsyncUpdateNotificationPermissions:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_serial_and_permissions(
        self, mock_put: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        perms = {"alerts": True}
        client = AsyncDysonClient(auth_token="tok")
        await client.update_notification_permissions(APP_ID, SERIAL, perms)

        body = mock_put.call_args.kwargs["json"]
        assert body["serialNumber"] == SERIAL
        assert body["alerts"] is True
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_notification_permissions(APP_ID, SERIAL, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/notifier/applications/{APP_ID}/permissions" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.update_notification_permissions(APP_ID, SERIAL, {})
        await client.close()


# ===========================================================================
# Asynchronous client — Smart home (NCP/NSP)
# ===========================================================================


class TestAsyncGetRegisteredProducts:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NCP_PRODUCTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_registered_products()

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = NCP_PRODUCTS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_registered_products()

        url = mock_get.call_args.args[0]
        assert "/v1/ncp/product/registered" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_registered_products()
        await client.close()


class TestAsyncRegisterNcp:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url_and_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"deviceId": "dev-001"}
        client = AsyncDysonClient(auth_token="tok")
        await client.register_ncp(body)

        url = mock_put.call_args.args[0]
        assert "/v1/ncp/register" in url
        assert mock_put.call_args.kwargs["json"] == body
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.register_ncp({})
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_put: AsyncMock
    ) -> None:
        mock_put.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.register_ncp({})
        await client.close()


class TestAsyncRegisterNsp:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url_and_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"deviceId": "dev-002"}
        client = AsyncDysonClient(auth_token="tok")
        await client.register_nsp(body)

        url = mock_put.call_args.args[0]
        assert "/v1/nsp/register" in url
        assert mock_put.call_args.kwargs["json"] == body
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.register_nsp({})
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_put: AsyncMock
    ) -> None:
        mock_put.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.register_nsp({})
        await client.close()
