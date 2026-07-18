# One-off E2E on prod: create a test subagent, verify bot+connector+self-learning, delete it.
import json
import sys
import urllib.request

sys.path.insert(0, "/var/www/albery")
from app import app  # noqa: E402
import agent_center  # noqa: E402

with app.test_request_context('/api/agent-center/agents', method='POST',
                              json={'name': 'Тест Агент', 'tier': 'faq',
                                    'role_prompt': 'Ты тестовый агент.', 'members': []}):
    resp = agent_center.agent_center_create_agent()
data = resp.get_json() if not isinstance(resp, tuple) else resp[0].get_json()
print('CREATE:', data)
slug = data['slug']

cfg = open('/root/.hermes/config.yaml', encoding='utf-8').read()
print('connector in config:', f'agent-{slug}:' in cfg)

agent = agent_center._agent_by_slug(slug)
url = f'http://127.0.0.1:5002/mcp-agent/{slug}/' + agent['mcp_token']


def rpc(payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


tl = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})
names = [t['name'] for t in tl['result']['tools']]
print('tools:', len(names), '| self-learning:', sorted(n for n in names if '_my_' in n))
print('admin leak:', [n for n in names if n in ('upsert_ai_instruction', 'delete_bitrix_task', 'update_ai_capabilities')])

r2 = rpc({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
          'params': {'name': 'upsert_my_instruction',
                     'arguments': {'name': 'Тестовый навык', 'content': 'Проверка самообучения.'}}})
print('learn:', r2.get('result') or r2.get('error'))

agent_center._agent_cache_bust()
d = agent_center._agent_by_slug(slug)
print('instructions in db:', [(i['name'], i['source']) for i in d['instructions']])

with app.test_request_context(f'/api/agent-center/agents/{slug}', method='DELETE'):
    print('DELETE:', agent_center.agent_center_agent_delete(slug).get_json())

cfg2 = open('/root/.hermes/config.yaml', encoding='utf-8').read()
print('connector removed:', f'agent-{slug}:' not in cfg2)
import yaml  # noqa: E402
yaml.safe_load(cfg2)
print('config still valid yaml: True')
