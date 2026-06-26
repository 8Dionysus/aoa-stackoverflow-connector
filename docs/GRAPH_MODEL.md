# Graph Model

The graph contains source-shape nodes and claim nodes.

## Source Nodes

- `topic:<topic_id>`
- `question:<question_id>`
- `item:question:<question_id>`
- `item:answer:<answer_id>`
- `item:comment:<comment_id>`
- `item:linked:<linked_question_id>`
- `tag:<tag>`
- `entity:<kind>:<value>`

## Claim Nodes

Claim nodes use the portable schema `aoa_connector_claim_v1`.

Claim kinds:

- `method`
- `warning`
- `status`
- `context`
- `risk`

## Claim Relations

Claim relation edges use the connector-family vocabulary plus
StackOverflow-specific signal relations:

- `source_supports_claim`
- `source_warns_about_claim`
- `source_updates_claim`
- `source_links_claim`
- `answer_acceptance_supports_claim`
- `answer_score_weakly_supports_claim`
- `method_uses_tool`
- `method_targets_object`
- `warning_targets_object`
- `warning_targets_action`
- `claim_contextualizes_claim`
- `claim_scope_limited_by`
- `claim_supersedes_claim`
- `claim_contradicts_claim`
- `duplicate_contextualizes_question`

Non-claim edges such as `topic_contains_question`, `question_contains_item`,
`question_tagged_with`, and `question_duplicate_to` remain source-local graph
support.
