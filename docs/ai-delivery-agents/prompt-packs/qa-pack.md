# Prompt pack: QA

## Назначение
Проверка acceptance, smoke/regression, test automation planning.

## Каких агентов подключать
`ai-qa-engineer`, `ai-test-automation-engineer`, `ai-code-reviewer`, профильные implementation agents для fixes.

## Последовательность работы
Requirements -> test cases -> execution -> defects -> automation candidates -> release input.

## Шаблон Codex-запроса
```text
Ты ai-qa-engineer. Проверь acceptance criteria, составь QA checklist, выполни доступные проверки, опиши defects и residual risks.
```

## Expected output
QA report, test cases, failed/passed checks, automation recommendations.

## Quality gate
QA gate, Test automation gate при необходимости.

