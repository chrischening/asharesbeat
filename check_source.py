import json
import re
import os
from collections import Counter

# 读取 index.html
with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有 JSON 数据块
# 查找 const ALL=[ ... ]; 模式
match = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if match:
    json_str = '[' + match.group(1) + ']'
    try:
        items = json.loads(json_str)
        sources = [item.get('source', '') for item in items]
        print(f'Total items in ALL: {len(items)}')
        print('Source distribution:')
        for src, cnt in Counter(sources).most_common():
            print(f'  "{src}": {cnt}')
        
        # 找出有 source 的条目
        sohu_items = [i for i in items if i.get('source') == 'sohu']
        print(f'\nSohu items: {len(sohu_items)}')
        if sohu_items:
            print('First 3 sohu items:')
            for item in sohu_items[:3]:
                print(f'  - {item.get("title", "")[:50]}')
    except Exception as e:
        print(f'Error parsing: {e}')
else:
    print('Could not find ALL data')