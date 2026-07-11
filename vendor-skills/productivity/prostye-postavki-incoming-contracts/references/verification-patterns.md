# Verification patterns for incoming contracts

## Historical parsed-item field mapping

The incoming-document UI may serialize a correctly entered item like this:

```json
{
  "price": "3",
  "total": "1750",
  "sum": "5250"
}
```

In that historical representation:

- `price` = quantity;
- `total` = unit price;
- `sum` = row sum.

Do not “fix” the values merely because the raw keys look inverted. The authoritative normalized checks are:

- after `save_incoming_contract_document_fields`: `itemsReadable[].qty`, `.price`, `.sum`, plus `totalAmount`;
- after `save_contract_from_incoming_document`: `itemsSaved[].qty`, `.price`, `.sum`, plus `totalAmount`.

## Explicit operational date override

When the source says a relative condition such as “within 21 calendar days after signing” but the user directly asks to set the deadline to today:

1. Set `contractDate` and `deadlineDate` to the live Moscow date.
2. Set item `planDate` to the same date when the request covers item plans.
3. Keep the original phrase in `deadlineText` or `notes` and state that the card deadline was set by user instruction.
4. Do not silently replace or erase the source phrase.

## Final creation checklist

- status is `created` or the expected overwrite result;
- number and both dates are correct;
- customer and supplier INNs match the source;
- neither linked organization is a placeholder;
- every `itemsSaved` row matches quantity, unit price, and sum;
- `totalAmount` matches the specification;
- `sumWarnings` is empty;
- `docsSent` reflects the user's instruction;
- source file is present in `docSnapshot` and removal from incoming is expected.

If any check fails, overwrite the same contract once with `contractId`; never create a duplicate.