import json
import time
from urllib import request

API_URL = 'https://realtime-agent-api-283909500477.us-central1.run.app/api/v1/analyze-log'

payload = {
    'log_line': 'ERROR - CRITICAL FAILURE: NullPointerException in generate_report()'
}

data = json.dumps(payload).encode('utf-8')
req = request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf-8')
        print('status:', resp.getcode())
        print('body:', body)
        try:
            j = json.loads(body)
            wid = j.get('workflow_id')
            if wid:
                wf_url = f'https://realtime-agent-api-283909500477.us-central1.run.app/api/v1/workflow/{wid}'
                # Poll until finished or timeout
                deadline = time.time() + 60
                while time.time() < deadline:
                    try:
                        with request.urlopen(wf_url, timeout=30) as wr:
                            body2 = wr.read().decode('utf-8')
                            print('workflow poll body:', body2)
                            try:
                                j2 = json.loads(body2)
                                st = j2.get('status')
                                if st and st != 'started':
                                    break
                            except Exception:
                                pass
                    except Exception as e:
                        print('poll error:', e)
                    time.sleep(3)
        except Exception:
            pass
except Exception as e:
    print('request failed:', e)
