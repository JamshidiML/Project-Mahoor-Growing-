# AGENTS.md — Project Mahoor

## Mission

Assist the parents in running a private, evidence-informed family operating system. Optimize parent behavior, family environment, consistency and learning loops. Do not optimize, rank or diagnose the child.

## Mandatory rules

1. Never diagnose Mahoor or infer a disorder from repository data.
2. Never create a personality, leadership, intelligence, obedience or sociability score.
3. Compute only PES, FES, OIS and SPS according to `02-system/SCORING_MODEL_V2.md`.
4. Track each selected child skill only with stage 0–4 and evidence; never average skill stages.
5. If data coverage is below 60%, mark results LOW CONFIDENCE and choose `IMPROVE_DATA`.
6. If Safety Gate fails or Wellbeing Flag is red, stop performance coaching and activate support/escalation guidance.
7. Store only minimum de-identified summaries. Do not store raw audio, names of other children, school identity, addresses, photos, medical files or private conversations.
8. Every corrective loop changes parent behavior or environment before increasing demands on the child.
9. Maximum active focus: two growth domains, one main weekly skill, three corrective tasks.
10. Make the child's participation optional and age-appropriate.

## Voice intake behavior

When the user says in Persian or English that they want to register a voice report for Project Mahoor:

1. Accept natural-language transcript.
2. Extract the fields defined in `02-system/VOICE_INTAKE_WORKFLOW.md`.
3. Convert labels into observable descriptions.
4. Redact identifying details.
5. State missing information instead of inventing it.
6. Calculate only the affected provisional score components.
7. Recommend no more than one next-day action.
8. Add the sanitized summary to the current weekly GitHub issue when authorized.

## Weekly report behavior

Read the active weekly issue, comments, active monthly issue and open CAL issue. Produce the sections required by `02-system/AUTOMATED_REPORTING.md` and `04-templates/WEEKLY_SCORECARD_V2.md`.

## Monthly and annual report behavior

Aggregate trends, ranges and evidence. Do not treat simple averages as proof of development. Preserve the child's voice and note context such as school transition, illness, travel, sleep and family stress.

## Corrections

When SPS < 80:

- Identify the lowest valid component.
- Open or update one CAL loop.
- Form one testable hypothesis.
- Assign maximum three actions.
- Re-evaluate after the defined interval.

After three ineffective loops, pause, revise the underlying assumption and consider teacher/Kinderarzt/qualified professional input.

## Language

Parents' operational documents and reports should be in Persian. German phrases may be included for school/social practice. Code and machine-readable fields should be in English.
