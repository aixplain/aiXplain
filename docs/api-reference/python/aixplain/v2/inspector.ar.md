---
sidebar_label: inspector
title: aixplain.v2.inspector
---

وحدة المراقب لواجهة API الإصدار v2 - فحص وكيل الفريق والتحقق من صحته.

توفر هذه الوحدة وظائف المراقب للتحقق من صحة عمليات وكيل الفريق
في مراحل مختلفة (المدخل، الخطوات، المخرج) باستخدام سياسات مخصصة.

### كائنات InspectorTarget

```python
class InspectorTarget(str, Enum)
```

<!-- ملاحظات الترجمة: [Inspector→مراقب per glossary] | [Team agent→وكيل الفريق per glossary] | [policies→سياسات per glossary] | [kept EN: InspectorTarget — class name] | [kept EN: API, Enum — technical terms never translated] -->