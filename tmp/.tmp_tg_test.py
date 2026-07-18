import json, re, urllib.parse, urllib.request
import yaml

tok = None
for line in open('/root/.hermes/.env'):
    m = re.match(r'(?:export\s+)?TELEGRAM[A-Z_]*TOKEN\s*=\s*(.+)', line.strip())
    if m:
        tok = m.group(1).strip().strip('"').strip("'")
        break
chat = str(yaml.safe_load(open('/root/.hermes/config.yaml'))['telegram']['allowed_chats'])
print('token found:', bool(tok), '| chat:', chat)
data = urllib.parse.urlencode({
    'chat_id': chat,
    'text': 'hh-auto-apply: тест доставки отчётов — если видишь это сообщение, канал работает'}).encode()
r = json.load(urllib.request.urlopen(
    'https://api.telegram.org/bot' + tok + '/sendMessage', data=data, timeout=20))
print('ok:', r.get('ok'), '| chat:',
      r.get('result', {}).get('chat', {}).get('title') or r.get('result', {}).get('chat', {}).get('id'))
