import tempfile

import pytest

pytest.importorskip("ezdxf")

import ezdxf  # type: ignore  # noqa: E402
from backend.jobs.parse_cad import _parse_dxf_payload, _prepare_dxf_quicklook

pytestmark = pytest.mark.no_db


def _dxf_payload_mm() -> bytes:
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_lwpolyline(
        [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
        format="xy",
        close=True,
    )
    msp.add_lwpolyline(
        [(500, 500), (3500, 500), (3500, 2800), (500, 2800)],
        format="xy",
        close=True,
    )
    with tempfile.NamedTemporaryFile(suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp.seek(0)
        return tmp.read()


def test_prepare_dxf_quicklook_extracts_site_metrics():
    payload = _dxf_payload_mm()

    quicklook = _prepare_dxf_quicklook(payload)
    metadata = quicklook.metadata

    assert pytest.approx(metadata["unit_scale_to_m"], rel=1e-6) == 0.001
    assert pytest.approx(metadata["site_area_sqm"], rel=1e-6) == 12.0
    assert pytest.approx(metadata["gross_floor_area_sqm"], rel=1e-6) == 18.9

    first_candidate = quicklook.candidates[0]
    assert pytest.approx(first_candidate.metadata["area_sqm"], rel=1e-6) == 12.0


def test_parse_dxf_payload_propagates_metadata():
    payload = _dxf_payload_mm()

    parsed = _parse_dxf_payload(payload)
    metadata = parsed.metadata

    assert pytest.approx(metadata["site_area_sqm"], rel=1e-6) == 12.0
    assert pytest.approx(metadata["gross_floor_area_sqm"], rel=1e-6) == 18.9
    assert metadata["parse_metadata"]["unit_scale_to_m"] == 0.001

    space = next(iter(parsed.graph.spaces.values()))
    assert pytest.approx(space.metadata["area_sqm"], rel=1e-6) == 12.0
