# Cost Monitoring and Model Choice

Interactive RPI workflows inherit the model and effort selected by the owner in the current Copilot session. A skill does not pin a model tier. The installer does not select a paid model or start inference. If a scheduled job needs reproducibility, its owner may choose and record a concrete model in that job's configuration.

## Measure actual outcomes

Use provider billing exports and observed work outcomes when they are available. Record the source, period, and attribution method for cost per completed change or workflow run. If a provider does not expose reliable attribution, report the value as unmeasured. Do not claim savings from a model label, token estimate, or planned scheduler.

Bounded independent assignments can reduce elapsed time, but each invocation uses resources. Set an explicit task, owned file set, resource budget, and terminal condition. Paid or scheduled fan-out requires the applicable owner authorization. Use the model already selected for interactive work unless the owner changes it.

## Review choices

When cost evidence exists, compare completed outcomes, quality, and spend across model choices. The owner can select a different model or effort for a particular session or scheduled job. Record the choice and observed result; do not silently rewrite workflow metadata or infer a cheaper model is adequate from static documentation.
