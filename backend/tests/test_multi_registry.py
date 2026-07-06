"""
Tests for multi-registry support (Task 3.20 / 4.01).

Validates the following additions:
  1. RegistryNotFoundError  — backend/core/exceptions.py
  2. ClassificationRegistry.load()  — backend/core/classification/registry.py
  3. list_available_registries()  — backend/core/classification/registry.py
  4. RegistriesResponse schema  — backend/api/schemas.py
  5. TransformRequestSchema.registry_id field
  6. ClassifyRequest.registry_id field
  7. GET /registries endpoint  — backend/api/main.py
  8. GET /registry?registry_id=default backward compatibility

Uses monkeypatch for REGISTRY_DIR / REGISTRY_PATH env vars.
Uses tmp_path for temporary directory/file fixtures.
All T1 safety tests are marked with @pytest.mark.safety and must never be
skipped or marked xfail.
"""

import json
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.api.main import app
from backend.api.schemas import (
    ClassifyRequest,
    RegistriesResponse,
    TransformRequestSchema,
)
from backend.core.classification.registry import (
    ClassificationRegistry,
    list_available_registries,
)
from backend.core.exceptions import NexBridgeError, RegistryNotFoundError


# ── Module-level TestClient ────────────────────────────────────────────────────

client = TestClient(app)


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_registry_json(
    *,
    version: str = "1.0",
    domain: str = "test",
    default_tier: int = 4,
    fields: dict | None = None,
) -> dict:
    """Return a minimal valid registry JSON dict."""
    return {
        "version": version,
        "domain": domain,
        "default_tier": default_tier,
        "fields": fields or {},
    }


def _write_registry(path, content: dict) -> None:
    """Write *content* as JSON to *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(content, fh)


# =============================================================================
# TestRegistryNotFoundError
# =============================================================================


class TestRegistryNotFoundError:
    """Tests for RegistryNotFoundError in backend/core/exceptions.py."""

    # ── Inheritance ───────────────────────────────────────────────────────────

    def test_registry_not_found_error_is_nexbridge_error(self):
        """RegistryNotFoundError must be a subclass of NexBridgeError."""
        err = RegistryNotFoundError(registry_id="hr", available=["default"])
        assert isinstance(err, NexBridgeError)

    def test_registry_not_found_error_is_exception(self):
        """RegistryNotFoundError must be raise-able as a standard exception."""
        with pytest.raises(RegistryNotFoundError):
            raise RegistryNotFoundError(registry_id="hr", available=["default"])

    # ── Stored attributes ─────────────────────────────────────────────────────

    def test_registry_not_found_stores_registry_id(self):
        """registry_id attribute must match the constructor argument."""
        err = RegistryNotFoundError(registry_id="aviation", available=["default"])
        assert err.registry_id == "aviation"

    def test_registry_not_found_stores_available_list(self):
        """available attribute must match the constructor argument."""
        available = ["default", "hr"]
        err = RegistryNotFoundError(registry_id="aviation", available=available)
        assert err.available == available

    def test_registry_not_found_stores_empty_available_list(self):
        """available may be an empty list — must be stored as-is."""
        err = RegistryNotFoundError(registry_id="missing", available=[])
        assert err.available == []

    # ── __str__ output ────────────────────────────────────────────────────────

    def test_registry_not_found_str_contains_registry_id(self):
        """__str__ must include the requested registry_id."""
        err = RegistryNotFoundError(registry_id="aviation", available=["default"])
        assert "aviation" in str(err)

    def test_registry_not_found_str_contains_available_item(self):
        """__str__ must include each available registry name."""
        err = RegistryNotFoundError(registry_id="aviation", available=["default", "hr"])
        output = str(err)
        assert "default" in output
        assert "hr" in output

    def test_registry_not_found_str_empty_available_shows_none_marker(self):
        """When available=[], __str__ must show a '(none)' marker or similar."""
        err = RegistryNotFoundError(registry_id="missing", available=[])
        assert "(none)" in str(err)

    # ── Default message ───────────────────────────────────────────────────────

    def test_registry_not_found_default_message_includes_registry_id(self):
        """The auto-generated message (args[0]) must include the registry_id."""
        err = RegistryNotFoundError(registry_id="hr", available=["default"])
        assert "hr" in err.message

    def test_registry_not_found_custom_message_is_stored(self):
        """When a custom message is supplied it must be stored in .message."""
        err = RegistryNotFoundError(
            registry_id="hr",
            available=["default"],
            message="Custom override message",
        )
        assert err.message == "Custom override message"


# =============================================================================
# TestClassificationRegistryLoad
# =============================================================================


class TestClassificationRegistryLoad:
    """Tests for ClassificationRegistry.load() classmethod."""

    # ── No REGISTRY_DIR set ───────────────────────────────────────────────────

    def test_load_without_registry_dir_returns_registry(self, monkeypatch):
        """load() with no REGISTRY_DIR must return a working ClassificationRegistry."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        monkeypatch.delenv("REGISTRY_PATH", raising=False)

        registry = ClassificationRegistry.load()

        assert isinstance(registry, ClassificationRegistry)

    def test_load_without_registry_dir_registry_is_functional(self, monkeypatch):
        """Registry returned when REGISTRY_DIR is absent must classify fields."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        monkeypatch.delenv("REGISTRY_PATH", raising=False)

        registry = ClassificationRegistry.load()
        # The bundled default registry contains weight_limit as T1
        from backend.core.models import Tier
        result = registry.classify("weight_limit")
        assert result.tier == Tier.T1

    def test_load_none_registry_id_without_registry_dir_returns_registry(
        self, monkeypatch
    ):
        """load(registry_id=None) must behave identically to load()."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        monkeypatch.delenv("REGISTRY_PATH", raising=False)

        registry = ClassificationRegistry.load(registry_id=None)

        assert isinstance(registry, ClassificationRegistry)

    def test_load_without_registry_dir_same_as_direct_instantiation(
        self, monkeypatch
    ):
        """load() with no REGISTRY_DIR must return same fields as ClassificationRegistry()."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        monkeypatch.delenv("REGISTRY_PATH", raising=False)

        via_load = ClassificationRegistry.load()
        direct = ClassificationRegistry()

        assert via_load.list_all_fields() == direct.list_all_fields()

    # ── REGISTRY_DIR set — file exists ────────────────────────────────────────

    def test_load_with_registry_dir_loads_specified_file(
        self, tmp_path, monkeypatch
    ):
        """load('hr') with REGISTRY_DIR containing hr.json must load that file."""
        registry_data = _make_registry_json(
            version="2.0",
            domain="hr",
            fields={
                "salary_band": {
                    "tier": 2,
                    "label": "Operationally Sensitive",
                    "threshold": 0.95,
                    "description": "HR salary band",
                }
            },
        )
        _write_registry(tmp_path / "hr.json", registry_data)
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        registry = ClassificationRegistry.load("hr")

        assert registry.get_domain() == "hr"
        assert registry.get_version() == "2.0"

    def test_load_with_registry_dir_file_classifies_custom_field(
        self, tmp_path, monkeypatch
    ):
        """Fields defined in a custom registry file must be classified correctly."""
        from backend.core.models import Tier

        registry_data = _make_registry_json(
            domain="aviation",
            fields={
                "altitude_limit": {
                    "tier": 1,
                    "label": "Safety Critical",
                    "threshold": 1.0,
                    "description": "Aviation altitude constraint",
                }
            },
        )
        _write_registry(tmp_path / "aviation.json", registry_data)
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        registry = ClassificationRegistry.load("aviation")
        result = registry.classify("altitude_limit")

        assert result.tier == Tier.T1
        assert result.confidence_threshold == 1.0

    def test_load_default_id_with_registry_dir_loads_default_file(
        self, tmp_path, monkeypatch
    ):
        """load('default') must load default.json when REGISTRY_DIR is set."""
        registry_data = _make_registry_json(version="3.0", domain="custom-default")
        _write_registry(tmp_path / "default.json", registry_data)
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        registry = ClassificationRegistry.load("default")

        assert registry.get_domain() == "custom-default"
        assert registry.get_version() == "3.0"

    def test_load_none_id_with_registry_dir_loads_default_file(
        self, tmp_path, monkeypatch
    ):
        """load(registry_id=None) must treat None as 'default' and load default.json."""
        registry_data = _make_registry_json(version="3.0", domain="custom-default")
        _write_registry(tmp_path / "default.json", registry_data)
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        registry = ClassificationRegistry.load(None)

        assert registry.get_domain() == "custom-default"

    # ── REGISTRY_DIR set — file missing ───────────────────────────────────────

    def test_load_missing_registry_raises_registry_not_found_error(
        self, tmp_path, monkeypatch
    ):
        """
        load() when REGISTRY_DIR is set but {id}.json is absent must raise
        RegistryNotFoundError.
        """
        # tmp_path is an empty directory — no hr.json present
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        with pytest.raises(RegistryNotFoundError):
            ClassificationRegistry.load("hr")

    def test_load_missing_registry_error_has_correct_registry_id(
        self, tmp_path, monkeypatch
    ):
        """RegistryNotFoundError must carry the requested registry_id."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        with pytest.raises(RegistryNotFoundError) as exc_info:
            ClassificationRegistry.load("aviation")

        assert exc_info.value.registry_id == "aviation"

    def test_load_missing_registry_error_available_reflects_existing_files(
        self, tmp_path, monkeypatch
    ):
        """RegistryNotFoundError.available must list IDs that actually exist."""
        # Create default.json but not hr.json
        _write_registry(tmp_path / "default.json", _make_registry_json())
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        with pytest.raises(RegistryNotFoundError) as exc_info:
            ClassificationRegistry.load("hr")

        assert "default" in exc_info.value.available
        assert "hr" not in exc_info.value.available

    def test_load_missing_registry_error_available_empty_when_dir_empty(
        self, tmp_path, monkeypatch
    ):
        """When REGISTRY_DIR is empty, available must be ['default'] (function fallback)."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        with pytest.raises(RegistryNotFoundError) as exc_info:
            ClassificationRegistry.load("hr")

        # list_available_registries() returns ["default"] for empty dir
        assert exc_info.value.available == ["default"]

    def test_load_none_id_missing_default_json_raises_registry_not_found(
        self, tmp_path, monkeypatch
    ):
        """load(None) when default.json is absent must raise RegistryNotFoundError."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        with pytest.raises(RegistryNotFoundError) as exc_info:
            ClassificationRegistry.load(None)

        assert exc_info.value.registry_id == "default"


# =============================================================================
# TestListAvailableRegistries
# =============================================================================


class TestListAvailableRegistries:
    """Tests for list_available_registries() module-level function."""

    # ── No REGISTRY_DIR set ───────────────────────────────────────────────────

    def test_list_available_no_registry_dir_returns_default(self, monkeypatch):
        """list_available_registries() with no REGISTRY_DIR must return ['default']."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)

        result = list_available_registries()

        assert result == ["default"]

    def test_list_available_no_registry_dir_return_type_is_list(self, monkeypatch):
        """Return type must always be list[str]."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)

        result = list_available_registries()

        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    # ── REGISTRY_DIR pointing to populated directory ──────────────────────────

    def test_list_available_with_default_and_hr_json(self, tmp_path, monkeypatch):
        """Directory with default.json and hr.json must return ['default', 'hr'] sorted."""
        _write_registry(tmp_path / "default.json", _make_registry_json(domain="default"))
        _write_registry(tmp_path / "hr.json", _make_registry_json(domain="hr"))
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert sorted(result) == sorted(["default", "hr"])
        assert result == sorted(result), "Result must be returned in sorted order"

    def test_list_available_with_multiple_registries_sorted(
        self, tmp_path, monkeypatch
    ):
        """Multiple registry files must be returned in alphabetical order."""
        for name in ["zebra", "alpha", "default", "hr"]:
            _write_registry(tmp_path / f"{name}.json", _make_registry_json(domain=name))
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert result == sorted(result)
        assert set(result) == {"alpha", "default", "hr", "zebra"}

    def test_list_available_excludes_non_json_files(self, tmp_path, monkeypatch):
        """Non-JSON files in REGISTRY_DIR must not appear in the list."""
        _write_registry(tmp_path / "default.json", _make_registry_json())
        (tmp_path / "readme.txt").write_text("not a registry")
        (tmp_path / "notes.md").write_text("# notes")
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert result == ["default"]
        assert "readme" not in result
        assert "notes" not in result

    def test_list_available_strips_json_extension(self, tmp_path, monkeypatch):
        """IDs in the returned list must not include the .json extension."""
        _write_registry(tmp_path / "aviation.json", _make_registry_json())
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert "aviation" in result
        assert "aviation.json" not in result

    # ── REGISTRY_DIR pointing to empty directory ──────────────────────────────

    def test_list_available_empty_dir_returns_default(self, tmp_path, monkeypatch):
        """An empty REGISTRY_DIR must return ['default'] as the fallback."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert result == ["default"]

    # ── REGISTRY_DIR pointing to non-existent directory ───────────────────────

    def test_list_available_nonexistent_dir_returns_default(self, monkeypatch):
        """A REGISTRY_DIR path that does not exist must return ['default']."""
        monkeypatch.setenv("REGISTRY_DIR", "/tmp/nexbridge_nonexistent_dir_xyz_12345")

        result = list_available_registries()

        assert result == ["default"]

    def test_list_available_return_is_list_of_strings_for_all_cases(
        self, tmp_path, monkeypatch
    ):
        """Return type must be list[str] regardless of REGISTRY_DIR state."""
        _write_registry(tmp_path / "hr.json", _make_registry_json())
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        result = list_available_registries()

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)


# =============================================================================
# TestRegistriesResponseSchema
# =============================================================================


class TestRegistriesResponseSchema:
    """Tests for RegistriesResponse Pydantic schema in backend/api/schemas.py."""

    # ── Happy-path construction ───────────────────────────────────────────────

    def test_registries_response_constructs_with_list_and_count(self):
        """RegistriesResponse must construct with a list of strings and a count."""
        resp = RegistriesResponse(registries=["default", "hr"], count=2)
        assert resp.registries == ["default", "hr"]
        assert resp.count == 2

    def test_registries_response_empty_list_count_zero_accepted(self):
        """registries=[] and count=0 must be accepted (ge=0 boundary)."""
        resp = RegistriesResponse(registries=[], count=0)
        assert resp.registries == []
        assert resp.count == 0

    def test_registries_response_single_item_constructs(self):
        """A single-element list with count=1 must construct successfully."""
        resp = RegistriesResponse(registries=["default"], count=1)
        assert len(resp.registries) == 1
        assert resp.count == 1

    # ── Field types ───────────────────────────────────────────────────────────

    def test_registries_response_registries_is_list_of_str(self):
        """registries field must be list[str]."""
        resp = RegistriesResponse(registries=["default"], count=1)
        assert isinstance(resp.registries, list)
        for item in resp.registries:
            assert isinstance(item, str)

    def test_registries_response_count_is_int(self):
        """count field must be an int."""
        resp = RegistriesResponse(registries=["default"], count=1)
        assert isinstance(resp.count, int)

    # ── count ge=0 constraint ─────────────────────────────────────────────────

    def test_registries_response_count_negative_raises(self):
        """count=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError):
            RegistriesResponse(registries=[], count=-1)

    def test_registries_response_count_zero_is_boundary(self):
        """count=0 must be accepted as the lower boundary value."""
        resp = RegistriesResponse(registries=[], count=0)
        assert resp.count == 0

    # ── Missing required fields ───────────────────────────────────────────────

    def test_registries_response_missing_registries_raises(self):
        """Omitting 'registries' must raise ValidationError."""
        with pytest.raises(ValidationError):
            RegistriesResponse(count=1)  # type: ignore[call-arg]

    def test_registries_response_missing_count_raises(self):
        """Omitting 'count' must raise ValidationError."""
        with pytest.raises(ValidationError):
            RegistriesResponse(registries=["default"])  # type: ignore[call-arg]


# =============================================================================
# TestTransformRequestSchemaRegistryId
# =============================================================================


class TestTransformRequestSchemaRegistryId:
    """Tests for the registry_id field added to TransformRequestSchema."""

    def _base_request(self, **overrides) -> dict:
        """Return a minimal valid TransformRequestSchema kwargs dict."""
        defaults = dict(
            payload="<record><id>1</id></record>",
            source_format="xml",
            target_format="json",
            target_schema={"id": "string"},
        )
        defaults.update(overrides)
        return defaults

    # ── Default value ─────────────────────────────────────────────────────────

    def test_transform_request_registry_id_defaults_to_default(self):
        """registry_id must default to 'default' when omitted."""
        req = TransformRequestSchema(**self._base_request())
        assert req.registry_id == "default"

    # ── Explicit values ───────────────────────────────────────────────────────

    def test_transform_request_registry_id_accepts_default_string(self):
        """registry_id='default' must be accepted."""
        req = TransformRequestSchema(**self._base_request(registry_id="default"))
        assert req.registry_id == "default"

    def test_transform_request_registry_id_accepts_hr(self):
        """registry_id='hr' must be accepted."""
        req = TransformRequestSchema(**self._base_request(registry_id="hr"))
        assert req.registry_id == "hr"

    def test_transform_request_registry_id_accepts_any_string(self):
        """registry_id accepts any non-empty string value."""
        req = TransformRequestSchema(
            **self._base_request(registry_id="aviation-v2")
        )
        assert req.registry_id == "aviation-v2"

    def test_transform_request_registry_id_does_not_affect_other_validation(self):
        """Adding registry_id must not break existing field validators."""
        # invalid source_format must still be rejected
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                **self._base_request(source_format="csv", registry_id="hr")
            )
        assert "source_format" in str(exc_info.value)


# =============================================================================
# TestClassifyRequestRegistryId
# =============================================================================


class TestClassifyRequestRegistryId:
    """Tests for the registry_id field added to ClassifyRequest."""

    # ── Default value ─────────────────────────────────────────────────────────

    def test_classify_request_registry_id_defaults_to_default(self):
        """registry_id must default to 'default' when omitted."""
        req = ClassifyRequest(field_names=["employee_id"])
        assert req.registry_id == "default"

    # ── Explicit values ───────────────────────────────────────────────────────

    def test_classify_request_registry_id_accepts_hr(self):
        """registry_id='hr' must be accepted."""
        req = ClassifyRequest(field_names=["salary_band"], registry_id="hr")
        assert req.registry_id == "hr"

    def test_classify_request_registry_id_accepts_any_string(self):
        """registry_id accepts any string value."""
        req = ClassifyRequest(field_names=["field_a"], registry_id="custom-domain")
        assert req.registry_id == "custom-domain"

    def test_classify_request_registry_id_does_not_disable_empty_list_check(self):
        """field_names=[] validation must still fire when registry_id is set."""
        with pytest.raises(ValidationError) as exc_info:
            ClassifyRequest(field_names=[], registry_id="hr")
        assert "field_names" in str(exc_info.value)


# =============================================================================
# TestRegistriesEndpoint
# =============================================================================


class TestRegistriesEndpoint:
    """Tests for GET /registries endpoint in backend/api/main.py."""

    def test_registries_returns_200(self):
        """GET /registries must return HTTP 200."""
        response = client.get("/registries")
        assert response.status_code == 200

    def test_registries_response_has_registries_field(self):
        """Response body must contain a 'registries' key."""
        response = client.get("/registries")
        data = response.json()
        assert "registries" in data

    def test_registries_response_has_count_field(self):
        """Response body must contain a 'count' key."""
        response = client.get("/registries")
        data = response.json()
        assert "count" in data

    def test_registries_count_matches_len_of_registries(self):
        """'count' must equal len(registries) in the response."""
        response = client.get("/registries")
        data = response.json()
        assert data["count"] == len(data["registries"])

    def test_registries_list_is_list_of_strings(self):
        """'registries' must be a list of strings."""
        response = client.get("/registries")
        data = response.json()
        assert isinstance(data["registries"], list)
        for item in data["registries"]:
            assert isinstance(item, str)

    def test_registries_count_is_non_negative(self):
        """'count' must be >= 0."""
        response = client.get("/registries")
        data = response.json()
        assert data["count"] >= 0

    def test_registries_default_includes_default_entry(self, monkeypatch):
        """Without REGISTRY_DIR, 'registries' must contain 'default'."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        # Re-import to reflect env state — TestClient calls the live endpoint
        response = client.get("/registries")
        data = response.json()
        assert "default" in data["registries"]

    def test_registries_with_dir_reflects_json_files(
        self, tmp_path, monkeypatch
    ):
        """When REGISTRY_DIR contains JSON files, endpoint must list their IDs."""
        _write_registry(tmp_path / "default.json", _make_registry_json())
        _write_registry(tmp_path / "hr.json", _make_registry_json(domain="hr"))
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        response = client.get("/registries")
        data = response.json()

        assert set(data["registries"]) == {"default", "hr"}
        assert data["count"] == 2

    def test_registries_with_empty_dir_returns_default_fallback(
        self, tmp_path, monkeypatch
    ):
        """An empty REGISTRY_DIR must still return ['default'] and count=1."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        response = client.get("/registries")
        data = response.json()

        assert data["registries"] == ["default"]
        assert data["count"] == 1


# =============================================================================
# TestRegistryEndpointBackwardCompat
# =============================================================================


class TestRegistryEndpointBackwardCompat:
    """
    Backward compatibility tests for GET /registry?registry_id=default.

    Verifies that the existing /registry endpoint continues to work
    correctly with and without the registry_id query parameter after
    multi-registry support was added.
    """

    def test_registry_no_param_returns_200(self):
        """GET /registry (no params) must still return HTTP 200."""
        response = client.get("/registry")
        assert response.status_code == 200

    def test_registry_default_param_returns_200(self):
        """GET /registry?registry_id=default must return HTTP 200."""
        response = client.get("/registry", params={"registry_id": "default"})
        assert response.status_code == 200

    def test_registry_default_param_same_response_as_no_param(self):
        """
        GET /registry?registry_id=default must return the same body as
        GET /registry (no param), since 'default' is the default value.
        """
        no_param = client.get("/registry").json()
        with_param = client.get(
            "/registry", params={"registry_id": "default"}
        ).json()
        assert no_param == with_param

    def test_registry_default_response_has_version(self):
        """GET /registry?registry_id=default must include a 'version' field."""
        response = client.get("/registry", params={"registry_id": "default"})
        data = response.json()
        assert "version" in data
        assert data["version"] != ""

    def test_registry_default_response_has_domain(self):
        """GET /registry?registry_id=default must include a 'domain' field."""
        response = client.get("/registry", params={"registry_id": "default"})
        data = response.json()
        assert "domain" in data
        assert data["domain"] != ""

    def test_registry_default_response_field_count_matches_fields(self):
        """'field_count' must equal len(fields) in the /registry?registry_id=default response."""
        response = client.get("/registry", params={"registry_id": "default"})
        data = response.json()
        assert data["field_count"] == len(data["fields"])

    def test_registry_unknown_id_with_registry_dir_set_returns_404(
        self, tmp_path, monkeypatch
    ):
        """
        GET /registry?registry_id=nonexistent when REGISTRY_DIR is set but
        the file is absent must return HTTP 404.
        """
        _write_registry(tmp_path / "default.json", _make_registry_json())
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        response = client.get("/registry", params={"registry_id": "nonexistent"})
        assert response.status_code == 404

    def test_registry_404_detail_mentions_registry_id(
        self, tmp_path, monkeypatch
    ):
        """The 404 detail message must include the requested registry_id."""
        _write_registry(tmp_path / "default.json", _make_registry_json())
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        response = client.get("/registry", params={"registry_id": "nonexistent"})
        detail = response.json()["detail"]
        assert "nonexistent" in detail

    def test_registry_custom_id_with_file_present_returns_200(
        self, tmp_path, monkeypatch
    ):
        """
        GET /registry?registry_id=hr when hr.json exists in REGISTRY_DIR
        must return HTTP 200 with that registry's data.
        """
        hr_data = _make_registry_json(version="2.0", domain="hr")
        _write_registry(tmp_path / "hr.json", hr_data)
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))

        response = client.get("/registry", params={"registry_id": "hr"})
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "hr"
        assert data["version"] == "2.0"
