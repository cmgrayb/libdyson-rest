"""Unit tests for new robot vacuum endpoints added in v0.16+."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

SERIAL = "AB1-CD-EF234567"
MAP_ID = "pm-001"
ZONE_ID = "zone-A"
CLEAN_ID = "cr-007"

CLEAN_MAP_DATA_RESPONSE = {
    "cleanId": CLEAN_ID,
    "duration": 1800,
    "area": 22.5,
    "path": [],
}

CLEAN_ESTIMATION_RESPONSE = {
    "estimatedDuration": 900,
    "estimatedArea": 15.0,
}

RESTRICTIONS_RESPONSE = {
    "noGoZones": [{"id": "ngz-1", "vertices": []}],
    "keepOutAreas": [],
}

LIVE_MAP_RESPONSE = {
    "robotPosition": {"x": 1.0, "y": 2.0},
    "footprint": [],
}

SCHEDULE_EVENTS_PAYLOAD = [
    {
        "enabled": True,
        "days": [0, 2],
        "startTime": "07:30",
        "settings": {"cleaningMode": "auto"},
    }
]


# ===========================================================================
# Synchronous client tests
# ===========================================================================


class TestSyncGetCleanMapData:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_MAP_DATA_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_clean_map_data(SERIAL, CLEAN_ID)

        assert isinstance(result, dict)
        assert result["cleanId"] == CLEAN_ID
        mock_get.assert_called_once()

    @patch("httpx.Client.get")
    def test_correct_url_includes_serial_and_clean_id(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_MAP_DATA_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_map_data(SERIAL, CLEAN_ID)

        url = mock_get.call_args.args[0]
        assert f"/v2/{SERIAL}/clean-maps-data/{CLEAN_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_clean_map_data(SERIAL, CLEAN_ID)

    @patch("httpx.Client.get")
    def test_raises_auth_error_on_401(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.get_clean_map_data(SERIAL, CLEAN_ID)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_clean_map_data(SERIAL, CLEAN_ID)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [CLEAN_MAP_DATA_RESPONSE]
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_clean_map_data(SERIAL, CLEAN_ID)


class TestSyncUpdatePersistentMap:
    @patch("httpx.Client.put")
    def test_success_sends_name_in_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_persistent_map(SERIAL, MAP_ID, name="Downstairs")

        mock_put.assert_called_once()
        assert mock_put.call_args.kwargs["json"] == {"name": "Downstairs"}

    @patch("httpx.Client.put")
    def test_empty_body_when_no_name(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_persistent_map(SERIAL, MAP_ID)

        assert mock_put.call_args.kwargs["json"] == {}

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_persistent_map(SERIAL, MAP_ID)

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.update_persistent_map(SERIAL, MAP_ID)

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.update_persistent_map(SERIAL, MAP_ID)


class TestSyncDeletePersistentMap:
    @patch("httpx.Client.delete")
    def test_success_calls_delete(self, mock_delete: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.delete_persistent_map(SERIAL, MAP_ID)

        mock_delete.assert_called_once()

    @patch("httpx.Client.delete")
    def test_correct_url(self, mock_delete: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.delete_persistent_map(SERIAL, MAP_ID)

        url = mock_delete.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.delete_persistent_map(SERIAL, MAP_ID)

    @patch("httpx.Client.delete")
    def test_raises_auth_error_on_401(self, mock_delete: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_delete.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.delete_persistent_map(SERIAL, MAP_ID)

    @patch("httpx.Client.delete")
    def test_raises_connection_error_on_network_failure(
        self, mock_delete: Mock
    ) -> None:
        mock_delete.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.delete_persistent_map(SERIAL, MAP_ID)


class TestSyncUpdateMapMetadata:
    @patch("httpx.Client.put")
    def test_success_sends_name_in_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_map_metadata(SERIAL, MAP_ID, name="New Name")

        assert mock_put.call_args.kwargs["json"] == {"name": "New Name"}

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_map_metadata(SERIAL, MAP_ID)

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-map-metadata/{MAP_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.update_map_metadata(SERIAL, MAP_ID)

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.update_map_metadata(SERIAL, MAP_ID)


class TestSyncGetCleanEstimation:
    @patch("httpx.Client.post")
    def test_success_returns_dict(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_clean_estimation(SERIAL, MAP_ID, zone_ids=[ZONE_ID])

        assert isinstance(result, dict)
        assert "estimatedDuration" in result

    @patch("httpx.Client.post")
    def test_zone_ids_sent_in_body(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_estimation(SERIAL, MAP_ID, zone_ids=["z1", "z2"])

        assert mock_post.call_args.kwargs["json"] == {"zoneIds": ["z1", "z2"]}

    @patch("httpx.Client.post")
    def test_empty_body_when_no_zone_ids(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_estimation(SERIAL, MAP_ID)

        assert mock_post.call_args.kwargs["json"] == {}

    @patch("httpx.Client.post")
    def test_correct_url(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_estimation(SERIAL, MAP_ID)

        url = mock_post.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}/clean-estimation" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_clean_estimation(SERIAL, MAP_ID)

    @patch("httpx.Client.post")
    def test_raises_connection_error_on_network_failure(self, mock_post: Mock) -> None:
        mock_post.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_clean_estimation(SERIAL, MAP_ID)

    @patch("httpx.Client.post")
    def test_raises_api_error_on_non_dict_response(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [CLEAN_ESTIMATION_RESPONSE]
        mock_post.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_clean_estimation(SERIAL, MAP_ID)


class TestSyncGetRestrictions:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = RESTRICTIONS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_restrictions(SERIAL, MAP_ID)

        assert isinstance(result, dict)
        assert "noGoZones" in result

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = RESTRICTIONS_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_restrictions(SERIAL, MAP_ID)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/restrictions-definitions/{MAP_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_restrictions(SERIAL, MAP_ID)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_restrictions(SERIAL, MAP_ID)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_restrictions(SERIAL, MAP_ID)


class TestSyncUpdateRestrictions:
    @patch("httpx.Client.put")
    def test_success_sends_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_restrictions(SERIAL, MAP_ID, RESTRICTIONS_RESPONSE)

        mock_put.assert_called_once()
        assert mock_put.call_args.kwargs["json"] == RESTRICTIONS_RESPONSE

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.update_restrictions(SERIAL, MAP_ID, RESTRICTIONS_RESPONSE)

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/restrictions-definitions/{MAP_ID}" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.update_restrictions(SERIAL, MAP_ID, {})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.update_restrictions(SERIAL, MAP_ID, {})


class TestSyncDivideZone:
    @patch("httpx.Client.put")
    def test_success_sends_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"sourceZoneId": ZONE_ID, "divisionLine": []}
        client = DysonClient(auth_token="tok")
        client.divide_zone(SERIAL, MAP_ID, body)

        assert mock_put.call_args.kwargs["json"] == body

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.divide_zone(SERIAL, MAP_ID, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/zones-definitions/{MAP_ID}/divide-zone" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.divide_zone(SERIAL, MAP_ID, {})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.divide_zone(SERIAL, MAP_ID, {})


class TestSyncMergeZones:
    @patch("httpx.Client.put")
    def test_success_sends_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        body = {"sourceZoneIds": [ZONE_ID, "zone-B"]}
        client = DysonClient(auth_token="tok")
        client.merge_zones(SERIAL, MAP_ID, body)

        assert mock_put.call_args.kwargs["json"] == body

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.merge_zones(SERIAL, MAP_ID, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/zones-definitions/{MAP_ID}/merge-zones" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.merge_zones(SERIAL, MAP_ID, {})

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.merge_zones(SERIAL, MAP_ID, {})


class TestSyncGetLiveMapCleaning:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_live_map_cleaning(SERIAL)

        assert isinstance(result, dict)
        assert "robotPosition" in result

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_live_map_cleaning(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/live-maps/cleaning" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_live_map_cleaning(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_live_map_cleaning(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_live_map_cleaning(SERIAL)


class TestSyncGetLiveMapMapping:
    @patch("httpx.Client.get")
    def test_success_returns_dict(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_live_map_mapping(SERIAL)

        assert isinstance(result, dict)

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_live_map_mapping(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/live-maps/mapping" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_live_map_mapping(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_live_map_mapping(SERIAL)


class TestSyncSetScheduledEvents:
    @patch("httpx.Client.put")
    def test_success_sends_correct_body(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_scheduled_events(
            SERIAL, enabled=True, events=SCHEDULE_EVENTS_PAYLOAD
        )

        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["json"]["enabled"] is True
        assert call_kwargs["json"]["events"] == SCHEDULE_EVENTS_PAYLOAD

    @patch("httpx.Client.put")
    def test_product_type_sent_as_query_param(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_scheduled_events(
            SERIAL, enabled=True, events=[], product_type="438K"
        )

        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["params"] == {"productType": "438K"}

    @patch("httpx.Client.put")
    def test_no_params_when_no_product_type(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_scheduled_events(SERIAL, enabled=False, events=[])

        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs.get("params") == {}

    @patch("httpx.Client.put")
    def test_correct_url(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_scheduled_events(SERIAL, enabled=True, events=[])

        url = mock_put.call_args.args[0]
        assert f"/v1/unifiedscheduler/{SERIAL}/events" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.set_scheduled_events(SERIAL, enabled=True, events=[])

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.set_scheduled_events(SERIAL, enabled=True, events=[])


class TestSyncGetScheduleBinary:
    @patch("httpx.Client.get")
    def test_success_returns_bytes(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"\x00\x01\x02\x03"
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        result = client.get_schedule_binary(SERIAL)

        assert isinstance(result, bytes)
        assert result == b"\x00\x01\x02\x03"

    @patch("httpx.Client.get")
    def test_correct_url(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b""
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_schedule_binary(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/unifiedscheduler/{SERIAL}/app/schedule.bin" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_schedule_binary(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("down")
        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_schedule_binary(SERIAL)


# ===========================================================================
# Asynchronous client tests
# ===========================================================================


class TestAsyncGetCleanMapData:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_MAP_DATA_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_clean_map_data(SERIAL, CLEAN_ID)

        assert isinstance(result, dict)
        assert result["cleanId"] == CLEAN_ID
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_MAP_DATA_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_clean_map_data(SERIAL, CLEAN_ID)

        url = mock_get.call_args.args[0]
        assert f"/v2/{SERIAL}/clean-maps-data/{CLEAN_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
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
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("timeout")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_dict_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [CLEAN_MAP_DATA_RESPONSE]
        mock_get.return_value = mock_response
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_clean_map_data(SERIAL, CLEAN_ID)
        await client.close()


class TestAsyncUpdatePersistentMap:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_name_in_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_persistent_map(SERIAL, MAP_ID, name="New")

        assert mock_put.call_args.kwargs["json"] == {"name": "New"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_persistent_map(SERIAL, MAP_ID)

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.update_persistent_map(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_put: AsyncMock
    ) -> None:
        mock_put.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.update_persistent_map(SERIAL, MAP_ID)
        await client.close()


class TestAsyncDeletePersistentMap:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.delete")
    @pytest.mark.asyncio
    async def test_success_calls_delete(self, mock_delete: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.delete_persistent_map(SERIAL, MAP_ID)

        mock_delete.assert_called_once()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.delete")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_delete: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.delete_persistent_map(SERIAL, MAP_ID)

        url = mock_delete.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.delete_persistent_map(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.delete")
    @pytest.mark.asyncio
    async def test_raises_auth_error_on_401(self, mock_delete: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_delete.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            await client.delete_persistent_map(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.delete")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_delete: AsyncMock
    ) -> None:
        mock_delete.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.delete_persistent_map(SERIAL, MAP_ID)
        await client.close()


class TestAsyncUpdateMapMetadata:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_name(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_map_metadata(SERIAL, MAP_ID, name="Ground Floor")

        assert mock_put.call_args.kwargs["json"] == {"name": "Ground Floor"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_map_metadata(SERIAL, MAP_ID)

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-map-metadata/{MAP_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.update_map_metadata(SERIAL, MAP_ID)
        await client.close()


class TestAsyncGetCleanEstimation:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_post: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_clean_estimation(SERIAL, MAP_ID, zone_ids=["z1"])

        assert isinstance(result, dict)
        assert mock_post.call_args.kwargs["json"] == {"zoneIds": ["z1"]}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_post: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = CLEAN_ESTIMATION_RESPONSE
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_clean_estimation(SERIAL, MAP_ID)

        url = mock_post.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}/clean-estimation" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_clean_estimation(SERIAL, MAP_ID)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_post: AsyncMock
    ) -> None:
        mock_post.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_clean_estimation(SERIAL, MAP_ID)
        await client.close()


class TestAsyncGetRestrictions:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = RESTRICTIONS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_restrictions(SERIAL, MAP_ID)

        assert isinstance(result, dict)
        assert "noGoZones" in result
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = RESTRICTIONS_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_restrictions(SERIAL, MAP_ID)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/restrictions-definitions/{MAP_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_restrictions(SERIAL, MAP_ID)
        await client.close()


class TestAsyncUpdateRestrictions:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_restrictions(SERIAL, MAP_ID, RESTRICTIONS_RESPONSE)

        assert mock_put.call_args.kwargs["json"] == RESTRICTIONS_RESPONSE
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.update_restrictions(SERIAL, MAP_ID, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/restrictions-definitions/{MAP_ID}" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.update_restrictions(SERIAL, MAP_ID, {})
        await client.close()


class TestAsyncDivideZone:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.divide_zone(SERIAL, MAP_ID, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/zones-definitions/{MAP_ID}/divide-zone" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.divide_zone(SERIAL, MAP_ID, {})
        await client.close()


class TestAsyncMergeZones:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.merge_zones(SERIAL, MAP_ID, {})

        url = mock_put.call_args.args[0]
        assert f"/v2/app/{SERIAL}/zones-definitions/{MAP_ID}/merge-zones" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.merge_zones(SERIAL, MAP_ID, {})
        await client.close()


class TestAsyncGetLiveMapCleaning:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_live_map_cleaning(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_live_map_cleaning(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/live-maps/cleaning" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_live_map_cleaning(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_live_map_cleaning(SERIAL)
        await client.close()


class TestAsyncGetLiveMapMapping:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_dict(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_live_map_mapping(SERIAL)

        assert isinstance(result, dict)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = LIVE_MAP_RESPONSE
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_live_map_mapping(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/live-maps/mapping" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_live_map_mapping(SERIAL)
        await client.close()


class TestAsyncSetScheduledEvents:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_sends_correct_body(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_scheduled_events(
            SERIAL, enabled=True, events=SCHEDULE_EVENTS_PAYLOAD
        )

        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["json"]["enabled"] is True
        assert call_kwargs["json"]["events"] == SCHEDULE_EVENTS_PAYLOAD
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_product_type_sent_as_query_param(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_scheduled_events(
            SERIAL, enabled=True, events=[], product_type="438K"
        )

        assert mock_put.call_args.kwargs["params"] == {"productType": "438K"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_scheduled_events(SERIAL, enabled=False, events=[])

        url = mock_put.call_args.args[0]
        assert f"/v1/unifiedscheduler/{SERIAL}/events" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.set_scheduled_events(SERIAL, enabled=True, events=[])
        await client.close()


class TestAsyncGetScheduleBinary:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_bytes(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"\xde\xad\xbe\xef"
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        result = await client.get_schedule_binary(SERIAL)

        assert isinstance(result, bytes)
        assert result == b"\xde\xad\xbe\xef"
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_correct_url(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b""
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_schedule_binary(SERIAL)

        url = mock_get.call_args.args[0]
        assert f"/v1/unifiedscheduler/{SERIAL}/app/schedule.bin" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_schedule_binary(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("down")
        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_schedule_binary(SERIAL)
        await client.close()
