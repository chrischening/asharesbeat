import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查 ALL 数据
m = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if m:
    json_str = '[' + m.group(1) + ']'
    items = json.loads(json_str)
    
    print('ALL total items:', len(items))
    
    from collections import Counter
    sources = Counter(i.get('source', '') for i in items)
    print('Source distribution in ALL:')
    for src, cnt in sources.most_common():
        print('  "{}": {}'.format(src, cnt))
    
    positions = [i for i, it in enumerate(items) if it.get('source') == 'sohu']
    print('\nsohu count in ALL:', len(positions))
    if positions:
        print('first sohu position:', positions[0])