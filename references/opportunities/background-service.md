# Background platform service

_Opportunities for a background platform service. Routed from `opportunity-catalog.md`, which carries the practice taxonomy and the price baseline every scope needs._

Practices: `usage-optimization`, `governance-policy-risk`, `unit-economics`.

Predictive Optimization, Data Quality Monitoring, Data Classification, Fine-Grained Access Control,
Base Environments, AI Runtime. These bill through another service's SKU, are mostly not taggable,
and are found by filtering on `billing_origin_product` — never by SKU.

| Opportunity | Evidence to establish it | Trade-off to state |
|---|---|---|
| Narrow the enablement scope | Cost by catalog or schema against tables actually queried | Losing optimization or monitoring where it was earning its cost |
| Reduce monitor frequency | Refresh cost against how often results are read | Staleness in a governance signal |
| Disable where the benefit is unobserved | Cost of the service against measured benefit — query improvement, issues caught | The benefit may be real and unmeasured; say which |

The honest question for this scope is whether the service still earns its cost. Often it does, and
the finding is a narrowed scope rather than a removal. A background service is also the one place
where "we did not know we were paying for this" is a legitimate finding on its own.
