import sys
sys.path.insert(0, '.')
from monitor import fetch_sohu_news, fetch_news, fetch_eastmoney_news, fetch_wallstreetcn_news, fetch_jin10_news, analyze_all
from collections import Counter

# 模拟主流程
news = fetch_news(pages=1, page_size=20)
em_news = fetch_eastmoney_news(pages=1, page_size=20)
wscn_news = fetch_wallstreetcn_news(limit=20)
jin10_news = fetch_jin10_news()
sohu_news = fetch_sohu_news(pages=1, page_size=20)

seen_titles = set(n.get('title','')[:20] for n in news)
for en in em_news + wscn_news + jin10_news + sohu_news:
    if en['title'][:20] not in seen_titles:
        news.append(en)
        seen_titles.add(en['title'][:20])

hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)

# all_news 是按时间排序的，最新的在前
# 检查不同位置的 source 分布
print('all_news 总长度:', len(all_news))
print('all_news[:50] source:', Counter(n.get('source', '') for n in all_news[:50]))
print('all_news[50:100] source:', Counter(n.get('source', '') for n in all_news[50:100]))
print('all_news[100:150] source:', Counter(n.get('source', '') for n in all_news[100:150]))
print('all_news[150:200] source:', Counter(n.get('source', '') for n in all_news[150:200]))

# 找出 sohu 新闻在 all_news 中的位置
sohu_positions = [i for i, n in enumerate(all_news) if n.get('source') == 'sohu']
print('\nsohu 新闻在 all_news 中的位置:', sohu_positions[:10])
print('第一个 sohu 在位置:', sohu_positions[0] if sohu_positions else 'None')
print('sohu 新闻总数:', len(sohu_positions))