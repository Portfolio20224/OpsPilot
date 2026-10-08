from app.core.observability import (
    generate_request_id,
    measure_operation,
)


def test_generate_request_id():
    request_id = generate_request_id()

    assert isinstance(request_id, str)
    assert len(request_id) > 0


def test_measure_operation_logs_duration(caplog):
    with caplog.at_level("INFO", logger="opspilot"):
        with measure_operation(
            operation="test_operation",
            request_id="test-request",
        ):
            pass

    assert "operation=test_operation" in caplog.text
    assert "request_id=test-request" in caplog.text
    assert "duration_ms=" in caplog.text