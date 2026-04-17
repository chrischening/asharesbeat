import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查所有数据块
data_blocks = ['ALL', 'ALL_A', 'ALL_HK', 'ALL_US', 'BULL', 'BEAR', 'NEUT']

for block_name in data_blocks:
    pattern = r'const {}=\[(.*?)\];'.format(block_name)
    m = re.search(pattern, content, re.DOTALL)
    if m:
        try:
            items = json.loads('[' + m.group(1) + ']')
            sources = {}
            for it in items:
                src = it.get('source', '')
                sources[src] = sources.get(src, 0) + 1
            print('{} ({} items): {}'.format(block_name, len(items), sources))
        except:
            print('{}: parse error'.format(block_name))