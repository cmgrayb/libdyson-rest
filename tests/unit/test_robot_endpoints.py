"""Unit tests for Vis Nav robot vacuum client endpoints (sync and async)."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError
from libdyson_rest.models import (
    CleaningStrategy,
    CleanRecord,
    PersistentMap,
    PersistentMapMeta,
    RecommendedCleanMap,
)

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

SERIAL = "AB1-CD-EF234567"
MAP_ID = "pm-001"
ZONE_ID = "zone-A"

CLEAN_MAP_ITEM = {
    "cleanId": "cr-001",
    "sequenceNumber": 1,
    "cleanTimeline": [
        {"time": "2024-01-01T09:00:00Z", "eventName": "START"},
        {"time": "2024-01-01T09:30:00Z", "eventName": "STOP"},
    ],
    "cleanedFootprint": {"area": 10.0},
    "cleaningProgramme": {
        "persistentMapId": MAP_ID,
        "orderedZones": [],
        "unorderedZones": [],
    },
    "persistentMap": {"id": MAP_ID},
    "dustMap": {"width": 50, "height": 40, "resolution": 20, "dustData": []},
}

# v2 schema item — matches the real RB05-AA response shape
CLEAN_MAP_ITEM_V2 = {
    "persistentMapId": MAP_ID,
    "cleanId": "fce99365-3756-5655-5356-444130343735",
    "isSpotClean": False,
    "orientation": 0,
    "startTime": 1780779744,
    "endTime": 1780784253,
    "cleanDuration": 76,
    "areaCleaned": 37.76,
    "downloadUrl": "https://example.s3.eu-west-1.amazonaws.com/map.bin?X-Amz-Expires=900",
    "zones": [
        {
            "id": ZONE_ID,
            "name": "Living room",
            "type": "livingRoom",
            "isSelected": True,
            "settings": {
                "cleaningStrategy": "auto",
                "cleanType": "vacuum",
                "waterLevel": "low",
                "mopPasses": 1,
                "dryPasses": 1,
            },
            "nameLocation": {"x": 1.825, "y": -1.725},
        }
    ],
    "spotZones": [],
    "dockLocation": None,
    "startBattery": 100.0,
    "endBattery": 56.0,
    "faults": [{"type": "2108", "x": -0.449, "y": 0.003}],
    "firmwareVersion": None,
}

MAP_META_ITEM = {
    "id": MAP_ID,
    "name": "Ground Floor",
    "zonesDefinitionLastUpdatedDate": "2024-06-01T00:00:00Z",
    "zones": [
        {"id": ZONE_ID, "name": "Kitchen", "area": 8.0},
        {"id": "zone-B", "name": "Living Room", "area": 20.0},
    ],
}

PERSISTENT_MAP_ITEM = {
    "id": MAP_ID,
    "name": "Ground Floor",
    "offset": {"x": 500.0, "y": -200.0},
    "presentationMap": {"data": "base64=="},
    "zonesDefinition": {"persistentMapDisplayOrientation": 90},
    "zones": [{"id": ZONE_ID, "name": "Kitchen"}],
}

RECOMMENDED_CLEANS_ITEM = {
    "persistentMapId": MAP_ID,
    "zonePredictions": [
        {
            "zoneId": ZONE_ID,
            "zoneDustMilligrams": [{"name": "total", "weight": 3.0}],
        }
    ],
}


# ===========================================================================
# Synchronous client tests
# ===========================================================================


class TestSyncGetCleanMaps:
    @patch("httpx.Client.get")
    def test_success_returns_clean_records(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [CLEAN_MAP_ITEM]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        records = client.get_clean_maps(SERIAL, api_version=2)

        assert len(records) == 1
        assert isinstance(records[0], CleanRecord)
        assert records[0].clean_id == "cr-001"
        mock_get.assert_called_once()

    @patch("httpx.Client.get")
    def test_dust_map_param_included_by_default(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_maps(SERIAL, api_version=2)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {"dustMap": "total"}

    @patch("httpx.Client.get")
    def test_dust_map_param_omitted_when_false(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_maps(SERIAL, api_version=2, include_dust_map=False)

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("params") == {}

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_clean_maps(SERIAL, api_version=2)

    @patch("httpx.Client.get")
    def test_raises_auth_error_on_401(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.side_effect = httpx.HTTPStatusError(
            "error", request=Mock(), response=mock_response
        )

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.get_clean_maps(SERIAL, api_version=2)

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("timeout")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_clean_maps(SERIAL, api_version=2)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_list_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": "unexpected"}
        mock_response.text = '{"error": "unexpected"}'
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            client.get_clean_maps(SERIAL, api_version=2)
        assert exc_info.value.raw == '{"error": "unexpected"}'

    @patch("httpx.Client.get")
    def test_v2_wrapped_response_parsed_correctly(self, mock_get: Mock) -> None:
        """v2 endpoint wraps the list in a ``{"data": [...]}`` envelope."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [CLEAN_MAP_ITEM_V2]}
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        records = client.get_clean_maps(SERIAL, api_version=2)

        assert len(records) == 1
        record = records[0]
        assert isinstance(record, CleanRecord)
        assert record.clean_id == "fce99365-3756-5655-5356-444130343735"
        assert record.persistent_map_id == MAP_ID
        assert record.start_time_epoch == 1780779744
        assert record.end_time_epoch == 1780784253
        assert record.clean_duration == 76
        assert record.area_cleaned == pytest.approx(37.76)
        assert record.is_spot_clean is False
        assert record.start_battery == pytest.approx(100.0)
        assert record.end_battery == pytest.approx(56.0)
        assert len(record.zones) == 1
        assert record.zones[0].id == ZONE_ID
        assert record.zones[0].is_selected is True
        assert record.zones[0].settings is not None
        assert record.zones[0].settings.cleaning_strategy == "auto"
        assert len(record.faults) == 1
        assert record.faults[0].type == "2108"
        assert record.faults[0].x == pytest.approx(-0.449)

    @patch("httpx.Client.get")
    def test_v2_data_envelope_with_non_list_value_raises(self, mock_get: Mock) -> None:
        """``{"data": <non-list>}`` should still raise DysonAPIError."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "not-a-list"}
        mock_response.text = '{"data": "not-a-list"}'
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list"):
            client.get_clean_maps(SERIAL, api_version=2)

    @patch("httpx.Client.get")
    def test_v2_url_used(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_maps(SERIAL, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/{SERIAL}/clean-maps" in url

    @patch("httpx.Client.get")
    def test_v1_url_used_for_vis_nav(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_clean_maps(SERIAL, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/{SERIAL}/clean-maps" in url


class TestSyncGetPersistentMapMetadata:
    @patch("httpx.Client.get")
    def test_success_returns_map_meta_list(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [MAP_META_ITEM]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        metas = client.get_persistent_map_metadata(SERIAL, api_version=2)

        assert len(metas) == 1
        assert isinstance(metas[0], PersistentMapMeta)
        assert metas[0].id == MAP_ID
        assert len(metas[0].zones) == 2

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_persistent_map_metadata(SERIAL, api_version=2)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_list_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": MAP_ID}
        mock_response.text = f'{{"id": "{MAP_ID}"}}'
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            client.get_persistent_map_metadata(SERIAL, api_version=2)
        assert exc_info.value.raw == f'{{"id": "{MAP_ID}"}}'

    @patch("httpx.Client.get")
    def test_correct_url_used(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_persistent_map_metadata(SERIAL, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-map-metadata" in url

    @patch("httpx.Client.get")
    def test_v1_url_used_for_vis_nav(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_persistent_map_metadata(SERIAL, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/persistent-map-metadata" in url

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("timeout")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_persistent_map_metadata(SERIAL, api_version=2)


class TestSyncGetPersistentMap:
    @patch("httpx.Client.get")
    def test_success_returns_persistent_map(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        pm = client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

        assert isinstance(pm, PersistentMap)
        assert pm.id == MAP_ID
        assert pm.offset_x == pytest.approx(500.0)
        assert pm.display_orientation == 90
        assert pm.presentation_map_data == "base64=="

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_dict_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [PERSISTENT_MAP_ITEM]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

    @patch("httpx.Client.get")
    def test_correct_url_includes_map_id(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url

    @patch("httpx.Client.get")
    def test_v1_url_includes_map_id(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.get_persistent_map(SERIAL, MAP_ID, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/persistent-maps/{MAP_ID}" in url

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("timeout")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_persistent_map(SERIAL, MAP_ID, api_version=2)


class TestSyncGetRecommendedCleans:
    @patch("httpx.Client.get")
    def test_success_returns_recommendations(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [RECOMMENDED_CLEANS_ITEM]
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        recs = client.get_recommended_cleans(SERIAL)

        assert len(recs) == 1
        assert isinstance(recs[0], RecommendedCleanMap)
        assert recs[0].persistent_map_id == MAP_ID
        assert len(recs[0].zone_predictions) == 1

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.get_recommended_cleans(SERIAL)

    @patch("httpx.Client.get")
    def test_raises_api_error_on_non_list_response(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_response.text = "{}"
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            client.get_recommended_cleans(SERIAL)
        assert exc_info.value.raw == "{}"

    @patch("httpx.Client.get")
    def test_raises_connection_error_on_network_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = httpx.NetworkError("timeout")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.get_recommended_cleans(SERIAL)


class TestSyncSetZoneBehaviour:
    @patch("httpx.Client.put")
    def test_success_with_enum_strategy(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.BOOST)

        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["json"] == {"cleaningStrategy": "boost"}

    @patch("httpx.Client.put")
    def test_success_with_string_strategy(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, "quiet")

        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["json"] == {"cleaningStrategy": "quiet"}

    @patch("httpx.Client.put")
    def test_correct_url_format(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = DysonClient(auth_token="tok")
        client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO)

        url = mock_put.call_args.args[0]
        # Must NOT contain "persistent-maps/" — this is a common mistake
        assert "persistent-maps" not in url
        assert f"/v1/app/{SERIAL}/{MAP_ID}/zones/{ZONE_ID}/zone-behaviours" in url

    def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = DysonClient()
        with pytest.raises(DysonAuthError):
            client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO)

    @patch("httpx.Client.put")
    def test_raises_auth_error_on_401(self, mock_put: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_put.side_effect = httpx.HTTPStatusError(
            "error", request=Mock(), response=mock_response
        )

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO)

    @patch("httpx.Client.put")
    def test_raises_connection_error_on_network_failure(self, mock_put: Mock) -> None:
        mock_put.side_effect = httpx.NetworkError("down")

        client = DysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO)


# ===========================================================================
# Asynchronous client tests
# ===========================================================================


class TestAsyncGetCleanMaps:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_clean_records(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [CLEAN_MAP_ITEM]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        records = await client.get_clean_maps(SERIAL, api_version=2)

        assert len(records) == 1
        assert isinstance(records[0], CleanRecord)
        assert records[0].clean_id == "cr-001"
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_clean_maps(SERIAL, api_version=2)
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
            await client.get_clean_maps(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_get: AsyncMock
    ) -> None:
        mock_get.side_effect = httpx.RequestError("timeout")

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.get_clean_maps(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_list_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": "oops"}
        mock_response.text = '{"error": "oops"}'
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            await client.get_clean_maps(SERIAL, api_version=2)
        assert exc_info.value.raw == '{"error": "oops"}'
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v2_wrapped_response_parsed_correctly(
        self, mock_get: AsyncMock
    ) -> None:
        """v2 endpoint wraps the list in a ``{"data": [...]}`` envelope."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [CLEAN_MAP_ITEM_V2]}
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        records = await client.get_clean_maps(SERIAL, api_version=2)

        assert len(records) == 1
        record = records[0]
        assert isinstance(record, CleanRecord)
        assert record.clean_id == "fce99365-3756-5655-5356-444130343735"
        assert record.start_time_epoch == 1780779744
        assert record.end_time_epoch == 1780784253
        assert record.area_cleaned == pytest.approx(37.76)
        assert len(record.zones) == 1
        assert len(record.faults) == 1
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v2_data_envelope_with_non_list_value_raises(
        self, mock_get: AsyncMock
    ) -> None:
        """``{"data": <non-list>}`` should still raise DysonAPIError."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "not-a-list"}
        mock_response.text = '{"data": "not-a-list"}'
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list"):
            await client.get_clean_maps(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v2_url_used(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_clean_maps(SERIAL, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/{SERIAL}/clean-maps" in url
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v1_url_used_for_vis_nav(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_clean_maps(SERIAL, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/{SERIAL}/clean-maps" in url
        await client.close()


class TestAsyncGetPersistentMapMetadata:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_map_meta_list(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [MAP_META_ITEM]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        metas = await client.get_persistent_map_metadata(SERIAL, api_version=2)

        assert len(metas) == 1
        assert isinstance(metas[0], PersistentMapMeta)
        assert metas[0].id == MAP_ID
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_persistent_map_metadata(SERIAL, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_list_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": MAP_ID}
        mock_response.text = f'{{"id": "{MAP_ID}"}}'
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            await client.get_persistent_map_metadata(SERIAL, api_version=2)
        assert exc_info.value.raw == f'{{"id": "{MAP_ID}"}}'
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v2_url_used(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_persistent_map_metadata(SERIAL, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-map-metadata" in url
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v1_url_used_for_vis_nav(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_persistent_map_metadata(SERIAL, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/persistent-map-metadata" in url
        await client.close()


class TestAsyncGetPersistentMap:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_persistent_map(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        pm = await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

        assert isinstance(pm, PersistentMap)
        assert pm.id == MAP_ID
        assert pm.offset_x == pytest.approx(500.0)
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_dict_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [PERSISTENT_MAP_ITEM]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected object"):
            await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v2_url_includes_map_id(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_persistent_map(SERIAL, MAP_ID, api_version=2)

        url = mock_get.call_args.args[0]
        assert f"/v2/app/{SERIAL}/persistent-maps/{MAP_ID}" in url
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_v1_url_includes_map_id(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = PERSISTENT_MAP_ITEM
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.get_persistent_map(SERIAL, MAP_ID, api_version=1)

        url = mock_get.call_args.args[0]
        assert f"/v1/app/{SERIAL}/persistent-maps/{MAP_ID}" in url
        await client.close()


class TestAsyncGetRecommendedCleans:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_success_returns_recommendations(self, mock_get: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [RECOMMENDED_CLEANS_ITEM]
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        recs = await client.get_recommended_cleans(SERIAL)

        assert len(recs) == 1
        assert isinstance(recs[0], RecommendedCleanMap)
        assert recs[0].persistent_map_id == MAP_ID
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.get_recommended_cleans(SERIAL)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_raises_api_error_on_non_list_response(
        self, mock_get: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_response.text = "{}"
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAPIError, match="Expected list") as exc_info:
            await client.get_recommended_cleans(SERIAL)
        assert exc_info.value.raw == "{}"
        await client.close()


class TestAsyncSetZoneBehaviour:
    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_success_with_enum_strategy(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.QUIET)

        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args.kwargs
        assert call_kwargs["json"] == {"cleaningStrategy": "quiet"}
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_correct_url_no_persistent_maps_segment(
        self, mock_put: AsyncMock
    ) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        client = AsyncDysonClient(auth_token="tok")
        await client.set_zone_behaviour(SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO)

        url = mock_put.call_args.args[0]
        assert "persistent-maps" not in url
        assert f"/v1/app/{SERIAL}/{MAP_ID}/zones/{ZONE_ID}/zone-behaviours" in url
        await client.close()

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_authenticated(self) -> None:
        client = AsyncDysonClient()
        with pytest.raises(DysonAuthError):
            await client.set_zone_behaviour(
                SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_raises_auth_error_on_401(self, mock_put: AsyncMock) -> None:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_put.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonAuthError, match="expired"):
            await client.set_zone_behaviour(
                SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO
            )
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.put")
    @pytest.mark.asyncio
    async def test_raises_connection_error_on_network_failure(
        self, mock_put: AsyncMock
    ) -> None:
        mock_put.side_effect = httpx.RequestError("timeout")

        client = AsyncDysonClient(auth_token="tok")
        with pytest.raises(DysonConnectionError):
            await client.set_zone_behaviour(
                SERIAL, MAP_ID, ZONE_ID, CleaningStrategy.AUTO
            )
        await client.close()
