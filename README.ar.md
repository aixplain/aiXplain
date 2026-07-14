<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/aixplain-logo-light.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/aixplain-logo-dark.png">
    <img src="docs/assets/aixplain-logo-dark.png" alt="aiXplain" width="520">
  </picture>
</p>

<h1 align="center">aiXplain SDK</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-2ea44f?style=flat-square" alt="الرخصة"></a>
  <a href="https://studio.aixplain.com/browse"><img src="https://img.shields.io/badge/Marketplace-900%2B%20models%20%26%20tools-0b74de?style=flat-square" alt="حجم السوق"></a>
  <a href="https://console.aixplain.com/settings/keys"><img src="https://img.shields.io/badge/%F0%9F%94%91%20PAYG%20API%20key-Console-0b74de?style=flat-square" alt="مفتاح API بنظام الدفع حسب الاستخدام"></a>
  <a href="https://discord.gg/aixplain"><img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**أنشئ وانشر وأدِر وكلاء الذكاء الاصطناعي المستقلين لعمليات أعمالك.**

يوفر aiXplain SDK واجهات برمجة تطبيقات Python وREST للوكلاء الذين يخططون، ويستخدمون الأدوات، ويستدعون النماذج والبيانات، وينفذون التعليمات البرمجية، ويتكيفون أثناء التشغيل. كما يعمل بشكل أصيل مع وكلاء البرمجة وبيئات التطوير المتوافقة مع MCP.

> **كن مؤسسة تعتمد الوكلاء أولاً**
>
> مصمم لعمليات الأعمال: مستقل، محكوم، متوافق مع MCP، ومبني لإدارة السياق. مساعدك التفاعلي بالذكاء الاصطناعي على بُعد [نقرة واحدة](https://auth.aixplain.com/).
>
> _نحن ندير أعمالنا باستخدام وكلاء aiXplain، ونستخدمهم عبر المنتجات وتطوير الأعمال والتسويق._

## لماذا aiXplain

- **حلقة تشغيل مستقلة** — يخطط، ويستدعي الأدوات والنماذج، ويراجع، ويستمر دون مخططات انسياب ثابتة.
- **تنفيذ متعدد الوكلاء** — يفوّض العمل إلى وكلاء فرعيين متخصصين أثناء التشغيل.
- **الحوكمة افتراضيًا** — التحكم في الوصول وإنفاذ السياسات أثناء كل تشغيل.
- **الرصد والمراقبة في بيئة الإنتاج** — فحص التتبعات على مستوى الخطوات، واستدعاءات الأدوات، والنتائج لأغراض التصحيح.
- **قابلية نقل النماذج والأدوات** — استبدل الأصول دون إعادة كتابة شيفرة الربط.
- **وصول أصيل عبر MCP** — اربط عملاء MCP بـ [أكثر من 900 أصل مستضاف على aiXplain](#mcp-servers) بمفتاح API واحد بنظام الدفع حسب الاستخدام.
- **نشر مرن** — شغّل نفس تعريف الوكيل بدون خادم أو في بيئة خاصة.

| | aiXplain SDK | أُطر عمل الوكلاء الأخرى |
|---|---|---|
| الحوكمة | التحكم في الوصول وإنفاذ السياسات مدمجان | عادةً شيفرة مخصصة أو حواجز حماية خارجية |
| النماذج والأدوات | أكثر من 900 نموذج وأداة بمفتاح API واحد | إعداد لكل مزوّد على حدة |
| النشر | سحابي (فوري) أو محلي | عادةً بيئة تشغيل وبنية تحتية يتم تجميعها ذاتيًا |
| الرصد والمراقبة | تتبعات ولوحات معلومات مدمجة | يختلف حسب إطار العمل |
| سير عمل وكلاء البرمجة | يعمل بشكل أصيل مع وكلاء البرمجة وبيئات التطوير المتوافقة مع MCP | عادةً ليس هدف سير عمل من الدرجة الأولى |

## AgenticOS

AgenticOS هو منصة التشغيل المحمولة التي تقف خلف وكلاء aiXplain. يتولى AgentEngine تنسيق التخطيط والتنفيذ والتفويض للوكلاء المستقلين. يربط AssetServing الوكلاء بالنماذج والأدوات والبيانات عبر طبقة تشغيل محكومة. يلتقط نظام الرصد والمراقبة التتبعات والمقاييس والمراقبة لكل تشغيل إنتاجي عبر عمليات النشر السحابية (الفورية) والمحلية.

<div align="center">
  <img src="docs/assets/aixplain-agentic-os-architecture.svg" alt="بنية aiXplain AgenticOS" title="aiXplain"/>
</div>

---

## سوق خوادم MCP

<!-- ملاحظات الترجمة: [أُبقي على AgenticOS وAgentEngine وAssetServing كأسماء علامة تجارية دون ترجمة] | [تُرجم Governance→الحوكمة وObservability→الرصد والمراقبة وSubagents→وكلاء فرعيين حسب المسرد] | [kept EN: MCP, SDK, API, REST, Python, Discord — أسماء تقنية وعلامات تجارية لا تُترجم] | [تُرجم Marketplace→السوق في العنوان وMarketplace size→حجم السوق في alt text] -->
