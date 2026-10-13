import os, json, urllib.request
for k in ('HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy','ALL_PROXY','all_proxy'):
    os.environ.pop(k, None)
os.environ['no_proxy'] = '127.0.0.1,localhost'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
q = json.loads(opener.open('http://127.0.0.1:8188/queue', timeout=15).read())
print('运行中:', len(q.get('queue_running', [])), ' 排队:', len(q.get('queue_pending', [])))
for it in q.get('queue_running', []):
    print('  RUN ', it[0], it[1])
for it in q.get('queue_pending', []):
    print('  WAIT', it[0], it[1])
h = json.loads(opener.open('http://127.0.0.1:8188/history', timeout=20).read())
print('--- 最近完成 ---')
items = sorted(h.items(), key=lambda kv: kv[1].get('status',{}).get('completed',0))[-8:]
for pid, d in items:
    outs = d.get('outputs', {})
    names = [o.get('filename','') for v in outs.values() for o in v.get('gifs',[])]
    print('  ', pid[:8], d.get('status',{}).get('status_str'), names)
