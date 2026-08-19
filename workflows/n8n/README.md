# n8n Workflows

Ready-to-import n8n workflow JSON files for automating operational tasks.

## invoice-capture-to-notion.json

**What it does:** Watches an email inbox for incoming invoices, extracts the
invoice data from PDF attachments using an LLM, and files a structured
record into a Notion database. Invoices that are missing key fields are
routed to a manual-review email instead of being auto-filed.

**Flow:**
1. `IMAP Email Trigger` — polls the shared invoices inbox for new mail
2. `Extract PDF Attachments` — pulls out PDF attachments, one per invoice
3. `Loop Over Invoices` — processes each PDF individually
4. `Extract Text From PDF` — converts the PDF to raw text
5. `Extract Invoice Fields (AI)` — an LLM (via `OpenAI Chat Model`) parses
   vendor, invoice number, dates, amounts, currency, and PO number
6. `Validate & Normalize` — checks required fields are present
7. `Extraction Complete?` — routes valid invoices to Notion, incomplete ones
   to a manual-review notification
8. `Create Notion Invoice Page` — creates a page in your Notion invoices
   database
9. `Notify Manual Review` — emails the AP team when a field is missing

### Setup

1. In n8n, **Import from File** and select `invoice-capture-to-notion.json`.
2. Create/attach credentials for the four placeholder nodes:
   - `IMAP Email Trigger` → IMAP credential for the invoices inbox
   - `OpenAI Chat Model` → OpenAI API credential
   - `Create Notion Invoice Page` → Notion API credential
   - `Notify Manual Review` → SMTP credential
3. In `Create Notion Invoice Page`, replace `YOUR_NOTION_INVOICES_DATABASE_ID`
   with your Notion database ID, and make sure the database has these
   properties (rename in the node if yours differ):
   - `Name`/Title — set from the node's `title` field
   - `Vendor` (rich text)
   - `Invoice Number` (rich text)
   - `Invoice Date` (date)
   - `Due Date` (date)
   - `Total Amount` (number)
   - `Currency` (select)
   - `PO Number` (rich text)
   - `Status` (select, with a `Captured` option)
   - `Source Email` (rich text)
4. Update the `fromEmail`/`toEmail` addresses in `Notify Manual Review`.
5. Activate the workflow.

Node versions target a recent n8n release; if your instance flags a node as
outdated on import, open it once in the editor and n8n will offer to migrate
it automatically.
