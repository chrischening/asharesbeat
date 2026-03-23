#!/usr/bin/env python3
"""
A股利好监控工具 v4
- 实时新闻：利好个股 + 实时报价 + 连涨龙头 + 弹性评分 (前端自动刷新)
- 今日热点股 TOP 7
- 热门板块/ETF 详细面板 (价格+涨跌+情绪方向+相关个股)
- 国内基金监控：热门基金排行 + 实时估值 + 基金新闻
- 夜间新闻大合集 (22:00–08:30 按影响力排序)
数据源：同花顺 7x24 + 东方财富快讯 + 天天基金 + 腾讯行情 + 腾讯日K
"""
import requests, json, re, time, os, sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# ═══ BEIJING TIME HELPER ═══════════════════════════════════
BJT = timezone(timedelta(hours=8))
def beijing_now():
    """Return current Beijing time (UTC+8), timezone-aware."""
    return datetime.now(BJT)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
THS = {'User-Agent': UA, 'Referer': 'https://news.10jqka.com.cn/', 'Accept': 'application/json'}
EM  = {'User-Agent': UA, 'Referer': 'https://www.eastmoney.com/', 'Accept': 'application/json'}
QT  = {'User-Agent': UA, 'Referer': 'https://finance.qq.com/'}

# ═══ SECTOR / ETF MAP ═══════════════════════════════════════
SECTOR_ETF = {
    '半导体':   {'etf':'512480','name':'半导体ETF','desc':'芯片/集成电路/晶圆'},
    '芯片':     {'etf':'512480','name':'半导体ETF','desc':'芯片/集成电路/晶圆'},
    '新能源':   {'etf':'516160','name':'新能源ETF','desc':'风电/光伏/储能'},
    '光伏':     {'etf':'515790','name':'光伏ETF','desc':'组件/逆变器/硅料'},
    '锂电池':   {'etf':'159755','name':'锂电池ETF','desc':'电芯/正负极材料'},
    '新能源汽车':{'etf':'515030','name':'新能源车ETF','desc':'整车/零部件/充电'},
    '汽车':     {'etf':'516110','name':'汽车ETF','desc':'整车/零部件'},
    '房地产':   {'etf':'512200','name':'房地产ETF','desc':'开发商/物业/地产链'},
    '医药':     {'etf':'512010','name':'医药ETF','desc':'制药/器械/医疗服务'},
    '创新药':   {'etf':'159992','name':'创新药ETF','desc':'生物医药/CRO/CXO'},
    '白酒':     {'etf':'512690','name':'白酒ETF','desc':'高端/次高端白酒'},
    '食品饮料': {'etf':'515170','name':'食品饮料ETF','desc':'食品/乳制品/饮料'},
    '银行':     {'etf':'512800','name':'银行ETF','desc':'国有/股份制/城商行'},
    '券商':     {'etf':'512000','name':'券商ETF','desc':'证券/投资银行'},
    '金融':     {'etf':'510230','name':'金融ETF','desc':'银行/保险/券商'},
    '保险':     {'etf':'512070','name':'保险ETF','desc':'人寿/财险'},
    '军工':     {'etf':'512660','name':'军工ETF','desc':'航空/航天/船舶/兵器'},
    '科技股':   {'etf':'515000','name':'科技ETF','desc':'TMT/软件/硬件'},
    '人工智能': {'etf':'515070','name':'AIETF','desc':'AI算力/大模型/应用'},
    'AI':       {'etf':'515070','name':'AIETF','desc':'AI算力/大模型/应用'},
    '机器人':   {'etf':'562500','name':'机器人ETF','desc':'工业/人形/核心零部件'},
    '消费':     {'etf':'159928','name':'消费ETF','desc':'家电/日用/零售'},
    '农业':     {'etf':'159825','name':'农业ETF','desc':'种植/养殖/农资'},
    '钢铁':     {'etf':'515210','name':'钢铁ETF','desc':'钢材/特钢/铁矿'},
    '煤炭':     {'etf':'515220','name':'煤炭ETF','desc':'动力煤/焦煤'},
    '有色金属': {'etf':'512400','name':'有色ETF','desc':'铜/铝/稀土/锂'},
    '石油':     {'etf':'159697','name':'石油ETF','desc':'油气开采/炼化/服务'},
    '天然气':   {'etf':'159697','name':'石油ETF','desc':'油气开采/炼化'},
    '原油':     {'etf':'159697','name':'石油ETF','desc':'油气/原油期货相关'},
    '黄金':     {'etf':'518880','name':'黄金ETF','desc':'金矿/金饰/黄金投资'},
    '通信':     {'etf':'515880','name':'通信ETF','desc':'运营商/设备/光模块'},
    '传媒':     {'etf':'512980','name':'传媒ETF','desc':'游戏/影视/出版'},
    '旅游':     {'etf':'159766','name':'旅游ETF','desc':'酒店/景区/航空'},
    '电力':     {'etf':'159611','name':'电力ETF','desc':'火电/水电/核电'},
    '基建':     {'etf':'516950','name':'基建ETF','desc':'铁路/公路/水利'},
    '数据中心': {'etf':'159515','name':'算力ETF','desc':'IDC/服务器/液冷'},
    '算力':     {'etf':'159515','name':'算力ETF','desc':'GPU/服务器/光模块'},
    '云计算':   {'etf':'516510','name':'云计算ETF','desc':'SaaS/IaaS/PaaS'},
    '网络安全': {'etf':'159899','name':'网安ETF','desc':'安全软件/密码/信创'},
    '储能':     {'etf':'159566','name':'储能ETF','desc':'电化学/抽水蓄能'},
    '港股':     {'etf':'513060','name':'恒生互联ETF','desc':'港股互联网龙头'},
    '中概股':   {'etf':'513050','name':'中概互联ETF','desc':'海外上市中国互联网'},
}

POLICY_KW = {
    '十五五':3,'十四五':2,'五年规划':3,'政府工作报告':3,'两会':2,
    '降准':2,'降息':2,'央行':1.5,'国务院':2,'证监会':1.5,
    '工信部':1.5,'发改委':1.5,'财政部':1.5,'国产替代':2,'自主可控':2,
    '新质生产力':2,'高质量发展':1.5,'科技创新':1.5,'数字经济':1.5,
    '碳中和':1.5,'碳达峰':1.5,'扩大内需':2,'消费升级':1.5,
}
HOT_KW = {
    'DeepSeek':2,'AI':2,'人工智能':2,'大模型':2,'机器人':2,
    '低空经济':2,'飞行汽车':2,'华为':1.5,'鸿蒙':1.5,
    '小米':1.5,'特斯拉':1.5,'卫星互联网':1.5,'量子':1.5,
    '英伟达':1.5,'具身智能':2,'人形机器人':2,
}
BULL_KW = [
    '增长','上涨','涨幅','利好','突破','新高','回购','增持',
    '净买入','净流入','中标','签订','合作','扶持','补贴',
    '超预期','扭亏','盈利','分红','战略合作','投资设立',
    '产能扩建','募资','纳入','获批','立项','发展规划',
    '降准','降息','加仓','买入','上调','回暖','复苏',
]
BEAR_KW = [
    '下降','下跌','减持','亏损','涉诉','处罚','违规',
    '立案','抽检不合格','实体清单','跌停','下行','承压',
    '鹰派','减值','暴跌','退市','违法','整改','风险',
    '做空','预警','亏','下滑','缩量','疲软',
]

# ═══ MARKET CONSTANTS ═══════════════════════════════════════
# THS stockMarket → market label
MARKET_MAP = {
    '22': 'A', '33': 'A', '151': 'A', '17': 'A',   # A股
    '177': 'HK',                                      # 港股
    '185': 'US',                                      # 美股
}
A_MARKETS = ('22', '33', '151', '17')
HK_MARKETS = ('177',)
US_MARKETS = ('185',)
ALL_MARKETS = A_MARKETS + HK_MARKETS + US_MARKETS

# HK/US sector-ETF mapping
SECTOR_ETF_HK = {
    '科技':   {'etf':'03032','name':'恒生科技ETF','desc':'港股科技龙头'},
    '互联网': {'etf':'03032','name':'恒生科技ETF','desc':'互联网/平台经济'},
    '医药':   {'etf':'03174','name':'恒生医药ETF','desc':'港股医药'},
    '金融':   {'etf':'02840','name':'恒生金融ETF','desc':'港股金融'},
    '地产':   {'etf':'03000','name':'恒生地产ETF','desc':'港股地产'},
    '消费':   {'etf':'03131','name':'恒生消费ETF','desc':'港股消费'},
}
SECTOR_ETF_US = {
    '科技':   {'etf':'QQQ','name':'纳指100ETF','desc':'美股科技巨头'},
    '半导体': {'etf':'SOXX','name':'半导体ETF','desc':'美股芯片'},
    'AI':     {'etf':'QQQ','name':'纳指100ETF','desc':'AI/大模型'},
    '新能源': {'etf':'TAN','name':'太阳能ETF','desc':'美股新能源'},
    '医药':   {'etf':'XBI','name':'生物科技ETF','desc':'美股生物医药'},
    '金融':   {'etf':'XLF','name':'金融ETF','desc':'美股金融'},
}

# ═══ 1. FETCH NEWS ══════════════════════════════════════════
def fetch_news(pages=4, page_size=40):
    all_news, seen = [], set()
    # A股 tags: '' (all), '-21101' (important), '21109' (opportunity)
    # 港股: '21105', 美股: '21107'
    for tag in ['', '-21101', '21109', '21105', '21107']:
        pg_count = pages if tag in ['', '-21101', '21109'] else 2  # fewer pages for HK/US
        for pg in range(1, pg_count+1):
            url = f'https://news.10jqka.com.cn/tapp/news/push/stock/?page_size={page_size}&track=website&tag={tag}&page={pg}'
            try:
                r = requests.get(url, headers=THS, timeout=10)
                d = r.json()
                if d.get('code')=='200':
                    for it in d['data'].get('list',[]):
                        if it['id'] not in seen:
                            seen.add(it['id'])
                            all_news.append(it)
            except: pass
    return all_news

# ═══ 1b. FETCH EAST MONEY NEWS ═══════════════════════════════
def fetch_eastmoney_news(pages=3, page_size=50):
    """Fetch news from East Money 7x24 live feed (kuaixun API)."""
    all_news, seen = [], set()
    # East Money 快讯 channels: 102=财经, 103=股票
    for col_id in ['102', '103', '132']:  # 132=国际市场
        for pg in range(1, pages+1):
            try:
                url = f'https://newsapi.eastmoney.com/kuaixun/v1/getlist_{col_id}_ajaxResult_{page_size}_{pg}_.html'
                r = requests.get(url, headers=EM, timeout=10)
                m = re.search(r'var ajaxResult=(\{.*\})', r.text, re.S)
                if not m: continue
                d = json.loads(m.group(1))
                for it in d.get('LivesList', []):
                    nid = str(it.get('newsid', '') or it.get('id', ''))
                    if not nid or nid in seen: continue
                    seen.add(nid)
                    # Parse showtime to Unix timestamp (Beijing time)
                    ctime_str = it.get('showtime', '')
                    try:
                        ct = datetime.strptime(ctime_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=BJT)
                        ctime = int(ct.timestamp())
                    except: ctime = int(time.time())
                    all_news.append({
                        'id': f'em_{nid}',
                        'title': it.get('title', ''),
                        'digest': it.get('digest', '') or it.get('simdigest', '') or '',
                        'url': it.get('url_w', '') or it.get('url_unique', ''),
                        'ctime': ctime,
                        'import': '2' if it.get('titlestyle') else '0',
                        'color': '',
                        'stock': [],
                        'tagInfo': [],
                        'tags': [],
                        'source': 'eastmoney',
                    })
            except: pass
    return all_news

# ═══ 1c. FETCH FUND DATA (天天基金) ═════════════════════════
FUND_TYPES = {
    '股票型': 'gp', '混合型': 'hh', '指数型': 'zs', '债券型': 'zq', 'QDII': 'qdii',
}

def fetch_fund_rankings(fund_type='', top_n=30):
    """Fetch fund rankings from 天天基金 (fund.eastmoney.com).
    fund_type: gp=股票型, hh=混合型, zs=指数型, zq=债券型, qdii=QDII, ''=全部"""
    funds = []
    try:
        ft_map = {'gp':'gp','hh':'hh','zs':'zs','zq':'zq','qdii':'qdii','':''}
        ft = ft_map.get(fund_type, fund_type)
        url = f'https://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft={ft}&rs=&gs=0&sc=rzdf&st=desc&qdii=&tabSubtype=,,,,,&pi=1&pn={top_n}&dx=1'
        headers = {**EM, 'Referer': 'https://fund.eastmoney.com/fundranking.html'}
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text
        m = re.search(r'datas:\[(.*?)\]', text, re.S)
        if m:
            items = m.group(1).split('","')
            for item in items:
                item = item.strip('"')
                fields = item.split(',')
                if len(fields) < 25: continue
                funds.append({
                    'code': fields[0],
                    'name': fields[1],
                    'nav': float(fields[4] or 0) if fields[4] else 0,
                    'acc_nav': float(fields[5] or 0) if fields[5] else 0,
                    'nav_date': fields[3],
                    'day_growth': float(fields[6] or 0) if fields[6] else 0,
                    'week_growth': float(fields[7] or 0) if fields[7] else 0,
                    'month_growth': float(fields[8] or 0) if fields[8] else 0,
                    'month3_growth': float(fields[9] or 0) if fields[9] else 0,
                    'month6_growth': float(fields[10] or 0) if fields[10] else 0,
                    'year_growth': float(fields[11] or 0) if fields[11] else 0,
                    'year2_growth': float(fields[12] or 0) if fields[12] else 0,
                    'year3_growth': float(fields[13] or 0) if fields[13] else 0,
                    'fund_type': fund_type or '全部',
                })
    except: pass
    return funds

def fetch_fund_estimate(fund_codes):
    """Fetch real-time estimated NAV for a list of fund codes.
    Returns {code: {name, estimate_nav, estimate_growth, estimate_time}}"""
    result = {}
    for code in fund_codes[:20]:
        try:
            url = f'https://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time()*1000)}'
            r = requests.get(url, headers={**EM, 'Referer': 'https://fund.eastmoney.com/'}, timeout=5)
            m = re.search(r'jsonpgz\((.*?)\)', r.text)
            if m:
                d = json.loads(m.group(1))
                result[code] = {
                    'name': d.get('name',''),
                    'code': code,
                    'estimate_nav': float(d.get('gsz',0)),
                    'estimate_growth': float(d.get('gszzl',0)),
                    'estimate_time': d.get('gztime',''),
                    'yesterday_nav': float(d.get('dwjz',0)),
                }
        except: pass
    return result

def fetch_all_fund_data():
    """Fetch comprehensive fund data: rankings for key types + estimates for top funds."""
    fund_data = {'rankings': {}, 'estimates': {}, 'summary': []}

    # Fetch rankings for key fund types
    for label, ftype in [('股票型','gp'), ('混合型','hh'), ('指数型','zs')]:
        funds = fetch_fund_rankings(fund_type=ftype, top_n=15)
        fund_data['rankings'][label] = funds

    # Collect top fund codes for estimate
    top_codes = []
    for label, funds in fund_data['rankings'].items():
        for f in funds[:5]:
            top_codes.append(f['code'])

    # Fetch real-time estimates
    if top_codes:
        fund_data['estimates'] = fetch_fund_estimate(top_codes)

    # Build summary: top performers across all types
    all_funds = []
    for label, funds in fund_data['rankings'].items():
        for f in funds:
            f['type_label'] = label
            all_funds.append(f)
    all_funds.sort(key=lambda x: -abs(x.get('day_growth', 0)))
    fund_data['summary'] = all_funds[:20]

    return fund_data

# ═══ 2. FETCH QUOTES ════════════════════════════════════════
def sym(code, market='A'):
    """Convert code to Tencent quote symbol. market: 'A', 'HK', 'US'"""
    if market == 'HK':
        c = code.replace('HK', '').replace('hk', '').lstrip('0') or '0'
        return f'hk{c.zfill(5)}'
    elif market == 'US':
        return f'us{code}'
    else:
        return f'sh{code}' if code.startswith('6') else f'sz{code}'

def detect_market(code):
    """Detect market from code format."""
    if re.match(r'^\d{6}$', code): return 'A'
    if code.upper().startswith('HK') or (re.match(r'^\d{4,5}$', code)): return 'HK'
    if re.match(r'^[A-Za-z]', code): return 'US'
    return 'A'

def fetch_quotes(codes):
    """Fetch quotes for A/HK/US stocks. Codes can be mixed markets."""
    if not codes: return {}
    # Separate by market
    a_codes = [c for c in codes if re.match(r'^\d{6}$', c)]
    hk_codes = [c for c in codes if c.upper().startswith('HK') or (re.match(r'^\d{4,5}$', c) and c not in a_codes and len(c) <= 5)]
    us_codes = [c for c in codes if re.match(r'^[A-Za-z]', c) and not c.upper().startswith('HK')]
    q = {}
    # A-shares
    for i in range(0, len(a_codes), 30):
        batch = [sym(c, 'A') for c in a_codes[i:i+30]]
        try:
            r = requests.get(f'https://qt.gtimg.cn/q={",".join(batch)}', headers=QT, timeout=10)
            for ln in r.text.strip().split('\n'):
                ln = ln.strip()
                if not ln or '=""' in ln: continue
                m = re.search(r'v_(\w+)="(.+)"', ln)
                if not m: continue
                f = m.group(2).split('~')
                if len(f) >= 46:
                    q[f[2]] = {
                        'name':f[1],'code':f[2],'market':'A',
                        'price':float(f[3] or 0),'prev_close':float(f[4] or 0),
                        'open':float(f[5] or 0),'volume':int(f[6] or 0),
                        'high':float(f[33] or 0),'low':float(f[34] or 0),
                        'change':float(f[31] or 0),'change_pct':float(f[32] or 0),
                        'amount':float(f[37] or 0),
                        'amplitude':float(f[43] or 0) if len(f)>43 else 0,
                        'currency':'CNY',
                    }
        except: pass
    # HK stocks
    for i in range(0, len(hk_codes), 30):
        batch = [sym(c, 'HK') for c in hk_codes[i:i+30]]
        try:
            r = requests.get(f'https://qt.gtimg.cn/q={",".join(batch)}', headers=QT, timeout=10)
            for ln in r.text.strip().split('\n'):
                ln = ln.strip()
                if not ln or '=""' in ln: continue
                m = re.search(r'v_(\w+)="(.+)"', ln)
                if not m: continue
                f = m.group(2).split('~')
                if len(f) >= 46:
                    raw_code = f[2]
                    store_key = f'HK{raw_code}' if not raw_code.startswith('HK') else raw_code
                    q[store_key] = {
                        'name':f[1],'code':store_key,'market':'HK',
                        'price':float(f[3] or 0),'prev_close':float(f[4] or 0),
                        'open':float(f[5] or 0),'volume':int(f[6] or 0),
                        'high':float(f[33] or 0),'low':float(f[34] or 0),
                        'change':float(f[31] or 0),'change_pct':float(f[32] or 0),
                        'amount':float(f[37] or 0),
                        'amplitude':float(f[43] or 0) if len(f)>43 else 0,
                        'currency':'HKD',
                    }
        except: pass
    # US stocks
    for i in range(0, len(us_codes), 20):
        batch = [sym(c, 'US') for c in us_codes[i:i+20]]
        try:
            r = requests.get(f'https://qt.gtimg.cn/q={",".join(batch)}', headers=QT, timeout=10)
            for ln in r.text.strip().split('\n'):
                ln = ln.strip()
                if not ln or '=""' in ln: continue
                m = re.search(r'v_(\w+)="(.+)"', ln)
                if not m: continue
                f = m.group(2).split('~')
                if len(f) >= 30:
                    q[f[2]] = {
                        'name':f[1],'code':f[2],'market':'US',
                        'price':float(f[3] or 0),'prev_close':float(f[4] or 0),
                        'open':float(f[5] or 0),'volume':int(f[6] or 0),
                        'high':float(f[33] or 0) if len(f)>33 else 0,
                        'low':float(f[34] or 0) if len(f)>34 else 0,
                        'change':float(f[31] or 0),'change_pct':float(f[32] or 0),
                        'amount':float(f[37] or 0) if len(f)>37 else 0,
                        'amplitude':float(f[43] or 0) if len(f)>43 else 0,
                        'currency':'USD',
                    }
        except: pass
    return q

# ═══ 3. FETCH DAILY KLINE (for consecutive up days) ════════
def fetch_kline(codes, days=10):
    """Returns {code: [{'date','close','change_pct'}, ...]} most recent N days.
    Supports A-share (6-digit) and US (ticker) codes. HK k-line not available on Tencent."""
    result = {}
    for code in codes:
        mkt = detect_market(code)
        if mkt == 'HK': continue  # Tencent has no HK k-line data
        try:
            s = sym(code, mkt)
            url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={s},day,,,{days},qfq'
            r = requests.get(url, headers=QT, timeout=8)
            d = r.json()
            # data -> {s} -> 'day' or 'qfqday'
            kdata = d.get('data',{}).get(s,{})
            rows = kdata.get('qfqday') or kdata.get('day') or []
            result[code] = []
            for row in rows:
                # row = [date, open, close, high, low, volume]
                if len(row) >= 3:
                    result[code].append({
                        'date': row[0],
                        'open': float(row[1]),
                        'close': float(row[2]),
                        'high': float(row[3]) if len(row)>3 else 0,
                        'low': float(row[4]) if len(row)>4 else 0,
                    })
        except: pass
    return result

def compute_consecutive_ups(kline_data):
    """From daily kline, compute current streak, historical max streak, and daily changes"""
    result = {}
    for code, rows in kline_data.items():
        if len(rows) < 2:
            result[code] = {'streak': 0, 'total_gain': 0, 'max_streak': 0, 'max_streak_gain': 0, 'daily': []}
            continue
        # Current streak (from latest going back)
        streak = 0
        total_gain = 0
        for i in range(len(rows)-1, 0, -1):
            if rows[i]['close'] > rows[i-1]['close']:
                streak += 1
                total_gain += (rows[i]['close'] - rows[i-1]['close']) / rows[i-1]['close'] * 100
            else:
                break
        # Historical max streak in the window
        max_streak = 0
        max_streak_gain = 0
        cur_s = 0
        cur_g = 0
        for i in range(1, len(rows)):
            if rows[i]['close'] > rows[i-1]['close']:
                cur_s += 1
                cur_g += (rows[i]['close'] - rows[i-1]['close']) / rows[i-1]['close'] * 100
                if cur_s > max_streak:
                    max_streak = cur_s
                    max_streak_gain = cur_g
            else:
                cur_s = 0
                cur_g = 0
        # Daily change list (recent 5)
        daily = []
        for i in range(max(1, len(rows)-5), len(rows)):
            chg = (rows[i]['close'] - rows[i-1]['close']) / rows[i-1]['close'] * 100
            daily.append({'date': rows[i]['date'], 'pct': round(chg, 2)})
        result[code] = {
            'streak': streak, 'total_gain': round(total_gain, 2),
            'max_streak': max_streak, 'max_streak_gain': round(max_streak_gain, 2),
            'daily': daily,
        }
    return result

# ═══ 4. ANALYZE NEWS ════════════════════════════════════════
def analyze_all(news_list):
    stock_scores = defaultdict(lambda: {'score':0,'mentions':0,'news':[],'name':'','code':'','reasons':set()})
    all_analyzed = []
    all_codes = set()

    for item in news_list:
        text = item.get('title','') + item.get('digest','')
        ctime = int(item.get('ctime',0))
        ts = datetime.fromtimestamp(ctime, tz=BJT) if ctime else None
        time_str = ts.strftime('%H:%M') if ts else ''
        date_str = ts.strftime('%m-%d') if ts else ''

        # Sentiment
        bull = sum(1 for kw in BULL_KW if kw in text)
        bear = sum(1 for kw in BEAR_KW if kw in text)
        imp = int(item.get('import','0'))
        if imp >= 3: bull += 1.5
        if item.get('color') == '2': bull += 0.5
        if bull > bear:
            sentiment, impact = '利好', bull - bear + imp*0.5
        elif bear > bull:
            sentiment, impact = '利空', bear - bull + imp*0.5
        else:
            sentiment, impact = '中性', imp*0.3

        # Stocks — extract from all markets
        stocks = []
        news_market = 'A'  # default market for this news item
        for s in item.get('stock',[]):
            c, mkt, n = s.get('stockCode',''), s.get('stockMarket',''), s.get('name','')
            if not c: continue
            mkt_label = MARKET_MAP.get(mkt, '')
            if not mkt_label: continue
            if mkt_label == 'A' and not re.match(r'^\d{6}$', c): continue
            if mkt_label == 'HK':
                c = c if c.startswith('HK') else f'HK{c}'
                news_market = 'HK'
            elif mkt_label == 'US':
                news_market = 'US'
            stocks.append({'code':c,'name':n,'market':mkt_label})
            all_codes.add(c)
        # If no stock extracted, detect market from keywords
        if not stocks:
            if any(kw in text for kw in ['港股','恒生','恒指','港交所']): news_market = 'HK'
            elif any(kw in text for kw in ['美股','纳指','标普','道琼斯','华尔街']): news_market = 'US'

        # Sectors + ETFs (pick sector map based on market)
        sectors = [t['name'] for t in item.get('tagInfo',[]) if t.get('type')=='0']
        etfs = {}
        sector_map = SECTOR_ETF_HK if news_market=='HK' else SECTOR_ETF_US if news_market=='US' else SECTOR_ETF
        for sec in sectors:
            for k, v in sector_map.items():
                if k in sec and v.get('etf'): etfs[v['etf']] = {'code':v['etf'],'name':v['name'],'desc':v.get('desc','')}
        for k, v in sector_map.items():
            if k in text and v.get('etf'): etfs[v['etf']] = {'code':v['etf'],'name':v['name'],'desc':v.get('desc','')}

        # Score for hot7
        if sentiment == '利好':
            pb = sum(v for k,v in POLICY_KW.items() if k in text)
            hb = sum(v for k,v in HOT_KW.items() if k in text)
            total = impact + pb + hb
            reasons = set()
            if pb > 0: reasons.add('政策利好')
            if hb > 0: reasons.add('热点概念')
            if bull >= 2: reasons.add('多重利好')
            if imp >= 3: reasons.add('重大事件')
            if not reasons: reasons.add('利好资讯')
            for sc in stocks:
                e = stock_scores[sc['code']]
                e['score'] += total; e['mentions'] += 1
                e['name'] = sc['name']; e['code'] = sc['code']
                e['market'] = sc.get('market', news_market)
                e['news'].append(item.get('title','')); e['reasons'].update(reasons)

        analyzed = {
            'title': item.get('title',''), 'digest': item.get('digest',''),
            'sentiment': sentiment, 'impact': round(impact,1),
            'time': time_str, 'date': date_str, 'url': item.get('url',''),
            'stocks': stocks, 'sectors': sectors,
            'etfs': list(etfs.values()),
            'tags': [t.get('name','') for t in item.get('tags',[])],
            'market': news_market,
            'ctime': ctime,
        }
        all_analyzed.append(analyzed)

    hot7 = sorted(stock_scores.values(), key=lambda x: (-x['score'],-x['mentions']))[:7]

    # Split: night news (22:00 - 08:30) vs realtime
    now = beijing_now()
    night_start = now.replace(hour=22, minute=0, second=0, microsecond=0) - timedelta(days=1)
    night_end = now.replace(hour=8, minute=30, second=0, microsecond=0)
    night_news = []
    realtime_news = []
    for n in all_analyzed:
        ts = datetime.fromtimestamp(n['ctime'], tz=BJT) if n['ctime'] else None
        if ts and night_start <= ts <= night_end:
            night_news.append(n)
        else:
            realtime_news.append(n)
    night_news.sort(key=lambda x: (-x['impact'], -x['ctime']))
    realtime_news.sort(key=lambda x: -x['ctime'])

    # Sector aggregation — collect catalysts (news headlines) per sector
    sec_agg = defaultdict(lambda: {'count':0,'bull':0,'bear':0,'stocks':set(),'catalysts_bull':[],'catalysts_bear':[]})
    for n in all_analyzed:
        for sec in n['sectors']:
            for k, v in SECTOR_ETF.items():
                if k in sec:
                    e = sec_agg[k]
                    e['count'] += 1
                    if n['sentiment']=='利好':
                        e['bull']+=1
                        if len(e['catalysts_bull']) < 3:
                            e['catalysts_bull'].append(n['title'][:60])
                    elif n['sentiment']=='利空':
                        e['bear']+=1
                        if len(e['catalysts_bear']) < 3:
                            e['catalysts_bear'].append(n['title'][:60])
                    for sc in n['stocks']: e['stocks'].add(f"{sc['name']}|{sc['code']}")
                    break

    sector_summary = []
    seen_etf = set()
    for k in sorted(sec_agg, key=lambda x: -sec_agg[x]['count']):
        v = sec_agg[k]
        ei = SECTOR_ETF.get(k,{})
        etf_code = ei.get('etf','')
        if etf_code in seen_etf: continue
        seen_etf.add(etf_code)
        stock_list = [{'name':s.split('|')[0],'code':s.split('|')[1]} for s in list(v['stocks'])[:5]]
        # Build reason text
        if v['bull'] > v['bear']:
            direction = '偏多'
            reason = f"利好{v['bull']}条 > 利空{v['bear']}条"
        elif v['bear'] > v['bull']:
            direction = '偏空'
            reason = f"利空{v['bear']}条 > 利好{v['bull']}条"
        else:
            direction = '中性'
            reason = f"利好{v['bull']} = 利空{v['bear']}"
        sector_summary.append({
            'sector': k, 'etf_code': etf_code, 'etf_name': ei.get('name',''),
            'desc': ei.get('desc',''), 'count': v['count'],
            'bull': v['bull'], 'bear': v['bear'],
            'stocks': stock_list,
            'direction': direction, 'reason': reason,
            'catalysts_bull': v['catalysts_bull'],
            'catalysts_bear': v['catalysts_bear'],
        })

    return hot7, realtime_news, night_news, all_analyzed, all_codes, sector_summary

# ═══ 5. BUILD REALTIME STOCK PICKS ═════════════════════════
def build_realtime_picks(realtime_news, quotes, klines, streaks):
    """For bullish realtime news, pick the best stock per news item.
    Sort by combined weight of news impact and time recency.
    Tag high-impact picks."""
    picks = []
    seen_codes = set()
    now_ts = time.time()
    for n in realtime_news:
        if n['sentiment'] != '利好' or not n['stocks']:
            continue
        best = None
        best_score = -999
        for sc in n['stocks']:
            q = quotes.get(sc['code'],{})
            if not q or q.get('price',0) <= 0: continue
            s = streaks.get(sc['code'],{})
            pct = q.get('change_pct',0)
            amp = q.get('amplitude',0)
            streak = s.get('streak',0)
            elasticity = abs(pct) + amp*0.3 + streak*1.5
            if pct > 0: elasticity += pct
            if elasticity > best_score:
                best_score = elasticity
                best = {
                    'code': sc['code'], 'name': sc['name'],
                    'price': q['price'], 'change_pct': q['change_pct'],
                    'change': q['change'],
                    'high': q['high'], 'low': q['low'],
                    'amount': q['amount'], 'amplitude': amp,
                    'streak': streak, 'total_gain': s.get('total_gain',0),
                    'max_streak': s.get('max_streak',0),
                    'max_streak_gain': s.get('max_streak_gain',0),
                    'daily': s.get('daily',[]),
                    'elasticity': round(elasticity, 2),
                    'news_title': n['title'], 'news_url': n['url'],
                    'news_time': n['time'], 'news_date': n['date'],
                    'news_digest': n['digest'][:120],
                    'news_impact': n['impact'],
                    'news_ctime': n['ctime'],
                }
        if best and best['code'] not in seen_codes:
            # Combined sort weight: impact * recency_factor * elasticity
            age_hours = max(0.5, (now_ts - best['news_ctime']) / 3600) if best['news_ctime'] else 24
            recency = max(0.2, 1.0 / (1 + age_hours * 0.15))  # decay: newer = higher
            best['combined_score'] = round(best['news_impact'] * recency * (1 + best['elasticity'] * 0.1), 2)
            # Impact level
            if best['news_impact'] >= 4:
                best['level'] = 'S'
            elif best['news_impact'] >= 2.5:
                best['level'] = 'A'
            elif best['news_impact'] >= 1.5:
                best['level'] = 'B'
            else:
                best['level'] = 'C'
            picks.append(best)
            seen_codes.add(best['code'])
    picks.sort(key=lambda x: -x['combined_score'])
    return picks[:20]

# ═══ 6. GENERATE HTML ══════════════════════════════════════
def generate_html(hot7, realtime_news, night_news, all_news, quotes, sector_summary, realtime_picks, streaks=None, run_elapsed=0, run_api_calls=0, fund_data=None):
    now = beijing_now().strftime('%Y-%m-%d %H:%M:%S')
    bull_c = sum(1 for n in all_news if n['sentiment']=='利好')
    bear_c = sum(1 for n in all_news if n['sentiment']=='利空')
    neut_c = sum(1 for n in all_news if n['sentiment']=='中性')

    # Enrich hot7
    if streaks is None:
        streaks = {}
    hot7e = []
    for s in hot7:
        q = quotes.get(s['code'],{})
        st = streaks.get(s['code'],{})
        hot7e.append({
            **s, 'price':q.get('price',0), 'change_pct':q.get('change_pct',0),
            'change':q.get('change',0), 'high':q.get('high',0), 'low':q.get('low',0),
            'amount':q.get('amount',0), 'streak':st.get('streak',0),
            'total_gain':st.get('total_gain',0),
            'reasons':list(s['reasons']), 'news':s['news'][:5],
        })

    # Enrich sector_summary with ETF quotes
    for sec in sector_summary:
        q = quotes.get(sec['etf_code'],{})
        sec['etf_price'] = q.get('price',0)
        sec['etf_change_pct'] = q.get('change_pct',0)
        # Enrich related stocks with quotes
        for sc in sec['stocks']:
            sq = quotes.get(sc['code'],{})
            sc['price'] = sq.get('price',0)
            sc['change_pct'] = sq.get('change_pct',0)

    def j(o): return json.dumps(o, ensure_ascii=False, default=str)

    # Split data by market for frontend tabs
    def by_market(items, mkt):
        return [n for n in items if n.get('market', 'A') == mkt]
    hot7_by_mkt = {}
    for mkt in ['A', 'HK', 'US']:
        mkt_scores = [s for s in hot7 if s.get('market', 'A') == mkt]
        mkt_hot7e = []
        for s in mkt_scores:
            q = quotes.get(s['code'],{})
            st = streaks.get(s['code'],{})
            mkt_hot7e.append({
                **s, 'price':q.get('price',0), 'change_pct':q.get('change_pct',0),
                'change':q.get('change',0), 'high':q.get('high',0), 'low':q.get('low',0),
                'amount':q.get('amount',0), 'streak':st.get('streak',0),
                'total_gain':st.get('total_gain',0),
                'reasons':list(s['reasons']), 'news':s['news'][:5],
            })
        hot7_by_mkt[mkt] = mkt_hot7e

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html'),'r',encoding='utf-8') as f:
        html = f.read()

    reps = {
        '__TIMESTAMP__': now,
        '__HOT7_JSON__': j(hot7e),
        '__HOT7_A_JSON__': j(hot7_by_mkt.get('A', [])),
        '__HOT7_HK_JSON__': j(hot7_by_mkt.get('HK', [])),
        '__HOT7_US_JSON__': j(hot7_by_mkt.get('US', [])),
        '__PICKS_JSON__': j(realtime_picks),
        '__PICKS_A_JSON__': j([p for p in realtime_picks if detect_market(p.get('code','')) == 'A']),
        '__PICKS_HK_JSON__': j([p for p in realtime_picks if detect_market(p.get('code','')) == 'HK']),
        '__PICKS_US_JSON__': j([p for p in realtime_picks if detect_market(p.get('code','')) == 'US']),
        '__REALTIME_NEWS_JSON__': j(realtime_news[:80]),
        '__NIGHT_NEWS_JSON__': j(night_news[:80]),
        '__ALL_NEWS_JSON__': j(all_news[:150]),
        '__ALL_A_JSON__': j(by_market(all_news, 'A')[:80]),
        '__ALL_HK_JSON__': j(by_market(all_news, 'HK')[:60]),
        '__ALL_US_JSON__': j(by_market(all_news, 'US')[:60]),
        '__BULL_NEWS_JSON__': j([n for n in all_news if n['sentiment']=='利好'][:60]),
        '__BEAR_NEWS_JSON__': j([n for n in all_news if n['sentiment']=='利空'][:60]),
        '__NEUT_NEWS_JSON__': j([n for n in all_news if n['sentiment']=='中性'][:40]),
        '__QUOTES_JSON__': j(quotes),
        '__SECTORS_JSON__': j(sector_summary[:20]),
        '__STATS_TOTAL__': str(len(all_news)),
        '__STATS_BULL__': str(bull_c),
        '__STATS_BEAR__': str(bear_c),
        '__STATS_NEUT__': str(neut_c),
        '__STATS_NIGHT__': str(len(night_news)),
        '__STATS_RT__': str(len(realtime_news)),
        '__RUN_ELAPSED__': f'{run_elapsed:.1f}',
        '__RUN_API_CALLS__': str(run_api_calls),
        '__FUND_DATA_JSON__': j(fund_data or {}),
    }
    for k, v in reps.items():
        html = html.replace(k, v)
    return html

# ═══ 7. TELEGRAM PUSH ═════════════════════════════════════
def build_tg_message(hot7e, rt_picks, quotes):
    """Build Telegram message with Hot7 + realtime picks"""
    now = beijing_now().strftime('%Y-%m-%d %H:%M')
    lines = [f'📊 <b>A股利好监控 {now}</b>', '']

    # Hot 7
    lines.append('🔥 <b>今日热点股 TOP 7</b>')
    lines.append('━━━━━━━━━━━━━━━')
    for i, s in enumerate(hot7e):
        q = quotes.get(s['code'], {})
        price = q.get('price', 0)
        pct = q.get('change_pct', 0)
        arrow = '📈' if pct > 0 else '📉' if pct < 0 else '➖'
        pct_str = f'+{pct:.2f}%' if pct > 0 else f'{pct:.2f}%'
        reasons_str = ' '.join(s.get('reasons', []))
        lines.append(f'<b>#{i+1} {s["name"]}</b> ({s["code"]})')
        lines.append(f'  {arrow} {price:.2f} {pct_str} | 评分{s["score"]:.1f}')
        if reasons_str:
            lines.append(f'  💡 {reasons_str}')
        # Show top 2 news with links
        for n_title in s.get('news', [])[:2]:
            lines.append(f'  · {n_title[:50]}')
        lines.append('')

    # Realtime Picks (top 10)
    lines.append('⚡ <b>实时利好精选</b>')
    lines.append('━━━━━━━━━━━━━━━')
    for p in rt_picks[:10]:
        lvl = p.get('level', 'C')
        lvl_icon = {'S': '🔴', 'A': '🟠', 'B': '🟡', 'C': '⚪'}.get(lvl, '⚪')
        pct = p['change_pct']
        arrow = '📈' if pct > 0 else '📉' if pct < 0 else '➖'
        pct_str = f'+{pct:.2f}%' if pct > 0 else f'{pct:.2f}%'
        streak_str = f' | {p["streak"]}连涨🔥' if p.get('streak', 0) >= 2 else ''
        lines.append(f'{lvl_icon}<b>[{lvl}] {p["name"]}</b> ({p["code"]})')
        lines.append(f'  {arrow} {p["price"]:.2f} {pct_str} 综合分{p["combined_score"]:.1f}{streak_str}')
        lines.append(f'  📰 {p["news_title"][:60]}')
        if p.get('news_url'):
            lines.append(f'  🔗 <a href="{p["news_url"]}">查看原文</a>')
        lines.append('')

    lines.append('─────────────────')
    lines.append(f'⏰ 数据来源: 同花顺7x24 | 腾讯行情')
    return '\n'.join(lines)

def send_telegram(token, chat_id, message):
    """Send message via Telegram Bot API. chat_id can be a single ID or list of IDs."""
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    # Support multiple chat targets
    targets = chat_id if isinstance(chat_id, list) else [chat_id]

    # Split long messages (Telegram limit 4096 chars)
    chunks = []
    if len(message) <= 4096:
        chunks = [message]
    else:
        lines = message.split('\n')
        chunk = ''
        for line in lines:
            if len(chunk) + len(line) + 1 > 4000:
                chunks.append(chunk)
                chunk = line
            else:
                chunk += ('\n' if chunk else '') + line
        if chunk:
            chunks.append(chunk)

    for target in targets:
        for i, chunk in enumerate(chunks):
            payload = {
                'chat_id': target,
                'text': chunk,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            }
            try:
                r = requests.post(url, json=payload, timeout=15)
                result = r.json()
                if result.get('ok'):
                    print(f"      Telegram 推送成功 → {target} ({i+1}/{len(chunks)})")
                else:
                    print(f"      Telegram 推送失败 → {target}: {result.get('description','未知错误')}")
            except Exception as e:
                print(f"      Telegram 推送异常 → {target}: {e}")

# ═══ 8. REALTIME ALERT (single news push) ═════════════════
def build_alert_message(news_item, stocks_info):
    """Build a single alert message for an important bullish news item."""
    title = news_item['title']
    url = news_item.get('url', '')
    impact = news_item['impact']
    t = news_item.get('time', '')
    d = news_item.get('date', '')

    # Level
    if impact >= 4: lvl, icon = 'S', '🔴'
    elif impact >= 2.5: lvl, icon = 'A', '🟠'
    elif impact >= 1.5: lvl, icon = 'B', '🟡'
    else: lvl, icon = 'C', '⚪'

    lines = [f'{icon} <b>[{lvl}级利好]</b> {d} {t}', '']
    lines.append(f'📰 <b>{title}</b>')
    if url:
        lines.append(f'🔗 <a href="{url}">查看原文</a>')
    lines.append('')

    # Related stocks with live quotes
    if stocks_info:
        lines.append('📊 <b>关联个股实时行情:</b>')
        for si in stocks_info[:6]:
            pct = si.get('change_pct', 0)
            arr = '📈' if pct > 0 else '📉' if pct < 0 else '➖'
            pct_s = f'+{pct:.2f}%' if pct > 0 else f'{pct:.2f}%'
            streak = si.get('streak', 0)
            sk = f' | {streak}连涨🔥' if streak >= 2 else ''
            lines.append(f'  {arr} <b>{si["name"]}</b> ({si["code"]}) {si.get("price",0):.2f} {pct_s}{sk}')
        lines.append('')

    # Sectors / ETFs
    secs = news_item.get('sectors', [])
    etfs = news_item.get('etfs', [])
    if secs:
        lines.append(f'🏷 板块: {", ".join(secs[:5])}')
    if etfs:
        etf_strs = [f'{e["name"]}({e["code"]})' for e in etfs[:3]]
        lines.append(f'💰 ETF: {", ".join(etf_strs)}')

    return '\n'.join(lines)

# ═══ 9. WATCH MODE (realtime monitoring loop) ═════════════
def run_watch(tg_token, tg_chat, interval=120, min_impact=1.5):
    """Continuously monitor for new important bullish news and push alerts."""
    seen_ids = set()
    print(f"🔍 实时监控模式启动 (间隔{interval}秒, 最低影响分={min_impact})")
    print(f"   推送到 Telegram Chat: {tg_chat}")
    print(f"   Ctrl+C 退出")
    print()

    # First run: load existing IDs without pushing (avoid flooding)
    print("  初始化: 加载已有新闻...")
    try:
        init_news = fetch_news(pages=2, page_size=40)
        for item in init_news:
            seen_ids.add(item['id'])
        print(f"  已记录 {len(seen_ids)} 条历史新闻ID, 后续仅推送新增")
    except Exception as e:
        print(f"  初始化异常: {e}")
    print()

    cycle = 0
    while True:
        cycle += 1
        now_str = beijing_now().strftime('%H:%M:%S')
        try:
            # Fetch latest news (fewer pages for speed)
            news = fetch_news(pages=2, page_size=30)
            new_items = [it for it in news if it['id'] not in seen_ids]

            if not new_items:
                print(f"[{now_str}] #{cycle} 无新增新闻")
                time.sleep(interval)
                continue

            # Mark as seen immediately
            for it in new_items:
                seen_ids.add(it['id'])

            # Analyze new items
            new_analyzed = []
            new_codes = set()
            for item in new_items:
                text = item.get('title', '') + item.get('digest', '')
                ctime = int(item.get('ctime', 0))
                ts = datetime.fromtimestamp(ctime, tz=BJT) if ctime else None
                time_str = ts.strftime('%H:%M') if ts else ''
                date_str = ts.strftime('%m-%d') if ts else ''

                bull = sum(1 for kw in BULL_KW if kw in text)
                bear = sum(1 for kw in BEAR_KW if kw in text)
                imp = int(item.get('import', '0'))
                if imp >= 3: bull += 1.5
                if item.get('color') == '2': bull += 0.5
                if bull > bear:
                    sentiment, impact = '利好', bull - bear + imp * 0.5
                elif bear > bull:
                    sentiment, impact = '利空', bear - bull + imp * 0.5
                else:
                    sentiment, impact = '中性', imp * 0.3

                stocks = []
                for s in item.get('stock', []):
                    c, mkt, n = s.get('stockCode', ''), s.get('stockMarket', ''), s.get('name', '')
                    if not c or not re.match(r'^\d{6}$', c): continue
                    if mkt not in ('22', '33', '151', '17'): continue
                    stocks.append({'code': c, 'name': n})
                    new_codes.add(c)

                sectors = [t['name'] for t in item.get('tagInfo', []) if t.get('type') == '0']
                etfs = {}
                for sec in sectors:
                    for k, v in SECTOR_ETF.items():
                        if k in sec and v.get('etf'): etfs[v['etf']] = {'code': v['etf'], 'name': v['name']}
                for k, v in SECTOR_ETF.items():
                    if k in text and v.get('etf'): etfs[v['etf']] = {'code': v['etf'], 'name': v['name']}

                new_analyzed.append({
                    'title': item.get('title', ''), 'sentiment': sentiment,
                    'impact': round(impact, 1), 'time': time_str, 'date': date_str,
                    'url': item.get('url', ''), 'stocks': stocks,
                    'sectors': sectors, 'etfs': list(etfs.values()),
                })

            # Filter: only important bullish news
            alerts = [n for n in new_analyzed if n['sentiment'] == '利好' and n['impact'] >= min_impact]

            bull_count = sum(1 for n in new_analyzed if n['sentiment'] == '利好')
            print(f"[{now_str}] #{cycle} 新增{len(new_items)}条 (利好{bull_count}) → {len(alerts)}条达标推送")

            if alerts and new_codes:
                # Fetch live quotes for related stocks
                quotes = fetch_quotes(list(new_codes))

                for alert in alerts:
                    # Enrich stocks with quotes
                    stocks_info = []
                    for sc in alert['stocks']:
                        q = quotes.get(sc['code'], {})
                        if q and q.get('price', 0) > 0:
                            stocks_info.append({
                                'name': sc['name'], 'code': sc['code'],
                                'price': q['price'], 'change_pct': q['change_pct'],
                            })
                    msg = build_alert_message(alert, stocks_info)
                    send_telegram(tg_token, tg_chat, msg)
                    time.sleep(1)  # rate limit

        except KeyboardInterrupt:
            print("\n⏹ 监控已停止")
            break
        except Exception as e:
            print(f"[{now_str}] #{cycle} 异常: {e}")

        time.sleep(interval)

# ═══ 10. FULL SUMMARY FETCH & SEND ════════════════════════
def do_full_summary(tg_token, tg_chat):
    """Fetch all data and send a full summary (Hot7 + realtime picks) to Telegram."""
    print(f"  [汇总] 抓取新闻...")
    news = fetch_news(pages=4, page_size=40)
    print(f"  [汇总] {len(news)}条 → 分析中...")
    hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)

    etf_codes = set()
    for s in sec_sum:
        if s['etf_code']: etf_codes.add(s['etf_code'])

    print(f"  [汇总] 获取行情...")
    quotes = fetch_quotes(list(all_codes) + list(etf_codes))

    kline_codes = set(s['code'] for s in hot7)
    for n in rt_news:
        if n['sentiment'] == '利好':
            for sc in n['stocks']: kline_codes.add(sc['code'])
    kline_codes = [c for c in kline_codes if c in quotes and quotes[c].get('price', 0) > 0]

    klines = fetch_kline(kline_codes[:50], days=10)
    streaks = compute_consecutive_ups(klines)
    rt_picks = build_realtime_picks(rt_news, quotes, klines, streaks)

    hot7e_msg = []
    for s in hot7:
        hot7e_msg.append({**s, 'reasons': list(s['reasons']), 'news': s['news'][:3]})

    msg = build_tg_message(hot7e_msg, rt_picks, quotes)
    send_telegram(tg_token, tg_chat, msg)
    print(f"  [汇总] 推送完成 (Hot7 + {len(rt_picks)}只精选)")

# ═══ 11. BOT MODE (command listener + scheduled push) ═════
def is_market_hours():
    """Check if current time is within A-share market hours (9:15-15:00 weekdays)."""
    now = beijing_now()
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    t = now.hour * 60 + now.minute  # minutes since midnight
    return 9 * 60 + 15 <= t <= 15 * 60  # 9:15 - 15:00

def get_telegram_updates(token, offset=None, timeout=5):
    """Poll Telegram getUpdates API for new messages."""
    url = f'https://api.telegram.org/bot{token}/getUpdates'
    params = {'timeout': timeout}
    if offset is not None:
        params['offset'] = offset
    try:
        r = requests.get(url, params=params, timeout=timeout + 10)
        data = r.json()
        if data.get('ok'):
            return data.get('result', [])
    except Exception as e:
        print(f"  getUpdates异常: {e}")
    return []

def run_bot(tg_token, tg_chat, interval=120, min_impact=1.5):
    """Bot mode: listen for '发送' command + auto-push every 15min during market hours + alert new bullish news.
    tg_chat can be a single chat_id string or a list of targets (private + channel)."""
    # Normalize targets
    targets = tg_chat if isinstance(tg_chat, list) else [tg_chat]
    # Private chat ID for command listening (first numeric ID in targets)
    private_id = next((t for t in targets if t.lstrip('-').isdigit()), targets[0])
    seen_ids = set()
    update_offset = None
    last_scheduled_push = 0  # timestamp of last scheduled push
    schedule_interval = 15 * 60  # 15 minutes in seconds

    print(f"🤖 Bot模式启动")
    print(f"   功能1: 发送'发送'到Bot → 立即推送最新汇总")
    print(f"   功能2: 盘中9:15-15:00 每15分钟自动推送汇总")
    print(f"   功能3: 新重大利好实时推送 (间隔{interval}秒, 阈值{min_impact})")
    print(f"   推送目标: {', '.join(targets)}")
    print(f"   命令监听: 私聊 {private_id}")
    print(f"   Ctrl+C 退出")
    print()

    # Initialize: load existing news IDs
    print("  初始化: 加载已有新闻...")
    try:
        init_news = fetch_news(pages=2, page_size=40)
        for item in init_news:
            seen_ids.add(item['id'])
        print(f"  已记录 {len(seen_ids)} 条历史新闻ID")
    except Exception as e:
        print(f"  初始化异常: {e}")

    # Consume existing Telegram updates to avoid replaying old commands
    print("  初始化: 清除旧Telegram消息...")
    old_updates = get_telegram_updates(tg_token, timeout=1)
    if old_updates:
        update_offset = old_updates[-1]['update_id'] + 1
        print(f"  跳过 {len(old_updates)} 条旧消息")
    print()

    cycle = 0
    last_alert_check = 0

    while True:
        try:
            now = beijing_now()
            now_str = now.strftime('%H:%M:%S')
            now_ts = time.time()

            # ── Check Telegram for '发送' command ──
            updates = get_telegram_updates(tg_token, offset=update_offset, timeout=3)
            for upd in updates:
                update_offset = upd['update_id'] + 1
                msg = upd.get('message', {})
                chat_id = str(msg.get('chat', {}).get('id', ''))
                text = msg.get('text', '').strip()
                if chat_id == private_id and text in ('发送', '推送', '查看', '/send', '/发送', '/推送', '/start'):
                    print(f"[{now_str}] 📩 收到'发送'指令 → 执行汇总推送")
                    try:
                        do_full_summary(tg_token, targets)
                        last_scheduled_push = now_ts  # reset timer to avoid double push
                    except Exception as e:
                        print(f"  汇总推送异常: {e}")
                        send_telegram(tg_token, targets, f'⚠️ 汇总推送失败: {e}')

            # ── Scheduled push every 15 min during market hours ──
            if is_market_hours() and (now_ts - last_scheduled_push) >= schedule_interval:
                print(f"[{now_str}] ⏰ 定时汇总推送 (盘中每15分钟)")
                try:
                    do_full_summary(tg_token, targets)
                    last_scheduled_push = now_ts
                except Exception as e:
                    print(f"  定时推送异常: {e}")

            # ── Check for new bullish news (alert logic, every `interval` seconds) ──
            if (now_ts - last_alert_check) >= interval:
                last_alert_check = now_ts
                cycle += 1

                news = fetch_news(pages=2, page_size=30)
                new_items = [it for it in news if it['id'] not in seen_ids]

                if new_items:
                    for it in new_items:
                        seen_ids.add(it['id'])

                    new_analyzed = []
                    new_codes = set()
                    for item in new_items:
                        text_content = item.get('title', '') + item.get('digest', '')
                        ctime = int(item.get('ctime', 0))
                        ts = datetime.fromtimestamp(ctime, tz=BJT) if ctime else None
                        time_str = ts.strftime('%H:%M') if ts else ''
                        date_str = ts.strftime('%m-%d') if ts else ''

                        bull = sum(1 for kw in BULL_KW if kw in text_content)
                        bear = sum(1 for kw in BEAR_KW if kw in text_content)
                        imp = int(item.get('import', '0'))
                        if imp >= 3: bull += 1.5
                        if item.get('color') == '2': bull += 0.5
                        if bull > bear:
                            sentiment, impact = '利好', bull - bear + imp * 0.5
                        elif bear > bull:
                            sentiment, impact = '利空', bear - bull + imp * 0.5
                        else:
                            sentiment, impact = '中性', imp * 0.3

                        stocks = []
                        for s in item.get('stock', []):
                            c, mkt, n = s.get('stockCode', ''), s.get('stockMarket', ''), s.get('name', '')
                            if not c or not re.match(r'^\d{6}$', c): continue
                            if mkt not in ('22', '33', '151', '17'): continue
                            stocks.append({'code': c, 'name': n})
                            new_codes.add(c)

                        sectors = [t['name'] for t in item.get('tagInfo', []) if t.get('type') == '0']
                        etfs = {}
                        for sec in sectors:
                            for k, v in SECTOR_ETF.items():
                                if k in sec and v.get('etf'): etfs[v['etf']] = {'code': v['etf'], 'name': v['name']}
                        for k, v in SECTOR_ETF.items():
                            if k in text_content and v.get('etf'): etfs[v['etf']] = {'code': v['etf'], 'name': v['name']}

                        new_analyzed.append({
                            'title': item.get('title', ''), 'sentiment': sentiment,
                            'impact': round(impact, 1), 'time': time_str, 'date': date_str,
                            'url': item.get('url', ''), 'stocks': stocks,
                            'sectors': sectors, 'etfs': list(etfs.values()),
                        })

                    alerts = [n for n in new_analyzed if n['sentiment'] == '利好' and n['impact'] >= min_impact]
                    bull_count = sum(1 for n in new_analyzed if n['sentiment'] == '利好')
                    print(f"[{now_str}] #{cycle} 新增{len(new_items)}条 (利好{bull_count}) → {len(alerts)}条达标推送")

                    if alerts and new_codes:
                        alert_quotes = fetch_quotes(list(new_codes))
                        for alert in alerts:
                            stocks_info = []
                            for sc in alert['stocks']:
                                q = alert_quotes.get(sc['code'], {})
                                if q and q.get('price', 0) > 0:
                                    stocks_info.append({
                                        'name': sc['name'], 'code': sc['code'],
                                        'price': q['price'], 'change_pct': q['change_pct'],
                                    })
                            alert_msg = build_alert_message(alert, stocks_info)
                            send_telegram(tg_token, targets, alert_msg)
                            time.sleep(1)
                else:
                    print(f"[{now_str}] #{cycle} 无新增新闻")

            # Short sleep for responsive command listening
            time.sleep(5)

        except KeyboardInterrupt:
            print("\n⏹ Bot已停止")
            break
        except Exception as e:
            print(f"[{now_str}] 循环异常: {e}")
            time.sleep(10)

# ═══ 12. DAEMON MODE (auto-refresh dashboard) ════════════════
def generate_dashboard_once():
    """Run full pipeline once and write HTML to output."""
    _run_start = time.time()
    _api_calls = 0
    print(f"[{beijing_now().strftime('%H:%M:%S')}] 开始刷新面板...", flush=True)

    print("  [1/7] 获取同花顺资讯...", flush=True)
    news = fetch_news(pages=4, page_size=40)
    _api_calls += 12
    print(f"        同花顺 {len(news)} 条", flush=True)

    print("  [2/7] 获取东方财富快讯...", flush=True)
    em_news = fetch_eastmoney_news(pages=3, page_size=50)
    _api_calls += 4
    # Merge & dedup by title similarity
    seen_titles = set(n.get('title','')[:20] for n in news)
    for en in em_news:
        if en['title'][:20] not in seen_titles:
            news.append(en)
            seen_titles.add(en['title'][:20])
    print(f"        东方财富 {len(em_news)} 条, 合并后 {len(news)} 条", flush=True)

    print("  [3/7] 分析情绪 / 提取热点...", flush=True)
    hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)
    bull_c = sum(1 for n in all_news if n['sentiment']=='利好')
    bear_c = sum(1 for n in all_news if n['sentiment']=='利空')
    print(f"        利好{bull_c} / 利空{bear_c} / 中性{len(all_news)-bull_c-bear_c}", flush=True)

    etf_codes = set()
    for s in sec_sum:
        if s['etf_code']: etf_codes.add(s['etf_code'])

    print(f"  [4/7] 获取行情 ({len(all_codes)}股 + {len(etf_codes)}ETF)...", flush=True)
    quotes = fetch_quotes(list(all_codes) + list(etf_codes))
    _api_calls += max(1, (len(all_codes) + len(etf_codes) + 29) // 30)

    kline_codes = set(s['code'] for s in hot7)
    for n in rt_news:
        if n['sentiment'] == '利好':
            for sc in n['stocks']: kline_codes.add(sc['code'])
    kline_codes = [c for c in kline_codes if c in quotes and quotes[c].get('price',0) > 0]

    print(f"  [5/7] 获取日K ({len(kline_codes)}只)...", flush=True)
    klines = fetch_kline(kline_codes[:50], days=10)
    _api_calls += min(len(kline_codes), 50)
    streaks = compute_consecutive_ups(klines)
    rt_picks = build_realtime_picks(rt_news, quotes, klines, streaks)

    print(f"  [6/7] 获取基金数据...", flush=True)
    fund_data = fetch_all_fund_data()
    _api_calls += 4  # 3 ranking calls + estimates
    fund_count = len(fund_data.get('summary', []))
    est_count = len(fund_data.get('estimates', {}))
    print(f"        基金排行 {fund_count} 只, 实时估值 {est_count} 只", flush=True)

    print(f"  [7/7] 生成HTML...", flush=True)
    _run_elapsed = time.time() - _run_start
    html = generate_html(hot7, rt_news, night_news, all_news, quotes, sec_sum, rt_picks, streaks, run_elapsed=_run_elapsed, run_api_calls=_api_calls, fund_data=fund_data)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  完成 ({_run_elapsed:.1f}s, API {_api_calls}次, 精选{len(rt_picks)}只, 基金{fund_count}只)", flush=True)
    return hot7, rt_picks, quotes

def run_daemon():
    """Daemon mode: auto-refresh dashboard on schedule.
    - Market hours (9:15-15:00 weekdays): every 15 minutes
    - Pre-market 8:30: refresh once
    - Post-market 15:30: refresh once
    - Otherwise: every 60 minutes
    """
    import sys as _sys
    print("🔄 Daemon模式启动 (面板自动刷新)", flush=True)
    print("   盘中 9:15-15:00: 每15分钟刷新", flush=True)
    print("   盘前 8:30 / 盘后 15:30: 各刷新一次", flush=True)
    print("   其他时段: 每60分钟刷新", flush=True)
    print("   Ctrl+C 退出", flush=True)
    print(flush=True)
    _sys.stdout.flush()

    last_refresh = 0
    refreshed_premarket = False
    refreshed_postmarket = False
    last_date = ''

    # Initial refresh
    try:
        generate_dashboard_once()
        last_refresh = time.time()
        print("✅ 初始刷新完成", flush=True)
    except Exception as e:
        print(f"  初始刷新异常: {e}", flush=True)

    while True:
        try:
            now = beijing_now()
            today = now.strftime('%Y-%m-%d')
            t_min = now.hour * 60 + now.minute
            elapsed = time.time() - last_refresh

            # Reset daily flags
            if today != last_date:
                refreshed_premarket = False
                refreshed_postmarket = False
                last_date = today

            should_refresh = False

            # Pre-market: 8:25-8:35
            if 8*60+25 <= t_min <= 8*60+35 and not refreshed_premarket:
                print(f"[{now.strftime('%H:%M:%S')}] ☀️ 盘前刷新")
                should_refresh = True
                refreshed_premarket = True

            # Post-market: 15:25-15:35
            elif 15*60+25 <= t_min <= 15*60+35 and not refreshed_postmarket:
                print(f"[{now.strftime('%H:%M:%S')}] 🌙 盘后刷新")
                should_refresh = True
                refreshed_postmarket = True

            # Market hours: every 15 min
            elif is_market_hours() and elapsed >= 15 * 60:
                print(f"[{now.strftime('%H:%M:%S')}] ⏰ 盘中定时刷新")
                should_refresh = True

            # Off-hours: every 60 min
            elif not is_market_hours() and elapsed >= 60 * 60:
                print(f"[{now.strftime('%H:%M:%S')}] 💤 非盘中定时刷新")
                should_refresh = True

            if should_refresh:
                try:
                    generate_dashboard_once()
                    last_refresh = time.time()
                    sys.stdout.flush()
                except Exception as e:
                    print(f"  刷新异常: {e}", flush=True)

            time.sleep(30)  # check every 30 seconds

        except KeyboardInterrupt:
            print("\n⏹ Daemon已停止")
            break
        except Exception as e:
            print(f"  循环异常: {e}")
            time.sleep(60)

# ═══ MAIN ═══════════════════════════════════════════════════
if __name__ == '__main__':
    tg_token = os.environ.get('TG_TOKEN', '')
    tg_chat = os.environ.get('TG_CHAT_ID', '')
    tg_channel = os.environ.get('TG_CHANNEL', '')  # e.g. @xiaoluozi_ai

    # Build target list: private chat + optional channel
    def build_targets():
        targets = []
        if tg_chat: targets.append(tg_chat)
        if tg_channel: targets.append(tg_channel)
        return targets

    # --daemon mode: auto-refresh dashboard
    if '--daemon' in sys.argv:
        run_daemon()
        sys.exit(0)

    # --bot mode: command listener + scheduled push + alerts (recommended)
    if '--bot' in sys.argv:
        if not tg_token or not tg_chat:
            print("❌ Bot模式需要设置 TG_TOKEN 和 TG_CHAT_ID")
            print("   export TG_TOKEN='你的token' TG_CHAT_ID='你的chat_id'")
            sys.exit(1)
        targets = build_targets()
        if tg_channel:
            print(f"📢 频道同步推送: {tg_channel}")
        interval = 120
        min_impact = 1.5
        for arg in sys.argv:
            if arg.startswith('--interval='): interval = int(arg.split('=')[1])
            if arg.startswith('--min-impact='): min_impact = float(arg.split('=')[1])
        run_bot(tg_token, targets, interval=interval, min_impact=min_impact)
        sys.exit(0)

    # --watch mode: realtime monitoring with instant alerts
    if '--watch' in sys.argv:
        if not tg_token or not tg_chat:
            print("❌ 实时监控需要设置 TG_TOKEN 和 TG_CHAT_ID")
            print("   export TG_TOKEN='你的token' TG_CHAT_ID='你的chat_id'")
            sys.exit(1)
        # Parse optional interval: --interval=60
        interval = 120
        min_impact = 1.5
        for arg in sys.argv:
            if arg.startswith('--interval='):
                interval = int(arg.split('=')[1])
            if arg.startswith('--min-impact='):
                min_impact = float(arg.split('=')[1])
        run_watch(tg_token, build_targets(), interval=interval, min_impact=min_impact)
        sys.exit(0)

    # Normal mode: full dashboard + optional summary push
    _run_start = time.time()
    _api_calls = 0
    print(f"[1/7] 获取同花顺资讯 (全部+重要+机会)... (北京时间 {beijing_now().strftime('%H:%M:%S')})")
    news = fetch_news(pages=4, page_size=40)
    _api_calls += 12  # 3 tags × 4 pages
    print(f"      同花顺 {len(news)} 条")

    print("[2/7] 获取东方财富快讯...")
    em_news = fetch_eastmoney_news(pages=3, page_size=50)
    _api_calls += 4
    seen_titles = set(n.get('title','')[:20] for n in news)
    for en in em_news:
        if en['title'][:20] not in seen_titles:
            news.append(en)
            seen_titles.add(en['title'][:20])
    print(f"      东方财富 {len(em_news)} 条, 合并后 {len(news)} 条")

    print("[3/7] 分析情绪 / 提取热点...")
    hot7, rt_news, night_news, all_news, all_codes, sec_sum = analyze_all(news)
    print(f"      利好{sum(1 for n in all_news if n['sentiment']=='利好')} / 利空{sum(1 for n in all_news if n['sentiment']=='利空')} / 中性{sum(1 for n in all_news if n['sentiment']=='中性')}")
    print(f"      实时{len(rt_news)} / 夜间{len(night_news)}")
    print(f"      TOP7: {', '.join(s['name'] for s in hot7)}")

    etf_codes = set()
    for s in sec_sum:
        if s['etf_code']: etf_codes.add(s['etf_code'])

    print(f"[4/7] 获取{len(all_codes)}只股票 + {len(etf_codes)}只ETF行情...")
    quotes = fetch_quotes(list(all_codes) + list(etf_codes))
    _api_calls += max(1, (len(all_codes) + len(etf_codes) + 29) // 30)
    print(f"      {len(quotes)}条报价")

    # K-line for hot7 + bullish stocks with quotes
    kline_codes = set(s['code'] for s in hot7)
    for n in rt_news:
        if n['sentiment'] == '利好':
            for sc in n['stocks']: kline_codes.add(sc['code'])
    kline_codes = [c for c in kline_codes if c in quotes and quotes[c].get('price',0) > 0]

    print(f"[5/7] 获取{len(kline_codes)}只股票日K (连涨分析)...")
    klines = fetch_kline(kline_codes[:50], days=10)
    _api_calls += min(len(kline_codes), 50)
    streaks = compute_consecutive_ups(klines)
    streak_stocks = [(c, v) for c, v in streaks.items() if v['streak'] >= 2]
    if streak_stocks:
        parts = []
        for c, v in sorted(streak_stocks, key=lambda x: -x[1]['streak'])[:5]:
            nm = quotes.get(c, {}).get('name', c)
            parts.append(f'{nm}({v["streak"]}连涨)')
        print(f"      连涨龙头: {', '.join(parts)}")

    rt_picks = build_realtime_picks(rt_news, quotes, klines, streaks)
    print(f"      实时利好精选: {len(rt_picks)}只")

    print("[6/7] 获取基金数据...")
    fund_data = fetch_all_fund_data()
    _api_calls += 4
    print(f"      基金排行 {len(fund_data.get('summary',[]))} 只, 实时估值 {len(fund_data.get('estimates',{}))} 只")

    print("[7/7] 生成面板...")
    _run_elapsed = time.time() - _run_start
    html = generate_html(hot7, rt_news, night_news, all_news, quotes, sec_sum, rt_picks, streaks, run_elapsed=_run_elapsed, run_api_calls=_api_calls, fund_data=fund_data)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"      输出: {out}")

    # Telegram push
    targets = build_targets()
    if tg_token and targets:
        print(f"[推送] 推送到 Telegram ({', '.join(targets)})...")
        hot7e_msg = []
        for s in hot7:
            hot7e_msg.append({**s, 'reasons': list(s['reasons']), 'news': s['news'][:3]})
        msg = build_tg_message(hot7e_msg, rt_picks, quotes)
        send_telegram(tg_token, targets, msg)
    else:
        print("[推送] 跳过 (未设置 TG_TOKEN / TG_CHAT_ID)")
