import sys
sys.path.insert(0, '.')
from monitor import fetch_sohu_news, fetch_news, fetch_eastmoney_news, fetch_wallstreetcn_news, fetch_jin10_news, analyze_all, beijing_now
from datetime import datetime, timedelta, timezone
import time

BJT = timezone(timedelta(hours=8))

# 模拟主流程
print('[1/7] 获取同花顺资讯...')
news = fetch_news(pages=1, page_size=20)

print('[2/7] 获取东方财富 + 华尔街见闻 + 金十数据 + 搜狐财经...')
em_news = fetch_eastmoney_news(pages=1, page_size=20)
wscn_news = fetch_wallstreetcn_news(limit=20)
jin10_news = fetch_jin10_news()
sohu_news = fetch_sohu_news(pages=1, page_size=20)

seen_titles = set(n.get('title','')[:20] for n in news)
for en in em_news + wscn_news + jin10_news + sohu_news:
    if en['title'][:20] not in seen_titles:
        news.append(en)
        seen_titles.add(en['title'][:20])

print(f'合并后 {len(news)} 条')

print('[3/7] 分析情绪 / 提取热点...')
hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)

print(f'all_news 总数: {len(all_news)}')

# 检查 all_news 中的 source 分布
from collections import Counter
sources = Counter(n.get('source', '') for n in all_news)
print('all_news source 分布:')
for src, cnt in sources.most_common():
    print('  {}: {}'.format(src, cnt))

# 检查排序后的顺序
print('\nall_news 前10条:')
for i, n in enumerate(all_news[:10]):
    src = n.get('source', '')
    print('  {}: source="{}", time={}'.format(i, src, n.get('time')))
    
# 检查 all_news[:150] 的 source
first_150 = all_news[:150]
sources_150 = Counter(n.get('source', '') for n in first_150)
print('\nall_news[:150] source 分布:')
for src, cnt in sources_150.most_common():
    print('  {}: {}'.format(src, cnt))