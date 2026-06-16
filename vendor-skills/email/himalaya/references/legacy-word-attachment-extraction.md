# Extracting text from legacy Word attachments in Himalaya messages

Use this note when an email attachment downloaded by `himalaya attachment download` has no useful extension, `message read --preview` inlines a huge `<#part type=application/octet-stream>` blob, or a forwarded request contains an old `.doc`/OLE specification.

## Workflow

1. Save the readable message header/body separately so the request context is not lost:
   ```bash
   mkdir -p /tmp/mail_<id>
   himalaya message read --folder INBOX --preview -H From -H To -H Date -H Subject <id> > /tmp/mail_<id>/message.txt
   ```

2. Download attachments even when the part is displayed as `application/octet-stream` and has no nice filename:
   ```bash
   himalaya attachment download --folder INBOX --downloads-dir /tmp/mail_<id> --output json <id>
   file /tmp/mail_<id>/*
   ```

3. For old Word/OLE files, prefer document converters if available:
   ```bash
   libreoffice --headless --convert-to txt --outdir /tmp/mail_<id> /tmp/mail_<id>/<attachment>
   soffice --headless --convert-to txt --outdir /tmp/mail_<id> /tmp/mail_<id>/<attachment>
   ```

4. If conversion fails or the binary has already been mixed into the preview output, recover embedded UTF-16LE strings:
   ```bash
   strings -el -n 2 /tmp/mail_<id>/<attachment> > /tmp/mail_<id>/attachment.utf16le.strings.txt
   # If only the preview/plain dump contains the blob:
   strings -el -n 2 /tmp/mail_<id>/message.txt > /tmp/mail_<id>/preview.utf16le.strings.txt
   ```

5. Search the extracted strings for table anchors and dates:
   ```bash
   grep -Ei 'Наименование|Кол-во|Срок|достав|изготов|[0-9]{2}\.[0-9]{2}\.[0-9]{4}|руб|шт|№' /tmp/mail_<id>/*.strings.txt
   ```

## Reading old Word specs

- Old `.doc` files often store visible Russian text as UTF-16LE; `strings -el` can recover item names, quantities, links, and deadline notes even when table formatting is lost.
- Quantity/price values may appear separated from item names. Cross-check nearby order, links, and table headers before reporting certainty.
- In the final user answer, clearly distinguish facts read from the email body (deadline requested by sender) from facts read from the attachment (delivery/manufacturing deadline, item list). If table extraction was imperfect, say so briefly instead of overstating precision.
