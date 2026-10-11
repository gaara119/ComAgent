"""Read-only evidence audit; writes only the newly authorized preaudit directories."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / 'eval/reports/d2-ai-preaudit'
ARTIFACT = ROOT / 'eval/artifacts/d2-ai-preaudit'
CSV = ROOT / 'data/aliases/aliases.csv'
UNIFIED = ROOT / 'eval/reports/d2-acceptance/unified-review.json'
DB = ROOT / 'eval/artifacts/d2-ai-preaudit/database-materials.json'
CAT = ROOT / 'data/catalog/chinook.yaml'
INDEX = ROOT / 'data/indexes/values/records.jsonl'
DICTIONARY = ROOT / 'data/docs/raw/d2/chinook-dictionary-zh.md'

def read_json(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def local(path, section, supports, line=None):
    d = {'path': path, 'section': section, 'supports': supports, 'kind': 'local_material'}
    if line is not None:
        d['line'] = line
    return d

sources = {}
def external(key, url, title, section, supports, access='浏览工具已返回可读正文', strength='primary'):
    d = {'path': url, 'url': url, 'section': section, 'title': title, 'supports': supports,
         'kind': 'external_source', 'access': access, 'source_strength': strength}
    sources[key] = d
    return d

external('metallica', 'https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html',
         '文化部关于同意美国金属乐队到上海市演出的批复', '批复正文，第36行；文市函〔2013〕689号',
         '文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。')
external('iron', 'https://www.sonymusic.com.tw/?p=21566', '索尼音乐：早晨後的配樂 十周年紀念版',
         '专辑简介首段', '唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。')
external('iron_variant', 'https://zh.wikipedia.org/wiki/%E9%90%B5%E5%A8%98%E5%AD%90%E6%A8%82%E5%9C%98',
         '维基百科：铁娘子乐团', '条目首段与英文名信息框',
         '可读搜索正文列出另一中文译名“铁处女”，支持其作为候选；不证明项目默认译名。',
         '搜索工具返回可读条目正文；open完整页返回 Internal Error，未取得完整原页', 'secondary')
external('iron_ambiguity', 'https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3',
         '维基百科：铁处女', '条目首段', '同一词形也用于刑具；只作为跨领域歧义佐证。',
         '搜索工具返回可读条目正文；未在本轮打开完整页', 'secondary')
external('led', 'https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29',
         '维基百科：齐柏林飞船（乐团）', '条目标题、首段与英文名信息',
         '中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。',
         '搜索工具返回可读条目正文', 'secondary')
external('led_variant', 'https://www.visitnsw.com/cn/destinations/central-coast/gosford-area/avoca-beach/events/the-life-times-led-zeppelin-featuring-zepplin-orchestral-strings',
         '新南威尔士州旅游官网：齐柏林飞艇乐队的生平与时代', '活动标题与简介',
         '官方旅游活动中文页使用“齐柏林飞艇”，页面路径标明 Led Zeppelin；只支持中文名用法，不审核演出时效。',
         '搜索工具返回标题与正文节选；open完整页返回 Internal Error', 'primary')
external('u2', 'https://www.u2.com/pages/band', 'U2 官网：THE BAND', '页面标题与成员/建团首段',
         '官网确认 U2 是乐队；“乐队/乐团”为同类中文限定语的AI语言判断，不采纳网页当前活动信息。')

country_urls = {
    'Australia': 'https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/',
    'Brazil': 'https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/',
    'Canada': 'https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/',
    'France': 'https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/',
    'Germany': 'https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/',
    'India': 'https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml',
    'USA': 'https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml',
    'United Kingdom': 'https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/',
    'Italy': 'https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/',
}
country_cn = {'Australia': '澳大利亚', 'Brazil': '巴西', 'Canada': '加拿大', 'France': '法国',
              'Germany': '德国', 'India': '印度', 'USA': '美国', 'United Kingdom': '英国', 'Italy': '意大利'}
for k, url in country_urls.items():
    external('country_' + k, url, '外交部：' + country_cn[k] + '国家概况', '页面标题、国名段及英/本国语国名',
             '官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。')
external('moe_europe', 'https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4',
         '教育部重编国语辞典：世界各国国名表及附图', '欧洲地区：法兰西、德意志、义大利各条目',
         '国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。')
external('moe_australia', 'https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4',
         '教育部重编国语辞典：西文译名索引表', '澳洲—Australia条目',
         '辞典索引将“澳洲”与 Australia 对应；未证明一切大陆/洲语境都能作国家筛选。',
         '搜索工具返回可读索引节选')
external('italy_short', 'https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all',
         '日本国立国会图书馆参考协同数据库：主要国家汉字表记', '回答第85–87行：中国语表记',
         '图书馆参考答复列出意大利中文国名的该简称；未证明中国大陆当代查询中的频率。')
external('uk_short', 'https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD',
         '剑桥中文简体—英语辞典：联合王国', '联合王国主词条', '中英词条直接支持 United Kingdom 的中文短名。',
         '搜索工具返回可读词条正文；open完整页返回 Internal Error')
external('american_slang', 'https://languagelog.ldc.upenn.edu/nll/?p=11626',
         'Language Log：Laowai: the old furriner', '关于老美/美国人的讨论段',
         '语言研究者讨论此词的俚语与人员指称；由该词推至国家是语境推断，不是地理字段的字面等价。')

dict_base = 'https://dictionary.cambridge.org/dictionary/english-chinese-simplified/'
for key, slug, section, supports in [
    ('classical', 'classical', 'classical adjective (ART, MUSIC ETC)', '词典支持古典义；结合数据库流派字段选取音乐义。'),
    ('classical_music', 'classical-music', '主词条', '词典支持 classical music 的中文音乐流派译法。'),
    ('jazz', 'jazz', 'jazz noun [U] 音乐义', '词典支持爵士音乐义，也列出非音乐品牌义；须限 genre.name。'),
    ('pop', 'pop', 'pop noun (MUSIC)', '词典支持 Pop 的音乐义，不能把普通形容词“流行”当作热度排序指标。'),
    ('rock', 'rock', 'rock noun (MUSIC)', '词典支持 Rock 的中文音乐义。'),
    ('rock_and_roll', 'rock-and-roll', '主词条音乐义', '词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。'),
    ('heavy_metal', 'heavy-metal', 'heavy metal noun (MUSIC)', '词典支持重金属音乐义；此值与数据库 Metal 类别同列并存。'),
    ('audio', 'audio', 'audio adjective / audio noun', '词典支持音频用语；格式缩写保持数据库原词形。'),
    ('protected', 'protected', '一般形容词义', '词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。'),
    ('purchase', 'purchase', 'purchase verb / noun (BUYING)', '词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。'),
]:
    external(key, dict_base + slug, '剑桥英汉辞典：' + slug, section, supports,
             '搜索工具返回可读词条正文；Rock And Roll完整页open为403' if key == 'rock_and_roll'
             else '搜索工具返回可读词条正文；本轮未单独open完整页')
external('metal_music', 'https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul',
         '剑桥英语辞典：metal', 'metal noun (MUSIC)及Synonym',
         '辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。',
         '搜索工具返回可读词条正文')

u = read_json(UNIFIED)
# Do not inspect, render, export, or print any evaluation-question rows.
unified = [x for x in u['rows'] if x.get('group') == 'alias']
assert len(unified) == 81
del u
db = read_json(DB)
schema = {x['table'] + '.' + x['column']: x for x in db['schema']}
with CSV.open(encoding='utf-8-sig', newline='') as f:
    csvrows = list(csv.DictReader(f))
csvmap = {x['alias_id']: (i + 2, x) for i, x in enumerate(csvrows)}
indices = {}
for line, s in enumerate(INDEX.read_text(encoding='utf-8-sig').splitlines(), 1):
    x = json.loads(s)
    if x.get('kind') == 'standard':
        indices[(x['column'], x['standard_value'])] = (line, x['candidate_id'])
surfaces = defaultdict(list)
for x in csvrows:
    surfaces[x['alias']].append({'column': x['column'], 'standard_value': x['standard_value'], 'id': x['alias_id']})
catlines = CAT.read_text(encoding='utf-8-sig').splitlines()
dictlines = DICTIONARY.read_text(encoding='utf-8-sig').splitlines()

artist_local = {
    'Iron Maiden': ('data/docs/raw/d2/iron-maiden.html', '公开背景第1段/标准名称页脚', 4, 'iron'),
    'Led Zeppelin': ('data/docs/raw/d2/source/led-zeppelin-summary.html', '公开背景第1段/标准名称页脚', 4, 'led'),
    'Metallica': ('data/docs/raw/d2/metallica-introduction.docx', 'word/document.xml：段落1标题、段落3与5', None, 'metallica'),
    'U2': ('data/docs/raw/d2/u2.html', '公开背景第1段/标准名称页脚', 4, 'u2'),
}

rows = []
for original in unified:
    rid = original['id']
    exp = original['expected']
    alias, col, value = exp['alias'], exp['column'], exp['standard_value']
    csvline, raw = csvmap[rid]
    assert (alias, col, value) == (raw['alias'], raw['column'], raw['standard_value'])
    field_exists = col in schema
    values = db['text_values'].get(col, {}).get('values', [])
    value_exists = value in values
    assert field_exists and value_exists
    assert not db['text_values'][col]['truncated']
    idxline, candidate_id = indices[(col, value)]
    table, column = col.split('.')
    tableline = next(i + 1 for i, t in enumerate(catlines) if t == '  name: ' + table)
    columnline = next(i + 1 for i in range(tableline, len(catlines)) if catlines[i] == '  - name: ' + column)
    dsection = '### ' + table
    dline = next(i + 1 for i, t in enumerate(dictlines) if t == dsection)
    ev = [
        local('data/aliases/aliases.csv', '待审行；LLM草稿仅作对象/来源登记，不作译名证明', '原待审别名、字段、标准值、pending配置', csvline),
        local('data/catalog/chinook.yaml', 'tables[' + table + '].columns[' + column + ']', '实际目录中的字段与业务含义', columnline),
        local('eval/artifacts/d2-ai-preaudit/database-materials.json',
              '$.schema中的 ' + col + '; $.text_values["' + col + '"].values[' + str(values.index(value)) + ']; 原始queries内该列SELECT DISTINCT',
              'qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断'),
        local('data/indexes/values/records.jsonl', 'kind=standard; candidate_id=' + candidate_id, '既有标准值索引旁证；未重建索引', idxline),
        local('data/docs/raw/d2/chinook-dictionary-zh.md', dsection, '字典中的字段范围说明', dline),
    ]
    status, disposition, complete = 'AI建议通过', '建议直接使用', True
    issues = []
    semantic, suggestion, human = '', '', ''
    inference = []
    if table == 'artist':
        path, section, line, sk = artist_local[value]
        ev += [local(path, section, '本地项目改写艺人材料确认对象背景；不是LLM别名草稿', line), sources[sk]]
        if alias in ('Iron Maiden乐队', 'Led Zeppelin乐队', 'Metallica乐队', 'U2乐队', 'U2乐团'):
            semantic = f'“{alias}”完整保留标准名称 {value}，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。'
            suggestion = f'在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 {value}。'
            human = '人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。'
            inference = ['中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。']
        elif alias == '铁娘子':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            semantic = '本地简介与唱片公司中文资料均支持 Iron Maiden 的该中文乐队名。裸词还可作人物称号、作品名或刑具名，真实库仅有该艺人并不能消除库外语义；须先确认音乐艺人语境。'
            issues = ['裸词跨领域多义；不能仅因 artist 表中恰有一个匹配就对任意输入唯一绑定。']
            ev.append(sources['iron_ambiguity'])
            suggestion = '明确“铁娘子乐队”、曲目/专辑或artist字段上下文时保留 Iron Maiden 候选；否则澄清指称。'
            human = '确认默认中文乐队名及裸词歧义处理；不要照抄既有建议作为人审结论。'
        elif alias == '铁处女':
            status, disposition, complete = 'AI建议有条件通过', '仅作为条件候选', False
            semantic = '本地简介只支持“铁娘子”；外部百科可读条目正文另外列出“铁处女”为该乐团译名，因此现有材料不足以断言此词错误。该词同时明确指刑具，且完整原页未成功访问、未找到同等级唱片公司中文证据；仅能暂列音乐艺人语境下的条件候选。'
            issues = ['同词刑具义明显。', '译名依据为外部二手百科可读节选；完整原页访问失败，证据链仍需补强。']
            ev += [sources['iron_variant'], sources['iron_ambiguity']]
            suggestion = '禁止对裸词自动唯一绑定；仅在用户明确讨论乐队且人审补充可信译名证据后考虑候选。'
            human = '核实完整中文译名来源，选择地域译法与条件检索范围；既有“拒绝”建议也不是证据。'
        elif alias in ('齐柏林飞船', '齐柏林飞艇'):
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            if alias == '齐柏林飞艇':
                ev.append(sources['led_variant'])
                semantic = '本地简介使用“齐柏林飞船”；另有州旅游官网活动中文节选使用“齐柏林飞艇”且路径对应 Led Zeppelin，支持该译名变体。飞船/飞艇也有航空器语义；不能把这种词形变体作一般实体的固定替换。'
                issues = ['音乐乐队与航空器多义。', '外部变体来源完整页open失败，仅取得官方搜索节选。']
                complete = False
            else:
                semantic = '本地公开简介明确把该译名与 Led Zeppelin 并列，外部中文艺人条目旁证。该裸词又是飞船通名，翻译对应成立仅限音乐艺人语境；数据库标准对象存在不证明用户一定在问乐队。'
                issues = ['乐队译名与航空器名称多义。']
            suggestion = '明确“乐队/乐团”、音乐作品或artist字段后保留 Led Zeppelin 候选；航空器语境不绑定。'
            human = '确认接受飞船/飞艇两个地区用名及音乐上下文约束；需要时补读完整外部变体原页。'
        elif alias == '金属乐队':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            semantic = '本地 DOCX 标题使用此专名，文化部演出批复把它与 Metallica 并列，已取得独立中文名证据。它也可指任意演奏金属音乐的乐队；用户问“有哪些金属乐队”是一个类别问题，不能改成只查 Metallica。'
            issues = ['专名与音乐类别组合短语同形；类别查询可能包含多位artist。']
            suggestion = '专名或 Metallica 指称明确时作候选；泛指一类乐队时按流派/作品分析并澄清，不强制唯一艺人。'
            human = '确认专名使用情形与类别问句的识别边界。'
        elif alias == '金属':
            status, disposition, complete = '证据不足', '证据不足', False
            semantic = 'Metallica 是真实 artist，文化部支持其完整中文名“金属乐队”，但已读本地与外部资料没有把裸词“金属”独立作为该乐队简称的证据。相同词形在待审CSV另指 genre.name=Metal，真实流派库还包含 Heavy Metal；删去“乐队”是有歧义的AI猜测，不能据熟悉程度批准。'
            issues = ['未取得“金属”作为Metallica简称的独立用法证据。', '与 genre.name=Metal 同形且可能泛指金属音乐/材料。']
            ev += [sources['metal_music'], local('eval/artifacts/d2-ai-preaudit/database-materials.json', '$.text_values["genre.name"].values：Metal和Heavy Metal', '真实类别并存，提供歧义候选')]
            suggestion = '暂不作为可直接使用的艺人别名；补充真实简称来源后仍须限定艺人语境，不得剥夺流派候选。'
            human = '提供可信简称用例并确认优先级；找不到依据时不启用该裸词艺人映射。'
        else:
            raise AssertionError(alias)
    elif table in ('customer', 'invoice'):
        ev.append(sources['country_' + value])
        business = '客户所在地国家' if table == 'customer' else '发票账单地址国家'
        other = 'invoice.billing_country' if table == 'customer' else 'customer.country'
        semantic = f'外交部该国概况支持 {value} 对象的中文简称/正式国名。这里的 {col} 表示{business}；中文国家名翻译正确不代表可替换成 {other}，也不能由国家字段推断个人国籍。'
        suggestion = f'先确认问题要筛选{business}，再在 {col} 中使用精确标准值 {value}；保留另一国家字段的独立口径。'
        human = f'确认所指的是{business}及目标国家名称；人审后再决定是否启用，不填人审签名。'
        if alias == country_cn[value] or alias in ('澳大利亚联邦', '巴西联邦共和国', '法兰西共和国', '德意志联邦共和国', '印度共和国', '美利坚合众国', '大不列颠及北爱尔兰联合王国'):
            semantic = f'“{alias}”由外交部国家概况的国名与页面名称支持，对应真实标准值 {value}。' + semantic.split('。', 1)[1]
            if value == 'USA':
                inference = ['数据库USA与外交部完整英文国名的缩写等价是通常语言推断；库内真实取值仍按USA。']
            if value == 'Italy':
                inference = ['外交部意大利对象及中文国名支持国家指称；Italy英文名对应是通常语言知识，并由既有真实数据库值核验。']
        elif alias in ('法兰西', '德意志'):
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            ev.append(sources['moe_europe'])
            semantic = f'教育部国名表独立支持“{alias}”这一国家用名，不能按“正式国名截短”猜出。{alias}也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。' + semantic.split('。', 1)[1]
            issues = ['历史政体、民族/文化形容语与现代国家指称须区分。']
            suggestion += ' 历史/民族语境需澄清，不把历史国家自动改成现代值。'
            human = '确认支持该地区/历史用名，并限制于本快照国家语境。'
            inference = ['繁体原词形转换为该简体别名是AI通常语言推断。']
        elif alias == '澳洲':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            ev.append(sources['moe_australia'])
            semantic = '教育部译名索引直接将“澳洲”与 Australia 对应，国家用法有独立依据。该词在用户表达中也可能作大陆/广域地区用语；不能仅因当前国家库无洲级值就把地区意图压成一个国家。' + semantic.split('。', 1)[1]
            issues = ['国家简称与大陆/广域地区意图可能混淆。']
            suggestion += ' 用户谈大陆、洲或多个国家时先澄清范围。'
            human = '确认本项目接受该地区用名，并规定国别/洲别澄清方式。'
        elif alias == '联合王国':
            ev.append(sources['uk_short'])
            semantic = '剑桥中英词条直接支持此中文短名与 United Kingdom 对应；外交部全称提供完整国家对象，不会缩成英格兰。' + semantic.split('。', 1)[1]
            inference = ['此判断限定本项目现代国家值，不用于历史或其他联合王国语境。']
        elif alias == '义大利':
            ev.append(sources['moe_europe'])
            semantic = '教育部国名表使用繁体“義大利”并对应意大利国家，地域译名有独立依据；本别名转为简体“义大利”是通常字形转换。' + semantic.split('。', 1)[1]
            inference = ['该地区译名的简繁转换是AI语言推断，不是意/义字随意纠错。']
        elif alias == '意国':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            ev.append(sources['italy_short'])
            semantic = '日本国立国会图书馆参考库的中文国名答复明确列出该简称，不能仅因它少见就判断为错。材料未证明本项目用户高频使用，短词也需限定国家语境；作为保守候选比直接唯一匹配合适。' + semantic.split('。', 1)[1]
            issues = ['简称来源属于图书馆参考答复；本项目真实用法和频率未提供。']
            human = '确认目标用户地域/语体是否需要此简称；没有真实用例也不自动扩大映射范围。'
        elif alias == '老美':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            ev.append(sources['american_slang'])
            semantic = '该口语词可以指美国人或以人员/政府借指美国；语言讨论支持俚语人员指称，外交部国名并不把它登记为标准国家名称。从“美国人”到所在地/账单国家不是等价关系：国籍、所在地、账单地址必须区分。只有用户明确用它表示国家地理筛选时，USA才可暂作候选。' + semantic.split('。', 1)[1]
            issues = ['俚语人员/政府指称与国家地理实体不等价。', '可能把国籍意图误改为customer.country或invoice.billing_country。']
            suggestion = f'明确国别地理语境且所需字段为 {col} 时才提议 USA；人员、国籍或政治指称应澄清，不直接生成字段过滤。'
            human = '确认俚语是否应纳入检索及其地理筛选约束，不能把语体偏好误作事实错误。'
            inference = ['该词在某些问句中借指美国的用法是AI语境推断；来源不证明可无条件换成country值。']
        else:
            raise AssertionError(alias)
    elif table == 'genre':
        if value == 'Classical':
            ev += [sources['classical'], sources['classical_music']]
            semantic = f'“{alias}”有剑桥 classical/ classical music 音乐义支持，目标为真实流派 Classical。在已明确 genre.name 的查询中，省略“音乐”不会改成艺术家或年代；不将它限制为字典列举的某个作曲年代。'
            suggestion = '音乐流派语境中可用于 Classical；艺术/建筑等其他古典义不得绑定。'
            human = '确认项目Classical分类使用范围，避免把语言词典时代定义当成数据库分类规则。'
            if alias == '古典':
                inference = ['省略“音乐”只在已确定genre字段时补全，是AI语境判断。']
        elif value == 'Jazz':
            ev.append(sources['jazz'])
            semantic = f'词典的音乐义支持“{alias}”与 Jazz 对应；真实库有Jazz。省略“乐”可在音乐流派语境成立，不能把爵位称号或品牌等非音乐义当作genre过滤。'
            suggestion = 'genre明确时可用Jazz；若“爵士”指人名/爵位/品牌则澄清。'
            human = '确认只接受音乐流派语境。'
            if alias == '爵士':
                inference = ['短词音乐义通过genre上下文选定，是AI语境判断。']
        elif value == 'Pop':
            ev.append(sources['pop'])
            semantic = f'剑桥 Pop 的音乐义支持“{alias}”；标准对象真实存在。中文“流行”还可表示受欢迎程度，“最流行的曲目”不是genre=Pop的同义改写，必须识别这是分类请求。'
            suggestion = '明确请求Pop流派时可用；热度/销量/流行程度比较不自动改成Pop过滤。'
            human = '确认分类语义与流行程度指标分开处理。'
            if alias == '流行':
                status, disposition = 'AI建议有条件通过', '仅作为条件候选'
                issues = ['流派短名与受欢迎程度形容词多义。']
                inference = ['从裸词“流行”选定Pop音乐义是AI上下文推断。']
        elif value == 'Metal':
            ev += [sources['metal_music'], sources['heavy_metal']]
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            semantic = f'“{alias}”在音乐上下文可表达Metal，字典有metal音乐义和对应金属音乐术语；但真实genre同时有Metal和Heavy Metal，词典还把两者列为一般语言同义。因此能作Metal候选不代表数据库分类可合并或唯一绑定。'
            issues = ['真实数据库Metal与Heavy Metal是不同标准分类，泛称可能覆盖两者。']
            if alias == '金属':
                issues.append('同一裸词在待审CSV还候选artist.name=Metallica，且另有材料义。')
            suggestion = '明确用户指数据库Metal分类时选Metal；泛称金属音乐时展示Metal/Heavy Metal范围并澄清；艺人语境保留独立候选。'
            human = '确定泛称金属音乐的业务范围；多候选许可不是自动将标准值合并或唯一绑定。'
            inference = ['中文“金属乐”与metal音乐义的术语组合属于AI语言推断，来源不定义Chinook类别边界。']
        elif value in ('Rock', 'Rock And Roll'):
            ev += [sources['rock'], sources['rock_and_roll']]
            if alias == '节奏摇滚':
                status, disposition, complete = '证据不足', '证据不足', False
                semantic = '目标 Rock And Roll 在真实库存在，但已读本地字典仅说明流派字段，没有给出“节奏摇滚”译名。独立英汉词条支持一般摇滚译法，未支持加入“节奏”后能专指这一数据库分类；本轮检索没有取得该译名的可信来源。不能因为它能人为避开Rock歧义就认定翻译正确，也不能用未搜到断言该词绝不存在。'
                issues = ['没有独立来源证明“节奏摇滚”专指Rock And Roll。', '加入“节奏”的意图可能只是人为区分类别，非真实译名依据。']
                suggestion = '暂不启用该译名；补充可信音乐术语来源或明确人审定义后再评估，保留Rock/Rock And Roll本来的分类差异。'
                human = '补证据并确认术语；不要仅依照既有“拒绝”建议盖章。'
            else:
                status, disposition = 'AI建议有条件通过', '仅作为条件候选'
                semantic = f'独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“{alias}”可表达 {value}，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。'
                issues = ['同字段同中文词形存在Rock/Rock And Roll两候选。']
                suggestion = f'保留 {value} 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。'
                human = '确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。'
                if alias == '摇滚':
                    inference = ['短词省略“乐”是AI中文语言判断；仍保留两分类候选。']
        else:
            raise AssertionError(value)
    elif table == 'media_type':
        ev.append(sources['audio'])
        if value.startswith('Protected'):
            ev.append(sources['protected'])
            semantic = f'“{alias}”保留标准名称 {value} 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。'
            if value.endswith('video file'):
                inference = ['video=file中的视频/文件为通常语言知识；未展开MPEG-4缩写或推断实际编码实现。']
            else:
                inference = ['Protected+AAC+audio/file中文组合是AI语言推断，未证明DRM实现或法律权利状态。']
            suggestion = f'媒体类型字段明确时可用；精确映射 {value} 并保留Protected，不能推断保护机制或客户付款状态。'
            human = '确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。'
        elif value.startswith('Purchased'):
            ev.append(sources['purchase'])
            semantic = f'“{alias}”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。'
            inference = ['Purchased形容词完成态的中文“已购买”为AI语法判断，独立词典只证明购买词义。']
            suggestion = f'只按媒体类型枚举 {value} 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。'
            human = '确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。'
            if alias == '购买AAC音频文件':
                status, disposition = 'AI建议有条件通过', '仅作为条件候选'
                semantic += '该词形未明确完成态，还可能是“购买一个AAC文件”的动作请求；必须先确认是在问类型标签。'
                issues = ['未标“已”，类型标签与购买动作请求多义。']
                suggestion += ' 若为购买行为或动作请求，先澄清，不据该词形唯一选择Purchased类型。'
        elif value == 'AAC audio file':
            status, disposition = 'AI建议有条件通过', '仅作为条件候选'
            semantic = f'“{alias}”保留AAC与audio的普通译义，未带Protected/Purchased修饰，适合作为数据库普通AAC类别的译名候选。但真实media_type还有Protected AAC与Purchased AAC；用户泛称AAC音频/文件可能指格式家族，不能自动只筛普通AAC。'
            issues = ['AAC格式泛称可能覆盖普通、Protected、Purchased三个真实枚举值。']
            inference = ['AAC+audio/file的中文组合是AI常用语言判断，格式缩写不变。']
            suggestion = '用户明确普通AAC类别时选AAC audio file；泛问AAC格式先澄清是否包含三个AAC类别。'
            human = '确认“普通类别”与“AAC格式总范围”的区别，禁止把父类说法直接绑定单个子类。'
        elif value == 'MPEG audio file':
            semantic = f'“{alias}”保持MPEG格式缩写及audio音频类型，中文组合翻译不涉及缩写展开。真实库另有Protected MPEG-4 video file，但其中video与本行audio不同；不能仅匹配MPEG词段忽略音频/视频限定。'
            inference = ['MPEG+audio/file的中文组合是AI常用语言判断。']
            suggestion = 'media_type字段和音频语境明确时可用该枚举；省略音频只说MPEG时重新澄清，不延伸本别名。'
            human = '确认保留音频限定，避免MPEG音频与MPEG-4视频的词段匹配冲突。'
        else:
            raise AssertionError(value)
    else:
        raise AssertionError(table)
    scope = '仅在目标字段已明确的语境下适用；AI预审不是启用操作。'
    reason = f'实查 {col} 字段与标准值 {value} 均存在，完整DISTINCT与既有标准值索引一致。{semantic} {scope}'
    rows.append({
        'review_id': original['review_id'], 'id': rid, 'group': 'alias',
        'alias': alias, 'column': col, 'standard_value': value,
        'reference_status': status, 'alias_disposition': disposition,
        'actual_status': '不适用（别名配置审核，未生成预测）',
        'reason': reason, 'issues': issues, 'suggestion': suggestion,
        'human_confirmation': human, 'evidence': ev, 'evidence_complete': complete,
        'field_exists': field_exists, 'standard_value_exists': value_exists,
        'registered_status_observed': raw['review_status'],
        'surface_candidates_observed': surfaces[alias], 'ai_inferences_and_limits': inference,
    })

assert len(rows) == 81
assert {x['review_id'] for x in rows} == {x['review_id'] for x in unified}
assert all(x['actual_status'] == '不适用（别名配置审核，未生成预测）' for x in rows)
assert all(x['registered_status_observed'] == 'pending' for x in rows)
assert all(len(x['evidence']) >= 5 and x['reason'] and x['human_confirmation'] for x in rows)
status_counter = Counter(x['reference_status'] for x in rows)
disposition_counter = Counter(x['alias_disposition'] for x in rows)
counts = {k: status_counter[k] for k in ('AI建议通过', 'AI建议有条件通过', 'AI发现错误', '证据不足')}
dispositions = {k: disposition_counter[k] for k in ('建议直接使用', '仅作为条件候选', '建议拒绝', '证据不足')}
report = {
    'title': 'D2 81项别名 AI 预审',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': '仅审别名配置登记与来源证据；开发环境材料审核；未调用问答API/项目模型，未重建索引，未作启用或人工审核。未阅读、输出或审核33项保留题内容。',
    'interpretation': {
        'direct_use': '建议直接使用仅是字段已明确时的AI候选映射建议，仍须真实人审决定启用。',
        'conditional': '条件候选保留多个合理标准对象；不等于自动绑定第一/最高分/唯一对象。',
        'evidence_complete': 'true表示本行字段/真值/名称或明确语言组合依据及限制已列；false表示独立译名缺失或关键原页未取得，不能冒充完整来源核验。',
        'local_artist_sources': '项目中文简介是带出处改写；只证明项目材料记载，不把LLM别名草稿与既有建议当成独立译名证据。',
        'ai_inference': '所有简繁转换、后缀组合、类型名称组合、缩写及语境判断在各行明确列示；词典不定义Chinook业务类别边界。',
        'actual_status': '本组无问答预测，实际状态全部不适用。',
    },
    'counts': {'total': 81, 'reference_status': counts, 'alias_disposition': dispositions,
               'evidence_complete': sum(x['evidence_complete'] for x in rows),
               'evidence_incomplete': sum(not x['evidence_complete'] for x in rows),
               'all_fields_and_values_exist': True},
    'input_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p)
                     for p in (CSV, UNIFIED, DB, CAT, INDEX, DICTIONARY)},
    'rows': rows,
}
REPORT.mkdir(parents=True, exist_ok=True)
ARTIFACT.mkdir(parents=True, exist_ok=True)
(REPORT / 'aliases-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(ARTIFACT / 'alias-external-source-observations.json').write_text(json.dumps({
    'checked_at_utc': report['generated_at_utc'],
    'method': '浏览工具检索/打开后人工读取的短证据摘要；未保存全文；访问不足在每项access中明确。',
    'negative_search_limit': '对节奏摇滚与Metallica裸词金属未取得可信独立用法，不等于证明它们绝无用法。',
    'sources': list(sources.values()),
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def escape(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')

lines = [
    '# D2 81项别名 AI 预审', '',
    '本报告仅为 AI 预审，没有人工签名、审核日期或批准状态，不启用任何别名。全部81行的实际状态均为“不适用（别名配置审核，未生成预测）”。没有调用问答API、项目模型或生成新系统预测；没有重建索引；未阅读/输出33项保留题内容。', '',
    '本轮先对真实只读数据库材料、实际catalog、既有索引及原待审CSV交叉核验，再检查 raw/d2 字典/艺人简介及独立公开来源。81项字段与标准对象均存在；LLM草稿和既有建议没有作为独立证明。真值存在不代表译名准确、适用范围正确或可以唯一绑定。', '',
    '“建议直接使用”只适用于目标字段已明确的别名匹配；“仅作为条件候选”需要音乐/国家/类型语境或用户澄清，且不能自动取第一或最高分候选。客户所在地国家与发票账单地址国家即使取值相同，也不允许换字段。', '',
    '| 状态 | 数量 |', '|---|---:|',
]
for k in ('AI建议通过', 'AI建议有条件通过', 'AI发现错误', '证据不足'):
    lines.append(f'| {k} | {counts.get(k, 0)} |')
lines += ['', f'证据完整：{report["counts"]["evidence_complete"]}；证据不完整：{report["counts"]["evidence_incomplete"]}。完整表示本行可核查的依据覆盖与局限已列，包含明确标注的常用语言组合推断；不代表人工批准。', '',
          '关键判断：金属（艺人Metallica简称）与节奏摇滚（Rock And Roll译名）缺少独立用法证据；铁处女有二手译名依据，不能按旧建议直接判错，但原页与高等级译名证据仍需补强；齐柏林飞艇完整原页访问失败。Rock/Rock And Roll、Metal/Heavy Metal、一般AAC/Protected AAC/Purchased AAC都需保留真实分类边界。', '',
          '| review_id | 别名 → 字段标准值 | 参考预审 | 处置建议 | 证据完整 |', '|---|---|---|---|---|']
for x in rows:
    lines.append('| ' + ' | '.join(escape(y) for y in [x['review_id'], x['alias'] + ' → ' + x['column'] + ' = ' + x['standard_value'], x['reference_status'], x['alias_disposition'], '是' if x['evidence_complete'] else '否']) + ' |')
for x in rows:
    lines += ['', '## ' + x['review_id'], '',
              '**' + x['alias'] + ' → ' + x['column'] + ' = ' + x['standard_value'] + '**', '',
              f'参考状态：{x["reference_status"]}；处置建议：{x["alias_disposition"]}；实际状态：{x["actual_status"]}；证据完整：{"是" if x["evidence_complete"] else "否"}。', '',
              x['reason'], '', '问题：' + ('；'.join(x['issues']) if x['issues'] else '未发现实质性映射错误；仍遵守字段限定与人审启用要求。'), '',
              '建议：' + x['suggestion'], '', '需人确认：' + x['human_confirmation']]
    if x['ai_inferences_and_limits']:
        lines += ['', 'AI推断与局限：' + '；'.join(x['ai_inferences_and_limits'])]
    if len(x['surface_candidates_observed']) > 1:
        lines += ['', '原CSV同词候选：' + '；'.join(y['column'] + '=' + y['standard_value'] for y in x['surface_candidates_observed']) + '。跨国家字段重复登记不会授权字段互换。']
    lines += ['', '证据：', '']
    for e in x['evidence']:
        p = e['path']
        label = e.get('title', p)
        target = p if p.startswith('https://') else (ROOT / p).as_posix() + (':' + str(e['line']) if 'line' in e else '')
        loc = '第' + str(e['line']) + '行；' if 'line' in e else ''
        text = f'- [{label}](<{target}>)：{loc}{e["section"]}。{e["supports"]}'
        if 'access' in e:
            text += ' 访问：' + e['access'] + '。'
        lines.append(text)
(REPORT / 'aliases-review.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'rows': len(rows), 'counts': counts, 'dispositions': dispositions,
                  'evidence_incomplete': [x['review_id'] for x in rows if not x['evidence_complete']],
                  'outputs': ['eval/reports/d2-ai-preaudit/aliases-review.json', 'eval/reports/d2-ai-preaudit/aliases-review.md',
                              'eval/artifacts/d2-ai-preaudit/alias-external-source-observations.json']}, ensure_ascii=False, indent=2))
