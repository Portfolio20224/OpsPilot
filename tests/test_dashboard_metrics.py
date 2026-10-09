from app.core.dashboard_metrics import percentile


def test_percentile_uses_linear_interpolation():
    assert percentile([10.0, 20.0, 30.0, 40.0], 0.5) == 25.0


def test_percentile_returns_none_for_empty_values():
    assert percentile([], 0.95) is None