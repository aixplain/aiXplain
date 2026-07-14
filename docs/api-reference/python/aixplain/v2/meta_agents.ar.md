---
sidebar_label: meta_agents
title: aixplain.v2.meta_agents
---

وحدة الوكلاء الفوقيين - المُنقّح وأدوات الوكلاء الفوقيين المساعدة الأخرى.

توفر هذه الوحدة وكلاء فوقيين يعملون فوق وكلاء آخرين،
مثل المُنقّح (Debugger) لتحليل استجابات الوكيل.

مثال على الاستخدام:
    from aixplain import Aixplain

    # تهيئة العميل
    aix = Aixplain("<api_key>")

    # الاستخدام المستقل
    debugger = aix.Debugger()
    result = debugger.run("Analyze this agent output: ...")

    # أو باستخدام موجِّه مخصص
    result = debugger.run(content="...", prompt="Focus on error handling")

    # من استجابة الوكيل (متسلسل)
    agent = aix.Agent.get("my_agent_id")
    response = agent.run("Hello!")
    debug_result = response.debug()  # يستخدم الموجِّه الافتراضي
    debug_result = response.debug("Why did it take so long?")  # موجِّه مخصص

### كائنات DebugResult

```python
@dataclass_json

@dataclass
class DebugResult(Result)
```

<!-- ملاحظات الترجمة: استخدام "الوكلاء الفوقيين" لـ meta agents كونها تعمل فوق وكلاء آخرين | kept EN: Debugger — اسم فئة برمجية | kept EN: DebugResult — اسم فئة برمجية | kept EN: Result — اسم فئة برمجية | الحفاظ على كتل الشيفرة كما هي دون ترجمة | ترجمة التعليقات داخل الشيفرة التوضيحية فقط عند كونها وصفية -->