# Cursor Assistant Rules

1. **Pending Edits Check**  
   After proposing a code change (via `edit_file`), pause and wait for the user to accept or reject the diff before running any follow-up automation, QA, or generation scripts.  
   • _Rationale:_ prevents wasting compute or confusing the user with results based on code that hasn't been approved.

2. **Confirmation Before Execution**  
   Any potentially long-running or write-heavy script (data generation, migrations, CI fixtures, etc.) must be explicitly green-lit by the user after the latest edits are applied.

3. **Branch Safety**  
   Never issue commands that mutate `main`; stay on the feature branch (`ai-improve`) unless the user instructs otherwise.

4. **Verbose Status**  
   When awaiting acceptance, clearly state: "Awaiting approval of the previous edit – no scripts executed." 