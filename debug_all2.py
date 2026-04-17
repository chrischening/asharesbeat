import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const ALL=\[(.*?)\];', content, re.DOTALL)
if m:
    json_str = '[' + m.group(1) + ']'
    items = json.loads(json_str)
    
    # 统计所有150条的source
    from collections import Counter
    sources = Counter(i.get('source', '') for i in items)
print('ALL[:300] source 分布:')
for src, cnt in sources.most_common():
        print('  "{}": {}'.format(src, cnt))
    
    # 找 sohu 在 ALL 中的位置
    positions = [i for i, it in enumerate(items) if it.get('source') == 'sohu']
    print('\nsohu 在 ALL[:150] 中的位置: {} 项'.format(len(positions)))
    if positions:
        print('位置: {}'.format(positions))
    
    # 如果 ALL[:150] 没有 sohu，那检查是否有其他包含 sohu 的数据块
    # 检查 BULL/NEUT 等
    print('\n--- 检查其他数据块 ---')
    
    # BULL
    m2 = re.search(r'const BULL=\[(.*?)\];', content, re.DOTALL)
    if m2:
        bull = json.loads('[' + m2.group(1) + ']')
        bull_src = Counter(i.get('source', '') for i in bull)
        print('BULL source:', dict(bull_src))
    
    # NEUT  
    m3 = re.search(r'const NEUT=\[(.*?)\];', content, re.DOTALL)
    if m3:
        neut = json.loads('[' + m3.group(1) + ']')
        neut_src = Counter(i.get('source', '') for i in neut)
        print('NEUT source:', dict(neut_src))