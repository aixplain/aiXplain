---
sidebar_label: rlm
title: aixplain.v2.rlm
---

RLM (نموذج اللغة التكراري) لـ aiXplain SDK الإصدار الثاني.

يُنسِّق تحليل السياق الطويل عبر بيئة REPL معزولة تكرارية. يقوم
نموذج المُنسِّق بالتخطيط وكتابة شيفرة Python لتقسيم سياق كبير
واستكشافه؛ بينما يتولى نموذج العامل تحليل كل جزء عبر استدعاءات
``llm_query()`` المُحقَنة في جلسة البيئة المعزولة.

### كائنات RLMResult

```python
@dataclass_json

@dataclass(repr=False)
class RLMResult(Result)
```

<!-- ملاحظات الترجمة: أُبقي على RLM كاختصار مع ترجمة الاسم الكامل بين قوسين | kept EN: REPL — اختصار تقني معروف عالميًا | kept EN: Python — اسم لغة برمجة | kept EN: llm_query() — اسم دالة داخل كتلة شيفرة | kept EN: SDK — مصطلح محمي حسب التعليمات -->