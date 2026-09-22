# Usability measurement

## Outcome

The measured product outcome is: starting on the portfolio overview, can a reviewer reach the exact trigger explanation and potentially affected rooms with no more than two intentional actions?

The browser test performs this sequence at a 1440 × 1040 viewport:

1. Select the table representation from the portfolio overview.
2. Select `Investigate` on an equipment issue.

The success assertions require both `What triggered this issue?` and `Potentially affected spaces` to be visible. The current automated result is 6/6 browser scenarios passing, including this two-action investigation path. The test also confirms that the same session can continue into rule drafting, target review and human-confirmed activation without a browser error.

This is a repeatable interaction benchmark, not a substitute for human research.

## Property-engineer validation plan

Recruit three to five property engineers who have not seen the implementation. Give each person an incident-start screen without explaining the navigation and ask them to identify:

- the equipment that needs attention;
- the exact comparison, threshold and qualifying interval;
- whether the AHU was running;
- the served rooms that may be affected;
- the distinction between trigger measurements and contextual IAQ, return-air and meter data;
- the active rule version and local override.

Record task completion, wrong-room selections, time to answer, navigation actions, clarification questions and confidence on a five-point scale. Target at least 90% correct trigger and affected-room identification, a median under three minutes and no confusion between the plant room and served tenant rooms.

After each session, ask the engineer to explain the issue in their own words and identify one missing diagnostic signal. Review terminology and information hierarchy before changing visual styling. Repeat the same tasks after revisions so improvements are comparable.

## Safety observation

The activation control remains disabled until the reviewer supplies a name, checks the confirmation and views a preview matching the saved configuration. The browser test verifies this gate before activation. A future authenticated deployment should replace the free-text reviewer with the verified user identity.
