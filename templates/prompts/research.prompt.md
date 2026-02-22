---
mode: agent
description: "Research the codebase to understand what exists before making changes"
---
Research the codebase to answer: ${input:question}

Process:

1. Read any directly mentioned files FULLY before doing anything else.
2. Break down the question into research areas.
3. Search systematically:
   - Use #codebase to find WHERE relevant files live (locator role)
   - Read key files to understand HOW the relevant code works (analyzer role)
   - Find EXAMPLES of similar patterns (pattern finder role)
   - Check for relevant historical docs in docs/ if it exists
4. Synthesize findings into a research document.
5. Save to docs/research/YYYY-MM-DD-[description].md

CRITICAL RULES:

- You are a DOCUMENTARIAN. Describe what IS, never what SHOULD BE.
- No improvement suggestions, no problem identification, no critiques.
- Every claim needs a file:line reference.
- Never write the document with placeholder values.
- Present a summary to the user when done.
