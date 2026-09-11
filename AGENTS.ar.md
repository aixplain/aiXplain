# aiXplain SDK

حزمة SDK بلغة Python لبناء ونشر وحوكمة وكلاء الذكاء الاصطناعي على منصة aiXplain.

- الرخصة: Apache 2.0
- Python: >=3.9, <4
- تهيئة الحزمة: `pyproject.toml` (PEP 621, setuptools backend)

---

## الإعداد والأوامر

```bash
# Install (development)
pip install -e .

# Install (production)
pip install aixplain

# Install with test dependencies
pip install -e ".[test]"
```

### البيئة

قم بتعيين `AIXPLAIN_API_KEY` (مطلوب) قبل استخدام SDK. يُشير `BACKEND_URL` افتراضيًا إلى بيئة الإنتاج (`https://platform-api.aixplain.com`).

### الاختبار

```bash
# Unit tests
python -m pytest tests/unit

# Functional / integration tests
python -m pytest tests/functional

# Unit tests with coverage (same as pre-commit hook)
coverage run --source=. -m pytest tests/unit
```

### التدقيق والتنسيق

Ruff هو أداة التدقيق والتنسيق الوحيدة.

```bash
ruff check .            # Lint
ruff check --fix .      # Lint with auto-fix
ruff format .           # Format
```

### توليد الشيفرة

تُولَّد ثلاث وحدات بواسطة `generate.py` ولا يجوز تعديلها يدويًا: `aixplain/v1/enums/generated_enums.py` (تعدادات `Function` و`Supplier` و`Language` و`License` الخاصة بـ `v1`) و`aixplain/v1/modules/pipeline/pipeline.py` (فئات عقد خطوط الأنابيب في `v1`) و`aixplain/v2/enums_include.py` (وحدة إعادة تصدير لتعدادات `v1` لا يستوردها أي شيء في `v2`). المولّد خاص بـ `v1` فقط: تعدادات `v2` تُصان يدويًا في `aixplain/v2/enums.py`، ويستورد `aixplain/v2/__init__.py` منها، ولا يحمّل `import aixplain` أي وحدة من `v1` على الإطلاق (يؤكد ذلك `tests/unit/test_v1_deprecation_warning.py`). لذا فإن تحديث ملفات البيانات يغيّر ما يعرضه `v1`، لا ما يقبله `Aixplain().Model.search(suppliers=...)`. فجوة معروفة: يضم `Supplier` في `v2` سبعة أعضاء ويتخلف عن كتالوج الخادم الخلفي، بما في ذلك المورّدون الأربعة الذين أضافهم تحديث 2026-09-08 إلى `v1` (`ALIBABA_CLOUD` و`ANTHROPIC` و`BYTEDANCE` و`OPENROUTER`).

```bash
python generate.py                # render (default): offline, no credential
python generate.py render --check # exit non-zero if the committed modules drifted
python generate.py fetch          # refresh tools/generator/fixtures/ (network + API key)
```

تقرأ خطوة العرض (render) ملفات البيانات المثبَّتة في `tools/generator/fixtures/` فقط، لذا فهي حتمية ولا تحتاج إلى خادم خلفي ولا إلى مفتاح؛ وتشغّل مهمة `generator-drift` في CI الأمر `python generate.py render --check` وتفشل إذا اختلفت الوحدات المثبَّتة عن عرض جديد. خطوة `fetch` هي الوحيدة التي تتصل بالشبكة وتُشغَّل يدويًا؛ ترفض أي `BACKEND_URL` غير الإنتاج ما لم يُمرَّر `--allow-nonprod`، وتسجّل المضيف الذي التقطت منه في `tools/generator/fixtures/provenance.json`، ويؤكد اختبار أنه مضيف الإنتاج — راجع `tools/generator/fixtures/README.md` لسير عمل التحديث ولماذا تُلتقط ملفات البيانات من الإنتاج.

تُصدَر قيم الخادم الخلفي كقيم Python حرفية، ويُتحقق من كل قيمة تُستخدم كمعرّف، لذا فإن أي قيمة لا يمكن عرضها بأمان تُفشل خطوة العرض بوضوح بدلًا من تشويهها.

### Pre-commit

```bash
pre-commit install
```

تُنفَّذ الخطافات التالية: trailing-whitespace، وend-of-file-fixer، وcheck-merge-conflict، وcheck-added-large-files، وruff (تدقيق + تنسيق)، واختبارات الوحدة.

---

## اصطلاحات كتابة الشيفرة

- **طول السطر**: 120 حرفًا.
- **المسافة البادئة**: 4 مسافات.
- **علامات الاقتباس**: علامات اقتباس مزدوجة للسلاسل النصية.
- **سلاسل التوثيق**: نمط Google (يُفرض بواسطة ruff `pydocstyle`). لا تُفرض قواعد سلاسل التوثيق في `tests/`.
- **تلميحات الأنواع**: مطلوبة لجميع الدوال العامة. استخدم `typing` (`Optional`، `Union`، `List`، `Dict`، `TypeVar`، generics).
- **التسمية**: `PascalCase` للفئات، و`snake_case` للدوال والطرق، و`UPPER_SNAKE_CASE` للثوابت.
- **الاستثناءات**: استخدم التسلسل الهرمي المخصص في `aixplain/exceptions/` (`AixplainBaseException` والفئات الفرعية). لا ترفع `Exception` مجردًا أبدًا.
- **الاستيرادات**: استخدم `from __future__ import annotations` أو حراسات `TYPE_CHECKING` لكسر الاستيرادات الدائرية. استخدم الاستيرادات المشروطة للتبعيات الاختيارية.
- **التحقق**: Pydantic للتحقق أثناء التشغيل. `dataclasses-json` للتسلسل إلى JSON.
- **ترويسة الرخصة**: أضف ترويسة رخصة Apache 2.0 في أعلى كل ملف مصدري.

---

## البنية المعمارية

### واجهة API المزدوجة

يوفر SDK طبقتي API تُصان بالتوازي:

| الجانب | V1 | V2 |
|---|---|---|
| النمط | نمط المصنع مع طرق الفئة | قائم على الموارد مع dataclasses وmixins |
| نقطة الدخول | `aixplain.factories.*Factory` | `aixplain.v2.*` |
| التسلسل | معالجة يدوية للقواميس | `dataclasses-json` (camelCase من API إلى snake_case في Python) |

> **V1 مهملة وستُزال في 1 فبراير 2027** (`2027-02-01`). يُصدر استيراد أي شيفرة من v1 — سواء
> `aixplain.v1` مباشرةً أو أحد المسارات القديمة مثل `aixplain.modules` — تحذير
> `aixplain._compat.AixplainV1DeprecationWarning` مرة واحدة لكل عملية تشغيل. التاريخ معرَّف في موضع
> واحد فقط هو `aixplain._compat.V1_REMOVAL_DATE`، ويفشل الاختبار
> `tests/unit/test_v1_deprecation_docs.py` إذا خالفه أي ملف توثيق مكتوب يدويًا؛ لذا عدّل الثابت أولًا
> ثم التوثيق، وليس العكس. راجع [`MIGRATION.md`](MIGRATION.md) للاطلاع على مقابل كل مصنع في v2،
> بما يشمل المصانع الثمانية التي **لا يوجد لها مقابل في v2 بعد** وتُعدّ شرطًا لإتمام الإزالة.
>
> لا يعني ذلك السماح بحذف شيفرة v1 — راجع قواعد V1 والتوافق العكسي.

### تخطيط الحزمة

| المجلد | الغرض |
|---|---|
| `aixplain/modules/` | كائنات المجال (Agent، Model، Pipeline، TeamAgent، أدوات) |
| `aixplain/factories/` | فئات المصنع V1 لإنشاء الموارد وإدارتها |
| `aixplain/v2/` | فئات الموارد V2 مع mixins ونظام الخطافات |
| `aixplain/enums/` | التعدادات (Function، Supplier، Language، Status، إلخ) |
| `aixplain/exceptions/` | التسلسل الهرمي المخصص للاستثناءات مع رموز الأخطاء والفئات |
| `aixplain/utils/` | أدوات مساعدة مشتركة (تهيئة، طلبات HTTP، أدوات الملفات، ذاكرة مؤقتة) |
| `aixplain/base/` | المعاملات الأساسية |
| `aixplain/decorators/` | المزخرفات (مثل: مدقق مفتاح API) |
| `aixplain/processes/` | سير عمل إدراج البيانات |

### أنماط التصميم الرئيسية

- **المصنع**: `AgentFactory`، و`ModelFactory`، و`PipelineFactory`، إلخ لإنشاء الموارد (V1).
- **Mixin**: `SearchResourceMixin`، و`GetResourceMixin`، و`RunnableResourceMixin`، و`ToolableMixin` لسلوك قابل للتركيب (V2).
- **الخطاف**: خطافات دورة الحياة `before_save` / `after_save` على الموارد (V2).
- **الباني**: طرق `build_run_payload()` / `build_save_payload()`.
- **الاستراتيجية**: مسارات تنفيذ متزامنة، وغير متزامنة، وتدفقية.
- **بيانات التشغيل**: تحمل حمولات تشغيل الوكلاء كائن `metaData` من `aixplain.utils.user_info_utils.build_run_metadata()` (استعلام `ipinfo.io` واحد مخزَّن مؤقتًا). إذا غيّرت ما يُرسل، فحدّث [docs/run-metadata.ar.md](docs/run-metadata.ar.md) — يفرض ذلك `tests/unit/test_run_metadata_docs.py`.

---

## الاختبار

- **إطار العمل**: pytest (مُهيَّأ في `pytest.ini`، `testpaths = tests`).
- **اختبارات الوحدة**: `tests/unit/` -- سريعة، مُحاكاة، بدون اتصالات شبكية.
- **الاختبارات الوظيفية**: `tests/functional/` -- اختبارات تكامل ضد خدمات حقيقية أو مرحلية.
- **بيانات المحاكاة**: `tests/mock_responses/` -- ملفات JSON ثابتة لاستجابات API.
- **CI**: تُشغِّل GitHub Actions ستة عشر مجموعة اختبار متوازية (unit، agent، model، pipeline، v2، finetune، إلخ) على Python 3.9 بمهلة 45 دقيقة.
- **سلاسل التوثيق في الاختبارات**: غير مُفرضة (يتجاهل ruff قواعد `D` لملفات `tests/**/*.py`).

---

## مسرد مصطلحات المجال

| المصطلح | الوصف |
|---|---|
| **وكيل (Agent)** | كيان ذكاء اصطناعي مستقل يستدل ويخطط ويستخدم الأدوات لإنجاز المهام. |
| **نموذج (Model)** | نموذج ذكاء اصطناعي (LLM، أو أداة مساعدة، أو فهرس) يمكن الوصول إليه عبر المنصة. |
| **خط معالجة (Pipeline)** | سير عمل تسلسلي يربط النماذج والأدوات بترتيب ثابت. |
| **وكيل الفريق (TeamAgent)** | نظام متعدد الوكلاء حيث يتعاون عدة وكلاء معًا. |
| **أداة (Tool)** | قدرة يمكن للوكيل استدعاؤها (أداة نموذج، أداة خط معالجة، مُفسِّر Python، SQL، إلخ). |
| **وكيل مصغر (Microagent)** | مكونات متخصصة مدمجة: **Mentalist** (التخطيط)، **Orchestrator** (التوجيه)، **مراقب (Inspector)** (التحقق)، **Bodyguard** (الأمان)، **Responder** (التنسيق). |
| **وكيل وصفي (Meta-agent)** | وكلاء تُحسِّن وكلاء آخرين. يراقب **Evolver** مؤشرات الأداء الرئيسية ويُحسِّن السلوك. |
| **التنسيق الثابت** | تنفيذ حتمي بترتيب `AgentTask` محدد مسبقًا. |
| **التنسيق الديناميكي** | تنفيذ تكيفي حيث يُولِّد Mentalist الخطة أثناء التشغيل (الافتراضي). |

<!-- ملاحظات الترجمة: أُبقيت أسماء الأنماط التصميمية (Factory, Mixin, Hook, Builder, Strategy) كمصطلحات مرجعية مع ترجمتها | kept EN: Mentalist, Orchestrator, Bodyguard, Responder, Evolver — أسماء مكونات خاصة بالمنصة | kept EN: dataclasses-json, PascalCase, snake_case, UPPER_SNAKE_CASE — مصطلحات برمجية معيارية | kept EN: ruff, pytest, Pydantic, GitHub Actions — أسماء أدوات وعلامات تجارية -->
