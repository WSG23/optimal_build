from __future__ import annotations

from pathlib import Path

from backend.scripts import bootstrap_sg_capture_data as bootstrap


def test_bootstrap_parser_defaults_to_full_sg_capture_sources() -> None:
    parser = bootstrap._build_arg_parser()
    args = parser.parse_args([])

    assert args.skip_zoning is False
    assert args.skip_parcels is False
    assert args.download is False
    assert args.zoning_input == Path("data/sg/zoning/master_plan_2019_land_use.geojson")
    assert args.parcel_input == Path("data/sg/parcels/land_lot_boundary.geojson")
    assert args.parcel_source_epsg == 4326
    assert args.batch_size == 1000


def test_bootstrap_dotenv_loader_preserves_and_overrides_values(
    tmp_path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SECRET_KEY=from-file\n"
        "DATABASE_URL='sqlite:///capture.db'\n"
        "# ignored\n"
        "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("SECRET_KEY", "already-set")
    bootstrap._load_dotenv(env_file)

    assert bootstrap.os.environ["SECRET_KEY"] == "already-set"
    assert bootstrap.os.environ["DATABASE_URL"] == "sqlite:///capture.db"

    bootstrap._load_dotenv(env_file, override=True)

    assert bootstrap.os.environ["SECRET_KEY"] == "from-file"
