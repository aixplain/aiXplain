"""Which request-body keys platform-backend actually reads, per endpoint (ENG-3782, layer 1).

platform-backend's global ValidationPipe neither whitelists nor rejects
unknown keys, so a key the SDK sends that no service reads is accepted with a
200 and silently does nothing. BUG-1092 and #1146 were exactly that (sort
fields the backend ignored), found only because a live test happened to check
the order. These sets are the keys each paginate service reads.

Source: platform-backend ``development`` @ 91ed4d7bf (2026-10-16).
"""

# src/model/controllers/model.v2.controller.ts:83-89 -> ModelService.paginateModels
# (args.* reads), input class ModelPaginationInput (src/model/inputs/index.ts:18).
MODEL_PAGINATE = frozenset(
    {
        "q",
        "saved",
        "functions",
        "dataRetentionModes",
        "suppliers",
        "vendors",
        "categories",
        "hosts",
        "developers",
        "path",
        "sort",
        "status",
        "pageNumber",
        "pageSize",
    }
)

# src/model/controllers/model.tool.v2.controller.ts -> ModelToolPaginationInput (src/model/inputs/index.ts:112).
TOOL_PAGINATE = frozenset(
    {
        "q",
        "path",
        "saved",
        "suppliers",
        "categories",
        "vendors",
        "developers",
        "hosts",
        "sort",
        "status",
        "provider",
        "pageNumber",
        "pageSize",
    }
)

# src/agent/controllers/agent.controller.ts:84-116 (developers, vendors) -> AgentService.paginateV2
# (src/agent/services/agent.service.ts:168, args.* reads); AgentPaginateInput (src/agent/inputs/agent.query.ts:42).
AGENT_PAGINATE = frozenset(
    {
        "q",
        "saved",
        "sort",
        "status",
        "categories",
        "developers",
        "vendors",
        "liveSearch",
        "owned",
        "pageNumber",
        "pageSize",
    }
)

# sortToMongo (src/common/inputs/sort.input.ts:17-21) maps `field` straight to a Mongo key: only real
# document fields sort anything.
SORTABLE_FIELDS = frozenset({"name", "createdAt", "updatedAt"})


def unread_keys(body: dict, reads: frozenset) -> list:
    """Keys the SDK sent with a value that the endpoint never reads."""
    return sorted(key for key, value in body.items() if value not in (None, [], "") and key not in reads)


def sort_problems(body: dict) -> list:
    """Why the body's sort would not sort, or [] when it would."""
    sort = body.get("sort")
    if not sort:
        return ["no `sort` list in the body"]
    problems = []
    for entry in sort:
        if entry.get("field") not in SORTABLE_FIELDS:
            problems.append("field %r is not a document field" % entry.get("field"))
        if entry.get("dir") not in (1, -1):
            problems.append("dir %r is not 1 or -1" % entry.get("dir"))
    return problems
