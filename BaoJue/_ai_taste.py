# -*- coding: utf-8 -*-
"""去 AI 味检测（零 Token，纯正则 + 统计）。

用法：
    python _ai_taste.py终版剧本/X003_终版.md
    python _ai_taste.py --json终版剧本/X004_文字剧本.md

判级：≥70 block / 40-69 warn / <40 pass
口径来源：skill short-drama-creation/references/去AI味.md
X002 风格裁决 7 条（用户 2026-09-29 亲手裁定）。

⛔ 上线前必须先跑 _ai_taste_selfcheck.py 验证本脚本自己。
"""
import io
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))

STRONG = ['不禁', '不由得', '不禁得', '仿佛', '宛如', '犹如', '恰似',
          '彷佛', '似乎在', '隐约', '莫名']
MEDIUM = ['一丝', '一抹', '微微', '缓缓', '轻轻', '淡淡', '深深',
          '一阵', '一股']
WEAK = ['眼神', '目光', '神色', '表情', '嘴角', '眉心', '眸中', '眼底']
DRAMA_BAD = ['一缕', '五官', '眉眼', '那一刻', '这一刻',
             '空气仿佛凝固', '时间仿佛静止']

# X002 风格裁决第 4 条：明令禁止，命中即 block
BANNED = [
    ('不是X是Y句式', re.compile(r'不是[^。！？\n]{1,20}[，,]\s*(?:而)?是')),
    ('没有X没有Y排比', re.compile(r'没有[^。！？\n]{1,15}[，,]\s*没有')),
    ('破折号', re.compile(r'——')),
    ('省略号', re.compile(r'…{2,}|\.{3,}')),
    ('箭头链', re.compile(r'[→➔➜]')),
    ('编号标签', re.compile(r'【[^】\n]{1,10}】')),
    ('评书腔', re.compile(r'(只见|却说|正是|当下|自此|便即|遂即)')),
]

CLICHE = ['看了看', '笑了笑', '点了点头', '皱了皱眉', '深吸一口气',
          '愣了一下', '眨了眨眼', '沉默不语', '不动声色']

CJK = re.compile(r'[\u4e00-\u9fff]')
#⛔ 台词行两种写法都必须认：
#   **钱经理**（拍桌）：台词← 带表演提示
#   **苏小满**：不是我            ← 无表演提示（X003 里大量这种）
# 早期版本只认带括号的，导致无括号台词行全被漏判成「散文」。
SPEECH = re.compile(r'^\*\*[^*]+\*\*\s*(?:[（(][^）)]*[）)]：)?\s*(.+)$')
STAGE = re.compile(r'^[△▲]')
# 场次标题 / 文档元信息，不算散文
HEADPAT = re.compile(
    r'^(第.{1,6}[集章]|场次|存档铁律|定版台账|归档|前情|后记|附)')
METAPAT = re.compile(r'^(来源|抓取日|本地文件|归档|状态)\s*[:：]')


def preprocess(text):
    """剥掉 Markdown 噪声，只留剧本实体。

    误判过的坑（都实测踩到）：
      ① 表格竖线 → 被当「编号标签」
      ② 「——」分隔线 → 被当「破折号」
      ③ 标题井号 → 被当「评书腔」
      ④ 存档铁律 / 定版台账 → 被当「散文叙述」
    """
    out = []
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            out.append('')
            continue
        if s.startswith('|'):
            continue
        if re.match(r'^[-=*_]{3,}$', s):
            continue
        if s.startswith('#'):
            s = s.lstrip('#').strip()
            if not s:
                continue
        if s.startswith('>'):
            s = s.lstrip('>').strip()
        if METAPAT.match(s):
            continue
        out.append(s)
    return out


def taste(text, verbose=True, name=''):
    lines = preprocess(text)
    findings = []
    score = 0
    block_hit = False
    body = '\n'.join(lines)

    # ── 层 1 词表 ──
    for w in STRONG:
        n = body.count(w)
        if n:
            score += n * 6
            findings.append(('warn', '强AI词', '%s ×%d' % (w, n)))
    for w in MEDIUM:
        n = body.count(w)
        if n:
            score += n * 4
            findings.append(('warn', '中AI词', '%s ×%d' % (w, n)))
    weak_total = sum(body.count(w) for w in WEAK)
    if weak_total >= 3:
        score += (weak_total - 3) * 2
        top = sorted(((w, body.count(w)) for w in WEAK),
                     key=lambda x: -x[1])[:3]
        findings.append(('warn', '弱AI词成串',
                         '共%d次：%s' % (weak_total,
                                     '、'.join('%s×%d' % (k, v) for k, v in top))))
    for w in DRAMA_BAD:
        n = body.count(w)
        if n:
            score += n * 5
            findings.append(('warn', '短剧禁词', '%s ×%d' % (w, n)))

    # ── 层 1 禁结构 ──
    for cat, pat in BANNED:
        hits = pat.findall(body)
        if hits:
            score += len(hits) * 12
            block_hit = True
            findings.append(('block', '禁结构', '%s ×%d' % (cat, len(hits))))

    # ── 层 2 统计：台词 ──
    speeches = [SPEECH.match(l).group(1) for l in lines if SPEECH.match(l)]
    clean = [re.sub(r'\*|\[Chinese\]', '', s) for s in speeches]
    lens = [len(CJK.findall(s)) for s in clean if CJK.findall(s)]

    if lens:
        avg = sum(lens) / len(lens)
        if avg > 25:
            score += 8
            findings.append(('warn', '台词均长', '%.1f 字（>25）' % avg))
        long_ratio = sum(1 for x in lens if x > 20) / len(lens)
        if long_ratio > 0.3 and avg > 20:
            score += 12
            block_hit = True
            findings.append(('block', '长句占比',
                             '%.0f%%>30%% 且均长 %.1f' % (long_ratio * 100, avg)))
        if max(lens) > 40:
            score += 10
            block_hit = True
            findings.append(('block', '超长台词', '最长 %d 字（>40）' % max(lens)))
        elif sum(1 for x in lens if x > 20) >= 2:
            score += 6
            findings.append(('warn', '超长台词', '%d 句 > 20 字' % sum(1 for x in lens if x > 20)))
        heads = []
        for s in clean:
            m = re.match(r'^[^\u4e00-\u9fff]*([\u4e00-\u9fff])', s)
            heads.append(m.group(1) if m else '')
        rep = sum(1 for i in range(2, len(heads))
                  if heads[i] == heads[i - 1] == heads[i - 2] and heads[i])
        if rep:
            score += 5
            findings.append(('warn', '句首复读', '连续三句同开头 ×%d' % rep))

    # ── 层 2 统计：动作套话（5 行窗口） ──
    real = [l for l in lines if l]
    for i in range(len(real) - 4):
        win = '\n'.join(real[i:i + 5])
        for w in CLICHE:
            if win.count(w) >= 2:
                score += 4
                findings.append(('warn', '动作套话', '「%s」5行内×%d' % (w, win.count(w))))
                break

    # ── 层 2 统计：的字密度 ──
    all_cjk = CJK.findall(body)
    if all_cjk:
        de = body.count('的') / len(all_cjk)
        if de > 0.12:
            score += 6
            findings.append(('warn', '「的」密度', '%.1f%% >12%%' % (de * 100)))

    # ── 层 2 统计：散文段 ──
    # 剧本主体 = 台词行 + △动作行；场次标题与文档元信息不算散文。
    paras, cur = [], []
    for l in lines:
        if l:
            cur.append(l)
        elif cur:
            paras.append(cur)
            cur = []
    if cur:
        paras.append(cur)

    narr_lines, narr_paras = 0, 0
    for pl in paras:
        has_speech = any(SPEECH.match(x) for x in pl)
        has_stage = any(STAGE.match(x) for x in pl)
        has_head = any(HEADPAT.match(x) for x in pl)
        if not has_speech and not has_stage and not has_head:
            narr_lines += len(pl)
            narr_paras += 1
    if narr_lines > 8:
        score += 10
        block_hit = True
        findings.append(('block', '长段散文', '连续 %d 行（>8）' % narr_lines))
    elif narr_lines > 4:
        score += 5
        findings.append(('warn', '长段散文', '连续 %d 行' % narr_lines))
    if narr_paras >= 5:
        score += 5
        findings.append(('warn', '散文段过多', '%d 段' % narr_paras))

    # ── 判级 ──
    verdict = 'block' if block_hit else ('warn' if score >= 40 else 'pass')

    if verbose:
        print('=' * 62)
        print('AI 味检测：%s' % (name or '(未命名)'))
        print('flavorScore = %d  →  %s' % (score, verdict))
        print('=' * 62)
        if not findings:
            print('干净。无AI 味命中。')
        else:
            order = {'block': 0, 'warn': 1}
            for lv, cat, msg in sorted(findings, key=lambda x: order[x[0]]):
                flag = 'BLOCK' if lv == 'block' else 'warn '
                print('  %-5s %-12s %s' % (flag, cat, msg))
        print()
        print('判级：≥70 block / 40-69 warn / <40 pass')
        print('目标：block 清零（X002 裁决第 5 条）')
    return score, verdict, findings


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    as_json = '--json' in args
    files = [a for a in args if not a.startswith('--')]
    out = []
    for f in files:
        if not os.path.exists(f):
            print('NOT FOUND: %s' % f)
            sys.exit(2)
        with io.open(f, encoding='utf-8') as fh:
            content = fh.read()
        if as_json:
            s, v, fs = taste(content, verbose=False)
            out.append({'file': f, 'score': s, 'verdict': v,
                        'findings': [{'level': a, 'cat': b, 'msg': c} for a, b, c in fs]})
        else:
            taste(content, name=os.path.basename(f))
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        if any(x['verdict'] == 'block' for x in out):
            sys.exit(1)


if __name__ == '__main__':
    main()