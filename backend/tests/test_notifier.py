from app.services.notifier import LogNotifier, notify, set_notifier


def test_log_notifier(caplog):
    set_notifier(LogNotifier())
    with caplog.at_level("INFO"):
        notify("test message")
    assert "test message" in caplog.text


def test_notify_default():
    # 기본 알림은 LogNotifier, 에러 없이 동작
    notify("hello")
