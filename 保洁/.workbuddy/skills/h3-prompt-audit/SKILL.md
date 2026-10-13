# H3 提示词审计 skill

本 skill 提供提示词的自动审计功能，防止常见错误。使用方法：`python _check_lines.py <prompt.txt>`。

## 台词断句规则（第 31 项检查）

### 规则说明
台词句末**必须用句号+换行封死**，不能紧跟下一个说话人标记（如 `...。钱经理 (S1) speaks`）。否则模型会把说话人标记当成台词的一部分念出来。

### 官方规范依据
参考 H3 官方范本（`minimax-h3-prompt-guide/SKILL.md` 第 205 行）：
- 台词**就在句末**，后面不再跟任何标记
- 台词绝不能用引号包（引号会把字烧进画面）

### 错误示例
```text
钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 三楼包厢。钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 贵客丢了一只金耳钉。
```

### 正确写法
```text
钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 三楼包厢。
钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 贵客丢了一只金耳钉。
```

### 检查器实现
在 `_check_lines.py` 中添加第 31 项检查：
```python
# 31. 台词句末紧跟说话人标记
BAD = re.compile(r'(\\[Chinese\\][^\\[\\n]*?[。！])\\s*(?:钱经理|苏小满|小唐)\\s*\\(S\\d\\)\\s*speaks')
if BAD.search(text):
    bad.append("台词句末紧跟说话人标记：台词后必须用句号+换行封死，不能紧跟下一个说话人标记")
```

### 自检
检查器会自动用坏样本验证自身：
- 坏样本：`苏小满 (S2) speaks: [Chinese] 收台的时候，就你一个人在。 景宸大厦 万山大厦 the empty doorway 没关系`
- 如果坏样本没报红，检查器会报错，说明检查器本身坏了

## 其他检查项
- [第 30 项] 说话人标记必须明确指出是谁在说
- [第 29 项] 台词不能包含说话人标记
- [第 28 项] 否定句检查
- [第 27 项] 相邻两刀不是同一人的大特写
- [第 26 项] 镜头段无截断句子

## 使用示例
```bash
python _check_lines.py seg01_prompt.txt
```

如果返回 0，说明提示词通过所有检查；如果返回非 0，说明有错误。