import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if m:
    items = json.loads('[' + m.group(1) + ']')
    # 找到有 source 的条目
    sohu_items = [i for i in items if i.get('source') == 'sohu']
    print('ALL 中有 sohu source 的条目数:', len(sohu_items))
    if sohu_items:
        print('第一条 sohu 新闻:', sohu_items[0].get('title', '')[:60])
        src = sohu_items[0].get('source', '')
        print('source 值:', repr(src))