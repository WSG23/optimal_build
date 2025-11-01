"""Tests for base model utilities."""

import uuid as uuid_module
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock

from sqlalchemy.dialects import postgresql, sqlite

from backend._compat.datetime import UTC
from app.models.base import UUID, BaseModel, MetadataProxy


class TestUUIDTypeDecorator:
    """Tests for the UUID type decorator."""

    def test_uuid_uses_pg_uuid_for_postgresql(self):
        """Test that PostgreSQL dialect uses native UUID type."""
        uuid_type = UUID()
        dialect = postgresql.dialect()

        impl = uuid_type.load_dialect_impl(dialect)

        # PostgreSQL uses PGUuid class (renamed from UUID)
        assert impl.__class__.__name__ in ("UUID", "PGUuid")

    def test_uuid_uses_char36_for_sqlite(self):
        """Test that SQLite dialect uses CHAR(36)."""
        uuid_type = UUID()
        dialect = sqlite.dialect()

        impl = uuid_type.load_dialect_impl(dialect)

        assert impl.length == 36

    def test_process_bind_param_with_none(self):
        """Test that None values pass through unchanged."""
        uuid_type = UUID()
        dialect = sqlite.dialect()

        result = uuid_type.process_bind_param(None, dialect)

        assert result is None

    def test_process_bind_param_with_uuid_object_sqlite(self):
        """Test binding UUID object to SQLite (converts to string)."""
        uuid_type = UUID()
        dialect = sqlite.dialect()
        test_uuid = uuid_module.uuid4()

        result = uuid_type.process_bind_param(test_uuid, dialect)

        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_process_bind_param_with_uuid_object_postgresql(self):
        """Test binding UUID object to PostgreSQL (keeps as UUID)."""
        uuid_type = UUID()
        dialect = postgresql.dialect()
        test_uuid = uuid_module.uuid4()

        result = uuid_type.process_bind_param(test_uuid, dialect)

        assert isinstance(result, uuid_module.UUID)
        assert result == test_uuid

    def test_process_bind_param_with_string(self):
        """Test binding UUID string."""
        uuid_type = UUID()
        dialect = sqlite.dialect()
        test_uuid = uuid_module.uuid4()
        uuid_str = str(test_uuid)

        result = uuid_type.process_bind_param(uuid_str, dialect)

        assert result == uuid_str

    def test_process_bind_param_with_int(self):
        """Test binding UUID from integer."""
        uuid_type = UUID()
        dialect = sqlite.dialect()
        # Create a UUID from an integer
        test_int = 123456789012345678901234567890123456
        expected_uuid = uuid_module.UUID(int=test_int)

        result = uuid_type.process_bind_param(test_int, dialect)

        assert result == str(expected_uuid)

    def test_process_result_value_with_none(self):
        """Test that None results pass through unchanged."""
        uuid_type = UUID()
        dialect = sqlite.dialect()

        result = uuid_type.process_result_value(None, dialect)

        assert result is None

    def test_process_result_value_postgresql_returns_uuid(self):
        """Test PostgreSQL returns UUID objects as-is."""
        uuid_type = UUID()
        dialect = postgresql.dialect()
        test_uuid = uuid_module.uuid4()

        result = uuid_type.process_result_value(test_uuid, dialect)

        assert result == test_uuid
        assert isinstance(result, uuid_module.UUID)

    def test_process_result_value_sqlite_converts_string_to_uuid(self):
        """Test SQLite converts string to UUID object."""
        uuid_type = UUID()
        dialect = sqlite.dialect()
        test_uuid = uuid_module.uuid4()
        uuid_str = str(test_uuid)

        result = uuid_type.process_result_value(uuid_str, dialect)

        assert isinstance(result, uuid_module.UUID)
        assert result == test_uuid

    def test_process_result_value_sqlite_with_uuid_object(self):
        """Test SQLite with UUID object (returns as-is)."""
        uuid_type = UUID()
        dialect = sqlite.dialect()
        test_uuid = uuid_module.uuid4()

        result = uuid_type.process_result_value(test_uuid, dialect)

        assert result == test_uuid


class TestBaseModel:
    """Tests for the BaseModel class."""

    def test_basemodel_is_abstract(self):
        """Test that BaseModel has __abstract__ = True."""
        assert BaseModel.__abstract__ is True

    def test_as_dict_normalizes_decimal(self):
        """Test as_dict normalizes Decimal to float."""
        # Create a mock instance without requiring database
        instance = Mock(spec=BaseModel)
        instance.id = 1
        instance.amount = Decimal("123.45")
        instance.status = "active"
        instance._private = "hidden"
        instance.__table__ = None  # Trigger fallback path

        # Call the actual method
        result = BaseModel.as_dict(instance)

        assert result["id"] == 1
        assert result["amount"] == 123.45
        assert isinstance(result["amount"], float)
        assert result["status"] == "active"
        assert "_private" not in result

    def test_as_dict_normalizes_datetime(self):
        """Test as_dict converts datetime to ISO format."""
        instance = Mock(spec=BaseModel)
        instance.id = 1
        test_datetime = datetime(2023, 6, 15, 10, 30, 45, tzinfo=UTC)
        instance.created_at = test_datetime
        instance.__table__ = None

        result = BaseModel.as_dict(instance)

        assert result["created_at"] == test_datetime.isoformat()

    def test_as_dict_normalizes_date(self):
        """Test as_dict converts date to ISO format."""
        instance = Mock(spec=BaseModel)
        instance.id = 1
        test_date = date(2023, 6, 15)
        instance.birth_date = test_date
        instance.__table__ = None

        result = BaseModel.as_dict(instance)

        assert result["birth_date"] == "2023-06-15"

    def test_as_dict_skips_private_attributes(self):
        """Test as_dict skips attributes starting with underscore."""
        instance = Mock(spec=BaseModel)
        instance.id = 1
        instance.name = "Test"
        instance._private_field = "should not appear"
        instance.__table__ = None

        result = BaseModel.as_dict(instance)

        assert "_private_field" not in result
        assert "id" in result
        assert "name" in result

    def test_as_dict_handles_none_values(self):
        """Test as_dict handles None values correctly."""
        instance = Mock(spec=BaseModel)
        instance.id = 1
        instance.optional_field = None
        instance.__table__ = None

        result = BaseModel.as_dict(instance)

        assert result["id"] == 1
        assert result["optional_field"] is None


class TestMetadataProxy:
    """Tests for the MetadataProxy descriptor."""

    def test_metadata_proxy_returns_empty_dict_when_none(self):
        """Test that MetadataProxy returns empty dict when metadata_json is None."""
        proxy = MetadataProxy()
        instance = Mock()
        instance.metadata_json = None

        result = proxy.__get__(instance, type(instance))

        assert result == {}
        assert instance.metadata_json == {}

    def test_metadata_proxy_returns_existing_metadata(self):
        """Test that MetadataProxy returns existing metadata_json."""
        proxy = MetadataProxy()
        instance = Mock()
        test_metadata = {"key": "value", "count": 42}
        instance.metadata_json = test_metadata

        result = proxy.__get__(instance, type(instance))

        assert result == test_metadata
        assert result is instance.metadata_json

    def test_metadata_proxy_set_updates_metadata_json(self):
        """Test that setting metadata updates metadata_json."""
        proxy = MetadataProxy()
        instance = Mock()
        new_metadata = {"foo": "bar"}

        proxy.__set__(instance, new_metadata)

        assert instance.metadata_json == new_metadata

    def test_metadata_proxy_set_none_becomes_empty_dict(self):
        """Test that setting metadata to None creates empty dict."""
        proxy = MetadataProxy()
        instance = Mock()
        instance.metadata_json = {"initial": "value"}

        proxy.__set__(instance, None)

        assert instance.metadata_json == {}

    def test_metadata_proxy_get_on_class_returns_base_metadata(self):
        """Test that accessing MetadataProxy on class returns BaseModel.metadata."""
        proxy = MetadataProxy()

        # Accessing on None (class-level access) should return BaseModel.metadata
        result = proxy.__get__(None, BaseModel)

        assert result is BaseModel.metadata
