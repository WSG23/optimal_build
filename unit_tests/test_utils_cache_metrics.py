import math
from types import SimpleNamespace

import pytest

from app.utils import metrics
from app.utils import cache as cache_module
from app.utils.cache import TTLCache


class _FakeTime:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value


def test_ttlcache_rejects_non_positive_ttl():
    with pytest.raises(ValueError):
        TTLCache(0)


@pytest.mark.anyio
async def test_ttlcache_stores_copies_and_expires(monkeypatch):
    fake_time = _FakeTime()
    monkeypatch.setattr(cache_module, "time", fake_time)
    cache = TTLCache(1.0, copy=lambda v: list(v))

    await cache.set("key", [1, 2])
    cached = await cache.get("key")
    assert cached == [1, 2]
    cached.append(3)
    # Original value is copied, so mutation does not leak
    cached_again = await cache.get("key")
    assert cached_again == [1, 2]

    fake_time.value = 2.0
    assert await cache.get("key") is None

    await cache.set("key", {"a": 1})
    await cache.invalidate("key")
    assert await cache.get("key") is None

    await cache.set("key", {"b": 2})
    await cache.clear()
    assert await cache.get("key") is None


@pytest.mark.anyio
async def test_ttlcache_returns_original_when_no_copy(monkeypatch):
    fake_time = _FakeTime()
    monkeypatch.setattr(cache_module, "time", fake_time)
    cache = TTLCache(1.0)
    payload = {"original": True}
    await cache.set("key", payload)
    cached = await cache.get("key")
    assert cached is payload


def test_counter_value_for_labeled_and_unlabeled_counters():
    metrics.reset_metrics()
    metrics.REQUEST_COUNTER.labels(endpoint="root").inc()
    assert metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "root"}) == 1.0

    metrics.PWP_BUILDABLE_TOTAL.inc()
    assert metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {}) == 1.0


def test_counter_value_handles_label_errors_and_registry_fallback(monkeypatch):
    class _FakeSample:
        def __init__(self, value: float):
            self._value = SimpleNamespace(get=lambda: value)

    class _RaisingCounter:
        _labelnames = ("a", "b")
        _name = "raising_counter"

        def labels(self, *args, **kwargs):
            if kwargs:
                raise TypeError("kwargs not supported")
            if len(args) != 2:
                raise ValueError("missing labels")
            return _FakeSample(5.0)

    metrics.reset_metrics()
    assert metrics.counter_value(_RaisingCounter(), {"a": "x", "b": "y"}) == 5.0

    class _RegistryOnly:
        _labelnames: tuple[str, ...] = ()
        _name = "registry_only"

    class _Registry:
        def get_sample_value(self, name: str, _labels: dict[str, str]) -> float | None:
            return 7.0 if name == "registry_only" else None

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    assert metrics.counter_value(_RegistryOnly(), {}) == 7.0

    class _EmptyRegistry:
        def get_sample_value(self, *_args, **_kwargs):
            return None

    class _ValueErrorCounter(_RaisingCounter):
        _name = "value_error_counter"

        def labels(self, *args, **kwargs):
            if kwargs:
                raise TypeError("kwargs not supported")
            raise ValueError("bad positional")

    monkeypatch.setattr(metrics, "REGISTRY", _EmptyRegistry())
    assert metrics.counter_value(_ValueErrorCounter(), {"a": "x", "b": "y"}) == 0.0


def test_counter_value_registry_sample_getter(monkeypatch):
    class _Registry:
        def get_sample_value(self, name: str, labels: dict[str, str]) -> float | None:
            if name == "sampled_counter" and labels.get("tag") == "v":
                return 3.5
            return None

    class _Counter:
        _labelnames: tuple[str, ...] = ()
        _name = "sampled_counter"

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    assert metrics.counter_value(_Counter(), {"tag": "v"}) == 3.5
    assert metrics.counter_value(_Counter(), {"tag": "none"}) == 0.0


def test_counter_value_registry_none_path(monkeypatch):
    class _Registry:
        def get_sample_value(self, name: str, labels: dict[str, str]) -> float | None:
            assert name == "none_counter"
            assert labels == {"foo": "bar"}
            return None

    class _Counter:
        _labelnames: tuple[str, ...] = ()
        _name = "none_counter"

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    assert metrics.counter_value(_Counter(), {"foo": "bar"}) == 0.0


def test_counter_value_without_sample_getter(monkeypatch):
    class _Registry:
        pass

    class _Counter:
        _labelnames: tuple[str, ...] = ()
        _name = "nameless"

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    assert metrics.counter_value(_Counter(), {"foo": "bar"}) == 0.0


def test_histogram_percentile_validations_and_empty_data():
    metrics.reset_metrics()
    with pytest.raises(ValueError):
        metrics.histogram_percentile(metrics.REQUEST_LATENCY_MS, -0.1)

    hist = metrics.Histogram(
        "custom_histogram",
        "doc",
        labelnames=("endpoint",),
        registry=metrics.REGISTRY,
    )
    with pytest.raises(RuntimeError):
        metrics.histogram_percentile(hist, 0.5, labels={"endpoint": "missing"})


def test_histogram_percentile_with_observations():
    metrics.reset_metrics()
    hist = metrics.REQUEST_LATENCY_MS
    sample = hist.labels(endpoint="root")
    sample.observe(10.0)
    sample.observe(30.0)

    result = metrics.histogram_percentile(hist, 0.5, labels={"endpoint": "root"})
    assert result.percentile == 0.5
    assert 10.0 <= result.value <= 30.0


def test_histogram_percentile_uses_observations_and_metric_map():
    class _Sample:
        def bucket_counts(self):
            return [(1.0, 1.0), (2.0, 2.0)]

        def observations(self):
            return [1.0, 3.0]

    class _Histogram:
        _metrics = {("x",): _Sample()}
        _labelnames = ("endpoint",)
        _name = "fake_hist"

    histogram = _Histogram()
    result = metrics.histogram_percentile(
        histogram, 0.5, labels={"endpoint": "x"}
    )
    assert result.value == 2.0
    assert result.buckets == ((1.0, 1.0), (2.0, 2.0))


def test_histogram_percentile_uses_bucket_fallback_when_no_observations():
    class _Sample:
        def bucket_counts(self):
            return [(1.0, 1.0), (2.0, 3.0)]

        def observations(self):
            return []

    class _Histogram:
        _metrics = {("x",): _Sample()}
        _labelnames = ("endpoint",)
        _name = "fake_hist"

    histogram = _Histogram()
    result = metrics.histogram_percentile(
        histogram, 0.5, labels={"endpoint": "x"}
    )
    assert result.value == 1.25


def test_collect_histogram_data_prefers_metric_map(monkeypatch):
    class _Sample:
        def bucket_counts(self):
            return [(1.0, 1.0)]

        def observations(self):
            return [2.0]

    class _Histogram:
        _metrics = {("label",): _Sample()}
        _labelnames = ("endpoint",)
        _name = "metric_map_histogram"

    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "label"}
    )
    assert buckets == [(1.0, 1.0)]
    assert observations == [2.0]


def test_collect_histogram_data_metric_map_without_buckets(monkeypatch):
    class _Sample:
        def bucket_counts(self):
            return []

        def observations(self):
            return []

    class _Histogram:
        _metrics = {("x",): _Sample()}
        _labelnames = ("endpoint",)
        _name = "no_bucket_histogram"

    class _Registry:
        def collect(self):
            return []

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "x"}
    )
    assert buckets == []
    assert observations == []


def test_collect_histogram_data_metric_map_then_registry(monkeypatch):
    class _Sample:
        def bucket_counts(self):
            return []

        def observations(self):
            return []

    class _Histogram:
        _metrics = {("y",): _Sample()}
        _labelnames = ("endpoint",)
        _name = "hybrid_histogram"

    class _RegSample:
        def __init__(self, name: str, labels: dict[str, str], value: float):
            self.name = name
            self.labels = labels
            self.value = value

    class _Metric:
        def __init__(self):
            self.name = "hybrid_histogram"
            self.samples = [
                _RegSample("hybrid_histogram_bucket", {"le": "1.0", "endpoint": "y"}, 1.0),
                _RegSample("hybrid_histogram_bucket", {"le": "+Inf", "endpoint": "y"}, 2.0),
                _RegSample("hybrid_histogram_bucket", {"le": "bad", "endpoint": "y"}, 0.0),
            ]

    class _Registry:
        def collect(self):
            return [_Metric()]

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "y"}
    )
    assert buckets[-1] == (float("inf"), 2.0)
    assert observations == []


def test_collect_histogram_data_metrics_map_missing_key(monkeypatch):
    class _Histogram:
        _metrics = {}
        _labelnames = ("endpoint",)
        _name = "missing_key_histogram"

    class _Registry:
        def collect(self):
            return []

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "nope"}
    )
    assert buckets == []
    assert observations == []


def test_collect_histogram_data_registry_missing_bound(monkeypatch):
    class _Sample:
        def __init__(self, labels: dict[str, str], value: float):
            self.name = "boundless_histogram_bucket"
            self.labels = labels
            self.value = value

    class _Metric:
        def __init__(self):
            self.name = "boundless_histogram"
            self.samples = [
                _Sample({"endpoint": "c"}, 1.0),
                _Sample({"endpoint": "c", "le": "+Inf"}, 2.0),
            ]

    class _Registry:
        def collect(self):
            return [_Metric()]

    class _Histogram:
        _metrics: dict = {}
        _labelnames = ("endpoint",)
        _name = "boundless_histogram"

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "c"}
    )
    assert buckets[-1] == (float("inf"), 2.0)


def test_collect_histogram_data_registry_path(monkeypatch):
    class _Sample:
        def __init__(self, name: str, labels: dict[str, str], value: float):
            self.name = name
            self.labels = labels
            self.value = value

    class _Metric:
        def __init__(self, name: str, samples):
            self.name = name
            self.samples = samples

    class _Registry:
        def __init__(self):
            self._metrics = [
                _Metric("registry_histogram", None),
                _Metric(
                    "registry_histogram",
                    [
                        _Sample("registry_histogram_bucket", {"le": "1.0", "endpoint": "a"}, 1.0),
                        _Sample("registry_histogram_bucket", {"le": "+Inf", "endpoint": "a"}, 2.0),
                        _Sample("registry_histogram_bucket", {"le": "bad", "endpoint": "a"}, 0.0),
                        _Sample("registry_histogram_bucket", {"le": "3.0", "endpoint": "b"}, 3.0),
                    ],
                ),
            ]

        def collect(self):
            return list(self._metrics)

    class _Histogram:
        _metrics: dict = {}
        _labelnames = ("endpoint",)
        _name = "registry_histogram"

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {"endpoint": "a"}
    )
    assert observations == []
    assert buckets[-1] == (float("inf"), 2.0)
    # Ensure invalid and mismatched labels were skipped
    assert (3.0, 3.0) not in buckets


def test_collect_histogram_data_non_dict_metrics_map(monkeypatch):
    class _Histogram:
        _metrics = "not-a-dict"
        _labelnames: tuple[str, ...] = ()
        _name = "non_dict_histogram"

    class _Registry:
        def collect(self):
            return []

    monkeypatch.setattr(metrics, "REGISTRY", _Registry())
    buckets, observations = metrics._collect_histogram_data(
        _Histogram(), {}
    )
    assert buckets == []
    assert observations == []


def test_histogram_percentile_from_bucket_counts():
    buckets = [(1.0, 1.0), (2.0, 3.0), (math.inf, 3.0)]
    result = metrics.histogram_percentile_from_bucket_counts(buckets, 0.5)
    assert result.value == pytest.approx(1.25)

    with pytest.raises(ValueError):
        metrics.histogram_percentile_from_bucket_counts(buckets, 1.5)

    with pytest.raises(RuntimeError):
        metrics.histogram_percentile_from_bucket_counts([], 0.5)


def test_percentile_helpers_error_paths():
    with pytest.raises(ValueError):
        metrics._percentile_from_buckets([], 0.5)
    with pytest.raises(ValueError):
        metrics._percentile_from_buckets([(1.0, 0.0)], 0.5)
    with pytest.raises(ValueError):
        metrics._percentile_from_observations([], 0.5)


def test_percentile_helpers_interpolation_and_singleton():
    assert metrics._percentile_from_observations([5.0], 0.7) == 5.0
    assert metrics._percentile_from_observations([1.0, 3.0, 5.0], 0.5) == 3.0
    assert metrics._percentile_from_observations([1.0, 9.0], 0.25) == 3.0

    buckets = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
    assert metrics._percentile_from_buckets(buckets, 0.5) == 1.5
    buckets_with_inf = [(1.0, 1.0), (math.inf, 2.0)]
    assert metrics._percentile_from_buckets(buckets_with_inf, 0.5) == 1.0
    buckets_stalled = [(1.0, 0.0), (2.0, 0.0), (3.0, 5.0)]
    assert metrics._percentile_from_buckets(buckets_stalled, 0.0) == 1.0
    buckets_all_inf = [(math.inf, 5.0)]
    assert metrics._percentile_from_buckets(buckets_all_inf, 0.5) == 0.0
    buckets_nan = [(1.0, math.nan)]
    assert metrics._percentile_from_buckets(buckets_nan, 0.5) == 1.0


def test_collect_histogram_data_and_label_matching():
    metrics.reset_metrics()
    hist = metrics.REQUEST_LATENCY_MS
    hist.labels(endpoint="first").observe(5.0)

    buckets, observations = metrics._collect_histogram_data(
        hist, {"endpoint": "first"}
    )
    assert buckets
    if observations:
        assert observations == [5.0]
    else:
        assert buckets[-1][1] >= 1.0
    assert metrics._labels_match({"a": "1"}, {"a": "1"})
    assert metrics._labels_match({"a": "1", "b": "2"}, {"a": "1"})
    assert metrics._labels_match({"endpoint": "first"}, {"endpoint": "first"})
    assert not metrics._labels_match({"endpoint": "first"}, {"endpoint": "second"})


def test_export_and_render_metrics_returns_bytes():
    metrics.reset_metrics()
    payload = metrics.export_metrics()
    rendered = metrics.render_latest_metrics()
    assert isinstance(payload, (bytes, bytearray))
    assert isinstance(rendered, (bytes, bytearray))
    assert b"api_requests_total" in payload
