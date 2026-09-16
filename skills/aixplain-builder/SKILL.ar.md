---
name: aixplain-builder
description: Build, run, and deploy anything on the aiXplain platform with the Python SDK and REST/JS/OpenAI-compatible APIs — AI agents and multi-agent teams, direct model inference (LLMs, speech-to-text/Whisper, translation, vision, embeddings), knowledge bases and RAG, tools and integrations (Slack, Gmail, databases, MCP, custom Python functions), runtime governance/inspectors, memory, and serverless deployment. Use this whenever the user mentions aiXplain (aixplain/aiXplain), the `aixplain` SDK, `from aixplain import Aixplain`, `aix.Agent`/`aix.Model`/`aix.Tool`, an aiXplain API key, Studio, the marketplace, or asks to build/run/deploy an agent, transcribe audio, run a model, set up RAG, or wire an integration on aiXplain — even when they don't name every component explicitly.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Builder

صمّم ونفّذ وانشر كل ما تدعمه حزمة تطوير aiXplain: الوكلاء وفِرَق الوكلاء، والاستدلال المباشر للنماذج، وقواعد المعرفة / RAG، والأدوات والتكاملات، وحوكمة زمن التشغيل، والذاكرة، وواجهات الوصول البرمجية. هذه المهارة هي المرجع الوحيد المعتمد — فكل مقتطف برمجي فيها تم التحقق منه مقابل **aiXplain SDK v0.2.48** (عميل `Aixplain` الموحّد من الإصدار v2) ومقابل الاستبطان الحيّ لحزمة التطوير.

## الجمهور والاكتفاء الذاتي

تُستخدم هذه المهارة نيابةً عن **غير المطورين والمطورين على حدٍّ سواء**. ولذلك:

- **أنجز العمل التقني بنفسك.** اكتب الشيفرة وشغّلها؛ ولا تُسلّم المستخدم تتبُّعًا للأخطاء. شخّص المشكلة وأصلحها وقدّم التقرير بلغة واضحة: ماذا حدث، وماذا فعلت، وما الخطوة التالية.
- **هذه المهارة مرجع معتمد.** استخدم مقتطفاتها كما هي مكتوبة؛ ولا توجّه المستخدم إلى GitHub أو إلى الشيفرة المصدرية لحزمة التطوير. وإذا فشل أحد المقتطفات هنا مقابل النسخة المثبّتة من حزمة التطوير، فالخطأ في المهارة لا عند المستخدم — أصلحها، ثم فكّر في اتباع عادة "الإبلاغ عن مشكلات aiXplain" أدناه.
- **ابدأ بعرض النتيجة ورابط Studio**، لا بتفاصيل التنفيذ. وأبقِ الشيفرة الكاملة متاحة للمطورين الراغبين فيها.

## التهيئة

ثبّت الحزمة أو حدّثها أولًا، ثم هيّئ العميل:

```bash
python3 -m pip install --upgrade aixplain
```

```python
import os
from aixplain import Aixplain

aix = Aixplain(api_key=os.environ["AIXPLAIN_API_KEY"])   # or Aixplain() if AIXPLAIN_API_KEY / TEAM_API_KEY is exported
```

إذا لم يكن `AIXPLAIN_API_KEY` مضبوطًا، فاطلبه من المستخدم (أو اطلب منه إضافته إلى ملف `.env`) — ويمكن الحصول عليه من https://app.aixplain.com/team/settings?tab=api-keys. تستهلك معظم العمليات أرصدة (الرصيد الواحد = دولار واحد)؛ فنبّه على ذلك قبل تشغيل أي عملية محاسَبة لمستخدم غير مطوّر.

## اختر الأداة المناسبة للمهمة

| ما يريده المستخدم… | ابنِ… | المرجع |
|---|---|---|
| الاستدلال لتحقيق هدف، واستدعاء الأدوات، والعمل متعدد الخطوات | **وكيل (Agent)** | `references/agents.md` |
| تنسيق عدة متخصصين / سير عمل | **فريق وكلاء (Team agent)** | `references/agents.md` |
| مجرد تشغيل نموذج مرة واحدة (نموذج لغوي، تفريغ صوتي، ترجمة، رؤية) | **استدعاء مباشر للنموذج** | `references/models.md` |
| الإجابة انطلاقًا من مستندات خاصة | **قاعدة معرفة + وكيل (RAG)** | `references/knowledge-memory.md` |
| الربط بـ Slack/Gmail/قاعدة بيانات/MCP، أو تغليف دالة Python | **أداة / تكامل** | `references/tools-integrations.md` |
| فرض سياسة في زمن التشغيل (السلامة، البيانات الشخصية، التنسيق) | **مفتّش (Inspector)** | `references/governance.md` |
| التذكّر عبر الأدوار أو الجلسات أو الوكلاء | **ذاكرة جلسة أو ذاكرة مشتركة** | `references/knowledge-memory.md` |
| استدعاء أصل منشور عبر HTTP/JS/عميل OpenAI | **واجهة REST / واجهة الوصول** | `references/deployment-access.md` |
| تحديث وكيل قائم/منشور، أو تصديره كشيفرة | **دورة حياة الوكيل** | `references/agents.md` |
| حالة محادثة متعددة الأدوار | **جلسة (Session)** | `references/agents.md` |
| تجميع تعليمات قابلة لإعادة الاستخدام، أو تشغيل وكيل وفق جدول/حدث | **مهارة / مُشغِّل (Trigger)** | `references/agents.md` |
| قياس جودة الوكيل أو تسجيلها دون اتصال | **تقييم + مقياس (Eval + Metric)** | `references/evaluation.md` |
| وصفة جاهزة للتكييف | — | `references/patterns.md` |

اقرأ الملف المرجعي ذا الصلة قبل كتابة شيفرة في ذلك المجال — فهي تحتوي على التواقيع والمعرّفات الدقيقة والمزالق.

> ### ⚠️ ما نُقل أو أُزيل في SDK 0.2.48 — لا تكتب هذه الصيغ
> الشيفرة السابقة للإصدار 0.2.48 (وبعض الوثائق المنشورة إلى الآن) تستخدم صيغًا صارت تفشل، اثنتان منها تفشل **بصمت**:
> - `from aixplain.v2.inspector import InspectorAction, EvaluatorConfig, …` → **أُزيلت من v2**. ابنِ الضوابط الوقائية بالصيغة `aix.Inspector(action="abort", metric={...})` باستخدام سلاسل نصية وقواميس عادية. راجع `references/governance.md`.
> - `from aixplain.v2.file import FileUploader` → نُقلت إلى **`aixplain.v2.upload_utils`**.
> - `model.inputs.get_required_parameters() / get_all_parameters() / reset_parameter() / reset_all_parameters()` → أُعيدت تسميتها إلى `.required` و `dict(.items())` و `.reset(k)` و `.reset()`.
> - 🔇 `agent.max_iterations = N` بعد الإنشاء **بلا أي أثر** — اضبط `agent.budget.max_iterations = N` بدلًا منها.
> - 🔇 `generate_session_id()` / `create_session()` **لم تعودا موجودتين**، و `session_id=` المُمرَّرة إلى `run()` **تُحذف بصمت** (فتحصل على تشغيل بلا حالة، ودون أي خطأ). استخدم `aix.Session` — راجع `references/agents.md`.

> **غير متوفر في حزمة تطوير v2:** خطوط الأنابيب (pipelines)، والضبط الدقيق (fine-tuning)، وقياس الأداء (benchmarking)، ومجموعات البيانات/المدوّنات. هذه متاحة في الإصدار القديم v1 فقط أو داخل Studio فقط. راجع `references/deployment-access.md § What the v2 SDK does NOT cover`. ولسير العمل متعدد الخطوات في v2، استخدم **فريق وكلاء**.

## سير العمل لبناء وكيل

1. **خطّط، ثم أكّد.** اذكر اسم الوكيل ووصفه وتعليماته، والأدوات/التكاملات المستخدمة، وما إذا كان وكيلًا مفردًا أم فريقًا. وانتظر الموافقة قبل بناء أي شيء يستهلك رصيدًا.
2. **ابحث قبل أن تُثبّت القيم في الشيفرة.** `aix.Tool.search(...)` و `aix.Model.search(...)` و `aix.Integration.search()["results"]`. ولا تقل أبدًا "غير متوفر" قبل البحث. قد تتغير المعرّفات الواردة في الجداول المرجعية — فإذا أعاد أحدها 404، فابحث بالاسم.
3. **أنشئ الأدوات وحدّد نطاقها.** لكل أداة، ضيّق `allowed_actions` إلى الحد الأدنى الذي تحتاجه المهمة — فالقيمة الافتراضية (جميع الإجراءات) تمنح الوكيل صلاحيات زائدة وتضر باستدلاله. راجع `references/tools-integrations.md`.
4. **ابنِ الوكيل.** احذف `llm` ما لم يطلب المستخدم نموذجًا بعينه (فالنموذج الافتراضي للمنصة جيد). واضبط `output_format`، وكذلك `expected_output` في حالة JSON.
5. **الحفظ = النشر.** `agent.save()` (أو `team.save(save_subcomponents=True)`) ينقل الأصل من `DRAFT → ONBOARDED` ويمنحه نقطة نهاية دائمة. ولا توجد دالة `deploy()` منفصلة.
6. **شغّل وتحقّق.** `agent.run(query=...)`، ثم اقرأ `.data.output`. وافحص `.data.steps` إذا كان سلوكه غير سليم.
7. **شارك روابط Studio** ليتمكن المستخدم من التحرير والمراقبة بصريًا:
   - أداة البناء البصرية: `https://app.aixplain.com/studio`
   - التحليلات: `https://app.aixplain.com/dashboard`
   (وحّدت aiXplain خدماتها على النطاق `app.aixplain.com` — فمضيفا `studio.`/`console.` والروابط العميقة الخاصة بكل وكيل مثل `/build/<ID>/schema` لم تعد موجودة. أعطِ المستخدم **معرّف** الوكيل إلى جانب الرابط.)

## أعراف تسري في كل مكان

- **تشغيل مرن:** التشغيل المتزامن عبر `.run(...)`؛ وغير المتزامن عبر `.run_async(...)` ثم `.sync_poll(url)` (يحجب التنفيذ ويعيد البنية نفسها) أو عبر `.poll(url)` يدويًا حتى `.completed`.
- **قراءة النتائج:** الوكلاء ← `response.data.output` و `.status` و `.data.steps` و `.data.execution_stats`؛ النماذج ← `response.data` و `.status` و `.usage` و `._raw_data`.
- **أسماء فريدة:** إذا أطلقت `save()` الخطأ `name_already_exists`، فاسأل المستخدم: أيحدّث الأصل القائم أم يُنشئ أصلًا باسم جديد؟ وإلحاق `int(time.time())` بالاسم يُبقي العروض التوضيحية فريدة.
- **لا تختلق بيانات اعتماد أو معرّفات.** اطلب من المستخدم المدخلات المطلوبة (روابط قواعد البيانات، رموز واجهات برمجة التطبيقات). ولا تستخدم القيم النائبة إلا إذا كانت موسومة بوضوح.

## تمرير الملفات المحلية إلى aiXplain

تستقبل النماذج والوكلاء والأدوات **روابط URL**، لا مسارات محلية. ارفع الملف أولًا ثم مرّر الرابط المُعاد:

```python
from aixplain.v2.upload_utils import FileUploader
url = FileUploader(api_key=os.environ["AIXPLAIN_API_KEY"]).upload(
    "/path/to/file.mp3", is_temp=True, return_download_link=True)   # download link, not raw s3://
```

استخدم `return_download_link=True` ليكون الرابط قابلًا للفتح من المتصفح. حدود الحجم: الصوت 50 ميجابايت، الصور/المستندات 25 ميجابايت، الفيديو/قواعد البيانات 300 ميجابايت. (بالنسبة إلى مخرجات `.html`/`.zip` قد يُخطئ كاشف نوع MIME في حزمة التطوير في تحديد الامتداد — فاضبط نوع المحتوى الصحيح عندما يكون ذلك مهمًا.)

## الإبلاغ عن مشكلات aiXplain (عادة)

عندما تصادف سلوكًا شاذًا سببه **aiXplain** بوضوح (لا شيفرة المستخدم أو إعداداته) — إجراء مُعلَن عنه يفشل دائمًا، أو معامل موثّق يتجاهله الخادم الخلفي، أو موصّل يطلب صلاحيات أقل من اللازم — فاعرض فتح مشكلة على https://github.com/aixplain/aiXplain. أعِد إنتاج المشكلة أولًا للتأكد من أن السبب من جانب aiXplain، ثم صُغ العنوان والمحتوى، و**احصل على موافقة المستخدم قبل النشر** (فالمستودع عام). أخفِ مفاتيح واجهات برمجة التطبيقات وعناوين البريد الإلكتروني ومعرّفات الأصول/الحسابات؛ واجعل خطوات إعادة الإنتاج عامة. وأدرِج إصدار حزمة التطوير، ونوع الأصل، وخطوات إعادة إنتاج مختصرة، والسلوك المتوقع مقابل السلوك الفعلي.

## روابط خارجية

- الوثائق: https://docs.aixplain.com · Studio: https://app.aixplain.com/studio · لوحة المعلومات: https://app.aixplain.com/dashboard · المفاتيح/الفوترة: https://app.aixplain.com/team/settings · الأسعار: https://aixplain.com/pricing
