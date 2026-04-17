import sys
sys.path.insert(0, '.')
from monitor import fetch_sohu_news, analyze_all
import json

# 测试 fetch_sohu_news
news = fetch_sohu_news(pages=1, page_size=5)
print(f'Fetched {len(news)} sohu news')
print(f'First item keys: {list(news[0].keys())}')
first_source = news[0].get('source', '')
print(f'First item source: "{first_source}"')

# 测试 analyze_all
hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)
print(f'\nanalyze_all returned {len(all_news)} items')
if all_news:
    print(f'First item keys: {list(all_news[0].keys())}')
    src = all_news[0].get('source', '')
    print(f'First item source: "{src}"')
    
# 检查 all_news 中有 source 的数量
non_empty = [n for n in all_news if n.get('source')]
print(f'\nItems with non-empty source: {len(non_empty)}')