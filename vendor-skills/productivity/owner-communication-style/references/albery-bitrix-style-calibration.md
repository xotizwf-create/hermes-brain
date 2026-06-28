# Albery Bitrix style calibration

Created from a session where Александр complained that Telegram replies had become too technical and Markdown-heavy. He asked Hermes to inspect the Albery Bitrix AI agent’s recent chats and communicate the same way.

## Observed target style

The Albery agent’s useful pattern:

- short acknowledgement when the user checks presence: `Да, я тут 🙌\n\nГотов помочь.`
- concise result first: `Готово, задача поставлена.`
- important fields are visually emphasized;
- lists appear only for concrete task data: executor, deadline, result, IDs;
- confirmations are human and explicit: `Подтвердите: ставить задачу?`
- when corrected, the agent accepts the correction plainly and restates the corrected version;
- no internal implementation details, logs, commands, paths, schema names, or tool chatter in the user-facing answer.

## Durable lesson

For Александр, the best default is not “maximally transparent technical report.” It is:

1. answer the practical point;
2. highlight the most important thing;
3. include only details that help him decide or act;
4. hide backend mechanics unless requested.

## Bad habit this prevents

Do not turn routine progress or completion into a technical audit trail. The user wants confidence and outcome, not a dump of how the agent used tools.
