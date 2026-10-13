# -*- coding: utf-8 -*-
"""_ai_taste.py 的已知答案样本 —— 上线前必须自证抓得住。

⛔ 铁律：校验器本身也会骗人。本文件是 _ai_taste.py 的验证基准。
用法： python _ai_taste_selfcheck.py

⛔ 判级口径：以 verdict 为准，不以分数为准。
   因为校验器有兜底规则「只要有block 级命中即判 block」，
   低分样本也会判 block —— 这是设计意图（X002 裁决第 4 条是禁项不是扣分项）。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ai_taste

# (样本名, 文本, 期望判级)
CASES = [
    ('坏样本1 · AI 腔密集',
     '她的眼神不禁闪烁，仿佛有什么在心底破碎。\n'
     '一丝寒意从脊背升起。\n'
     '他微微皱眉，缓缓开口——不是愤怒，是失望。\n'
     '【回忆】那年她也是这样——没有退路，没有选择。\n'
     '**苏小满**：你们不能搜我。\n',
     'block'),

    ('坏样本2 · 破折号+省略号+评书腔',
     '△ 她愣了一下——随即笑了。\n'
     '△ 空气仿佛凝固……\n'
     '△ 只见那少年立在门口，目光深沉。\n'
     '**他**：不是我要走，是你们不留。\n',
     'block'),

    ('坏样本3 · 超长台词',
     '**钱经理**（拍桌站起来指着她鼻子大声嚷）：'
     '三楼包厢贵客丢了一只金耳钉三万八你现在立刻把口袋翻出来给大家看清楚'
     '不然我就叫保安上来把你送出去。\n'
     '**苏小满**：不是我。\n',
     'block'),

    ('坏样本4 · 连续破折号（AI 最爱）',
     '△ 她抬头——看了看四周——又低下头。\n'
     '△ 他叹了口气——没有说话——转身走了。\n'
     '**苏小满**：随你。\n',
     'block'),

    ('好样本1 · X002 风格裁决样例',
     '△ 她盯着钱经理两秒。\n'
     '△ 把手伸进兜里。\n\n'
     '**钱经理**（逼近）：掏兜。自己掏，还是我喊保安。\n\n'
     '**苏小满**（后退半步）：你们不能搜我。\n\n'
     '**钱经理**：那就是心虚。\n\n'
     '△ 门口围了一圈人。没一个出声。\n',
     'pass'),

    ('好样本2 · X003 终版片段',
     '### 场次1-1：内景 万山大厦 物业办公室 中午\n\n'
     '△ 门被撞开。钱经理大步进来，身后的小唐，脸发白。\n\n'
     '**钱经理**（拍桌）：三楼包厢。贵客丢了一只金耳钉。三万八。\n\n'
     '**苏小满**：不是我。\n\n'
     '△ 钱经理转过头，斜了小唐一眼。\n\n'
     '**小唐**（保洁组同事，眼神躲闪）：钱经理。中午，我看见她往兜里塞东西。没看清。\n',
     'pass'),
]


def main():
    fails = 0
    print('=' * 68)
    print('_ai_taste.py 自检：校验器抓不抓得住已知答案')
    print('=' * 68)
    for name, text, expect in CASES:
        score, verdict, findings = _ai_taste.taste(text, verbose=False)
        ok = (verdict == expect)
        if not ok:
            fails += 1
        print('[%s] %-28s 期望 %-5s 实得 %-5s (score=%d)'
              % ('PASS' if ok else 'FAIL', name, expect, verdict, score))
        cats = sorted(set(c for _, c, _ in findings))
        print('        命中：%s' % ('、'.join(cats) if cats else '无'))
        if not ok:
            for lv, c, m in findings:
                print('          %s %s %s' % (lv, c, m))
    print('=' * 68)
    if fails:
        print('❌ %d 个样本判级错 —— 校验器被削弱了，不许上线' % fails)
        sys.exit(1)
    print('✅ %d 个样本全部按预期判级，校验器可用' % len(CASES))


if __name__ == '__main__':
    main()