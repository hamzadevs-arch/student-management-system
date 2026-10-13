"""Unauthenticated smoke checks for a CampusFlow deployment (stdlib only).

Usage: python campusflow/scripts/smoke_check.py https://your-service.onrender.com
Never include credentials in the URL or command.
"""
import sys
import urllib.error
import urllib.request


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as res:
            return res.status, res.headers.get('Content-Type', ''), res.read(500)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get('Content-Type', ''), exc.read(500)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith(('https://','http://')):
        raise SystemExit('Usage: python scripts/smoke_check.py https://your-campusflow-url')
    base = sys.argv[1].rstrip('/')
    checks = [
        ('API health', '/api/health', 200, b'"status":"ok"'),
        ('Release information', '/api/version', 200, b'"phase":13'),
        ('Unauthenticated access denied', '/api/students', 401, None),
        ('Frontend login shell', '/', 200, b'<html'),
        ('Unknown API path rejected', '/api/path-does-not-exist', 404, None),
    ]
    failed = False
    for name, path, status, content in checks:
        try:
            code, ctype, body = fetch(base + path)
            passed = code == status and (content is None or content in body.lower())
            print(f'{"PASS" if passed else "FAIL"} {name}: HTTP {code}')
        except Exception as exc:
            passed = False
            print(f'FAIL {name}: {exc}')
        failed |= not passed
    if failed:
        raise SystemExit(1)
    print('Deployment smoke checks passed.')


if __name__ == '__main__':
    main()
