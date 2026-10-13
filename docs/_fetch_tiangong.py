# -*- coding: utf-8 -*-
"""批量抓取 tiangong.ligen.cn/docs 全部章节 -> docs/tiangong/*.md

用法： python _fetch_tiangong.py
⛔ 开头必须pop 掉环境代理（WorkBuddy 内部代理对外一律 502），改用 10808。
"""
import io
import os
import re
import sys
import json
import time
import urllib.request
import urllib.error

for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
          'ALL_PROXY', 'all_proxy'):
    os.environ.pop(k, None)

PROXY = 'http://127.0.0.1:10808'
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))

BASE = 'https://tiangong.ligen.cn'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tiangong')

PAGES = [
    ('00-guide',          '/docs/guide',        '导读与快速上手'),
    ('01-philosophy',     '/docs/philosophy',   '核心理念与创作全流程'),
    ('02-install',        '/docs/install',      '安装、启动与界面总览'),
    ('03-project',        '/docs/project',      '立项篇：新建与管理项目'),
    ('04-setup-world',    '/docs/setup-world',  '设定篇：骨架·世界·体系·金手指'),
    ('05-planner',        '/docs/planner',      '规划篇：三级结构与AI拆解大纲'),
    ('06-writing',        '/docs/writing',      '写作篇：写作台与轻松/专注模式'),
    ('07-guardian',       '/docs/guardian',     '守护篇：校验·去AI味·守护灯'),
    ('08-overview',       '/docs/overview',     '总览篇：脉络·模式库·伏笔·名词'),
    ('09-simulation',     '/docs/simulation',   '剧情推演室'),
    ('10-library',        '/docs/library',      '藏书阁：拆书与弹药'),
    ('11-ai-setup',       '/docs/ai-setup',     '设置篇：AI通道·授权·备份'),
    ('12-faq',            '/docs/faq',          '常见问题与术语表'),
]


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'text/html,application/xhtml+xml',
            })
            with opener.open(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def strip_tags(html):
    """极简 HTML -> 文本，保留结构。"""
    h = re.sub(r'(?is)<script.*?</script>', '', html)
    h = re.sub(r'(?is)<style.*?</style>', '', h)
    h = re.sub(r'(?is)<nav.*?</nav>', '', h)
    h = re.sub(r'(?is)<svg.*?</svg>', '', h)
    # 表格转 markdown
    h = re.sub(r'(?is)</t[dh]>\s*<t[dh][^>]*>', ' | ', h)
    h = re.sub(r'(?is)</tr>', '\n', h)
    h = re.sub(r'(?is)<table[^>]*>', '\n\n[表格]\n', h)
    h = re.sub(r'(?is)</table>', '\n[/表格]\n\n', h)
    # 列表
    h = re.sub(r'(?is)<li[^>]*>', '\n- ', h)
    # 标题
    for i in range(1, 7):
        h = re.sub(r'(?is)<h%d[^>]*>' % i, '\n\n' + '#' * i + ' ', h)
        h = re.sub(r'(?is)</h%d>' % i, '\n', h)
    # 段落与换行
    h = re.sub(r'(?is)<br\s*/?>', '\n', h)
    h = re.sub(r'(?is)</p>', '\n\n', h)
    h = re.sub(r'(?is)</div>', '\n', h)
    h = re.sub(r'(?is)<[^>]+>', '', h)
    # 实体
    for a, b in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                 ('&quot;', '"'), ('&#39;', "'"), ('&mdash;', '——'),
                 ('&hellip;', '…'), ('&middot;', '·')]:
        h = h.replace(a, b)
    h = re.sub(r'[ \t]+\n', '\n', h)
    h = re.sub(r'\n{4,}', '\n\n\n', h)
    return h.strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    for slug, path, title in PAGES:
        url = BASE + path
        dest = os.path.join(OUT, slug + '.md')
        if os.path.exists(dest) and os.path.getsize(dest) > 2000:
            print('SKIP %-16s 已存在 %d bytes' % (slug, os.path.getsize(dest)))
            index.append((slug, title, url, os.path.getsize(dest)))
            continue
        try:
            html = fetch(url)
            text = strip_tags(html)
            head = ('# %s\n\n> 来源：%s\n> 抓取日：2026-10-08\n> 本地文件：docs/tiangong/%s.md\n\n---\n\n'
                    % (title, url, slug))
            with io.open(dest, 'w', encoding='utf-8') as f:
                f.write(head + text)
            n = os.path.getsize(dest)
            print('OK   %-16s %6d bytes  %s' % (slug, n, title))
            index.append((slug, title, url, n))
            time.sleep(0.8)
        except Exception as e:
            print('FAIL %-16s %s' % (slug, e))

    # 索引
    idx = ['# 天宫教程（tiangong.ligen.cn/docs）本地抓取索引\n',
           '> 抓取日：2026-10-08　共 %d 章\n' % len(index),
           '| # | 章节 | 本地文件 | 字节 |', '|---|---|---|---|']
    for i, (slug, title, url, n) in enumerate(index, 1):
        idx.append('| %02d | %s | [%s.md](%s.md) | %d |' % (i, title, slug, slug, n))
    with io.open(os.path.join(OUT, 'INDEX.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(idx) + '\n')
    print('\n索引已写入 docs/tiangong/INDEX.md')


if __name__ == '__main__':
    main()