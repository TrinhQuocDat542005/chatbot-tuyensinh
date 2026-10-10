from scripts.audit_repository import findings


def test_secret_is_detected_without_disclosing_value():
    token = 'ghp_' + 'a' * 36
    result = findings(('token=' + token).encode(), 'settings.txt')
    assert result == [{'path': 'settings.txt', 'line': 1, 'kind': 'github-token'}]
    assert token not in repr(result)


def test_environment_file_is_reported_even_without_recognized_token():
    assert findings(b'PASSWORD=something', '.env') == [
        {'path': '.env', 'kind': 'tracked-environment-file'}]
    assert findings(b'PORT=5005', '.env.example') == []


def test_binary_is_outside_scanner_scope():
    assert findings(b'\x00' + ('ghp_' + 'b' * 36).encode(), 'model.tar.gz') == []
