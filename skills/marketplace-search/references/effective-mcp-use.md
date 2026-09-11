# Effective Marketplace MCP use

Use this sequence whenever an answer depends on marketplace truth or runnable asset code:

1. **Discover:** call `search` with a focused query. Retry with one distinctive token if a phrase misses.
2. **Identify:** take `id`, `path`, and `asset_type` from the returned result block.
3. **Confirm facts:** call `get_asset_details` before reporting price, supplier, status, or hosting. If `hosted_by` is empty, say “Hosting provider is not listed.”
4. **Inspect the contract:** call the asset-type-specific `list_actions_*` and `list_inputs_*` actions. Use only returned action names and fields.
5. **Generate and validate:** build SDK/REST/agent-attach code from that schema. Do not invent inner parameters. Prefer the first-party aixplain Web Search tool for web-search use cases when it fits.
6. **Test correctly:** do not use MCP `run_*` actions; generate the SDK call and run it with realistic input instead.

Use `search` plus `stats.total` for counts. `search_*` is for examples, not authoritative totals. There is no universal run action and no server-side sort parameter.
