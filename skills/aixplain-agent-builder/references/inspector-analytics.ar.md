# عقد تحليلات المراقب

أنماط سياسة المراقب، ومخطط التحليلات، ومتطلبات التحقق.
مرتبط من المهارة الرئيسية — يُرجع إليه عند إضافة مراقبين.

---

## إرشادات السياسة

- يُفضَّل استخدام `InspectorPolicy.ABORT` لانتهاكات السياسة الصارمة.
- يُفضَّل استخدام `InspectorPolicy.ADAPTIVE` لمشكلات الجودة القابلة للاسترداد.
- اضبط مراقبي `RERUN` مع تحديد `max_retries` و`on_exhaust` بشكل صريح.
- لعمليات النشر القائمة: استرجع `TeamAgent`، وعدّل `inspectors`/`inspector_targets`، ثم استدعِ `.save()`.

---

## دلالات الحالة

أبقِ حالة التشغيل في aiXplain كما هي: `IN_PROGRESS | SUCCESS | FAILED`.
لا تُحمِّل `FAILED` معنى حظر السياسة.

### تعداد حالة الحوكمة (على مستوى التطبيق)

| الحالة | المعنى |
|--------|--------|
| `ALLOWED` | نجح المراقب، تنفيذ طبيعي |
| `BLOCKED_BY_INSPECTOR` | أوقف المراقب التشغيل |
| `REQUIRES_HUMAN_REVIEW` | وضع المراقب علامة للمراجعة اليدوية |
| `INSUFFICIENT_AUTH_CONTEXT` | سياق الدور/النطاق مفقود |
| `RESTRICTED_SCOPE` | الطلب يتجاوز النطاق المسموح |

### قيم إجراءات المراقب

قيم SDK: `continue | rerun | abort`.

إذا استخدمت واجهة المنتج `CONT|RERUN|ABORT|EDIT`، فقم بالربط صراحةً:
- `CONT` -> `continue`
- `RERUN` -> `rerun`
- `ABORT` -> `abort`
- `EDIT` -> امتداد مشتق من التطبيق (ليس إجراء مراقب أصلي)

---

## حقول حدث المراقب لكل تشغيل

الحد الأدنى من الحقول المطلوب التقاطها لكل تقييم مراقب:

| الحقل | الوصف |
|-------|-------|
| `run_id` | معرّف التشغيل الأصلي |
| `inspector_event_id` | معرّف الحدث الفريد |
| `inspector_name` | اسم المراقب |
| `target` | `INPUT | STEPS | OUTPUT` |
| `decision` | `continue | rerun | abort` |
| `reason_code` | سبب قابل للقراءة الآلية |
| `severity` | `LOW | MEDIUM | HIGH | CRITICAL` |
| `final_effect` | `none | rerouted | blocked` |
| `timestamp_start_utc` | بداية التقييم |
| `timestamp_end_utc` | نهاية التقييم |
| `latency_ms` | مدة التقييم |
| `retries_used` | عدد المحاولات المستهلكة |
| `governance_status` | حالة الحوكمة على مستوى التطبيق |
| `access_policy` | كائن سياسة قابل للقيمة الفارغة |
| `approval_status` | `DRAFT | PENDING_REVIEW | APPROVED | REJECTED` (قابل للقيمة الفارغة) |
| `run_total_latency_ms` | المدة الإجمالية للتشغيل |
| `token_or_credit_usage` | قابل للقيمة الفارغة؛ يُرجع لمستوى التشغيل |

---

## قواعد الربط المطلوبة

| القرار | حالة الحوكمة | التأثير النهائي |
|--------|-------------|----------------|
| `abort` | `BLOCKED_BY_INSPECTOR` | `blocked` |
| `rerun` (محاولة ناجحة) | — | `rerouted` |
| `continue` (بدون تدخل) | — | `none` |

يمكن لحظر السياسة أن يُعيد حالة تشغيل `SUCCESS` مع مخرج رفض آمن — يُعامَل كحظر حوكمة، وليس فشل وقت التشغيل.

---

## مصفوفة التحقق بعد التغيير (إلزامية)

بعد إضافة/تحديث المراقبين، شغّل 3 موجِّهات بالضبط:

| الاختبار | السلوك المتوقع |
|----------|---------------|
| **موجِّه مسموح** | مسار المتابعة، إجابة طبيعية متوافقة |
| **موجِّه مرفوض** | حظر/رفض، بدون بيانات/إجراءات مقيدة |
| **موجِّه غامض** | معالجة تحفظية (رفض أو طلب توضيح) |

لكل حالة التقط:
- `prompt`
- `expected_action`
- `observed_run_status`
- `observed_governance_status`
- `observed_output_summary`
- `pass_fail`

---

## بطاقات مؤشرات الأداء الرئيسية لكل مراقب

عند اختيار وكيل، اعرض هذه المقاييس لكل مراقب:

| المقياس | الوصف |
|---------|-------|
| `inspector_id` | المعرّف الفريد |
| `inspector_name` | اسم العرض |
| `inspector_desc` | الوصف |
| `target` | مدخل/خطوات/مخرج |
| `policy/action_mode` | نوع السياسة |
| `severity_model` | تصنيف الخطورة |
| `evaluation_count` | تقييمات المراقب (وليس تشغيلات الوكيل) |
| `pass_rate_pct` | معدل النجاح (صيغة صريحة مطلوبة) |
| `block_rate_pct` | معدل نتائج الإيقاف |
| `rerun_rate_pct` | معدل إعادة التشغيل |
| `edit_rate_pct` | معدل التعديل (إن وُجد) |
| `avg_reruns_per_evaluation` | متوسط المحاولات |
| `retry_exhausted_count` | عدد المحاولات المستنفدة |
| `avg_latency_ms` | متوسط زمن التقييم |
| `p95_latency_ms` | زمن الاستجابة عند المئين 95 |
| `avg_credits_per_evaluation` | تكلفة الرصيد لكل تقييم |
| `last_config_change_at` | طابع زمني لآخر تعديل |
| `last_config_change_by` | آخر مُعدِّل |
| `config_version` | إصدار التهيئة |
| `drift_7d_vs_30d_pass_delta` | انحراف معدل النجاح: 7 أيام مقابل 30 يومًا |
| `drift_7d_vs_30d_block_delta` | انحراف معدل الحظر: 7 أيام مقابل 30 يومًا |

### مخطط الاتجاه (يومي)

تتبّع لكل مراقب: `pass_count`، `block_count`، `rerun_count`، `override_count`.

<!-- ملاحظات الترجمة: Inspector→مراقب (matching glossary term) | Policy→سياسة | Run→تشغيل | kept EN: all inline code values, enum values, field names, SDK, aiXplain — as per rules | Prompt→موجِّه | Agent→وكيل | Governance→الحوكمة | nullable rendered as قابل للقيمة الفارغة for clarity -->