import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查 __ALL_NEWS_JSON__ 占位符是否被替换
print('Checking __ALL_NEWS_JSON__ placeholder:')
if '__ALL_NEWS_JSON__' in content:
    print('  Found placeholder, NOT replaced!')
else:
    print('  Placeholder was replaced')

# 在 ALL 中查找有 source 字段的条目
m = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if m:
    json_str = '[' + m.group(1) + ']'
    try:
        items = json.loads(json_str)
        # 检查前几条
        print('\nFirst 5 items source field:')
        for i, item in enumerate(items[:5]):
            src = item.get('source', '')
            print(f'  {i}: source="{src}"')
    except Exception as e:
        print(f'Error: {e}')
        # 打印前500字符看看
        print(f'JSON snippet: {json_str[:500]}')