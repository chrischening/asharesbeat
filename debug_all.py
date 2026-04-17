import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if m:
    json_str = '[' + m.group(1) + ']'
    items = json.loads(json_str)
    
    # 统计 ALL 中每条新闻的 source
    from collections import Counter
    sources = Counter(i.get('source', '') for i in items)
    print('Source distribution in ALL (first 150 items):')
    for src, cnt in sources.most_common():
        print('  "{}": {}'.format(src, cnt))
    
    # 检查前10条是否都是空 source
    print('\nFirst 10 items:')
    for i, item in enumerate(items[:10]):
        src = item.get('source', '')
        print('  {}: source="{}"'.format(i, src))