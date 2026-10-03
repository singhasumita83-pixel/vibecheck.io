import urllib.request
import time
import json

def test_live_analyze():
    with open('static/demo/bad_app.png', 'rb') as f:
        img_data = f.read()

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="image"; filename="screenshot.png"\r\n'
        b'Content-Type: image/png\r\n\r\n' + img_data + b'\r\n'
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="persona"\r\n\r\n'
        b'Busy professional\r\n'
        b'--' + boundary.encode() + b'\r\n'
        b'Content-Disposition: form-data; name="goal"\r\n\r\n'
        b'Approve inventory order\r\n'
        b'--' + boundary.encode() + b'--\r\n'
    )

    req = urllib.request.Request(
        'http://127.0.0.1:5000/api/analyze',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        elapsed = time.time() - t0
        print(f"Status Code: {resp.status}")
        print(f"Server Response Time: {elapsed*1000:.1f}ms")
        print(f"Model Serving: {data['model']['name']} ({data['model']['served_by']})")
        print(f"Findings Count: {len(data['findings'])}")
        print(f"Summary Scores: {data['summary']['scores']}")
        print(f"Fix Plan Items: {len(data['fix_plan'])}")
        print("\nLIVE LOCALHOST ANALYSIS TEST PASSED WITH FLYING COLORS!")

if __name__ == "__main__":
    test_live_analyze()
