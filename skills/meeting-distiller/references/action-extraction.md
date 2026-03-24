# Action Extraction

Use this when the user mainly wants tasks, owners, and due dates.

## Extraction rules

Extract only actions that are:
- directly requested
- clearly promised
- strongly implied by a stated blocker or next step

## Action item schema

For each action, capture:
- Task
- Owner
- Due date
- Confidence
- Evidence note (optional, short)

## Owner rules

- Use explicit owner when stated.
- If the owner is ambiguous, use the role or speaker label.
- If no owner exists, mark **Unassigned**.

## Due date rules

- Use explicit date if stated.
- If relative timing is given and the meeting date is known, convert it and mark inferred only if necessary.
- If no due date exists, mark **No clear deadline**.

## Good examples

- Task: Create user for Khun Prae
  Owner: Speaker 1 / system team
  Due: After receiving email
  Confidence: Confirmed

- Task: Send Khun Prae's email for account creation
  Owner: Khun Prae / coordinating side
  Due: No clear deadline
  Confidence: Confirmed

## Bad examples

- Inventing deadlines because the meeting felt urgent
- Assigning the user as owner when someone only mentioned the task generally
- Treating explanation steps as actions when no next-step commitment exists

## Interaction with transcript repair

When extracting actions, use the **repaired** names and terms from step 0.
If an action item depends on a garbled term marked [unclear], flag the entire action as lower confidence.
