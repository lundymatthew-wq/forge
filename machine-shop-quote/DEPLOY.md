# Deploy Checklist — Quote Form → Google (Sheet + Drive + Gmail)

Everything runs under **one dedicated Gmail account the owner controls**. No customer
Google sign-in, no Supabase, no Resend. The glue is a free **Google Apps Script web app**.

Do these steps in order, signed in as that dedicated account.

---

## 1. Create the Google Sheet
1. Go to <https://sheets.google.com> → **Blank spreadsheet**.
2. Rename the bottom tab from `Sheet1` to **`Quotes`** (exact, case-sensitive).
3. *(Optional but nice)* add a header row:
   `Timestamp | Name | Company | Email | Phone | Material | Quantity | Due date | Dimensions | Processing | Notes | Uploaded files`
4. Copy the **spreadsheet ID** from the URL — the long string between `/d/` and `/edit`:
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`
   → this is your **`SHEET_ID`**.

## 2. Create the Drive folder
1. Go to <https://drive.google.com> → **New → Folder** (e.g. "Quote Uploads").
2. Open the folder. Copy the **folder ID** from the URL — the part after `/folders/`:
   `https://drive.google.com/drive/folders/`**`THIS_PART`**
   → this is your **`FOLDER_ID`**.

## 3. Create the Apps Script project
1. Go to <https://script.google.com> → **New project**.
2. Delete the default `myFunction` stub, then paste in the entire contents of **`Code.gs`**.
3. Fill in the three constants at the top:
   - `FOLDER_ID`    → from step 2
   - `SHEET_ID`     → from step 1
   - `NOTIFY_EMAIL` → the shop address that should receive alerts
4. Save (💾 / Ctrl-S).

## 4. Deploy as a web app
1. Click **Deploy → New deployment**.
2. Click the gear icon → select type **Web app**.
3. Set:
   - **Execute as:** `Me`
   - **Who has access:** `Anyone`  ← **must be "Anyone"** or the public form is blocked.
4. Click **Deploy**.

## 5. Authorize (first run only)
1. When prompted, click **Authorize access** and pick the dedicated account.
2. You'll see an **"unverified app"** warning — this is expected for your own script.
   Click **Advanced → Go to [project name] (unsafe) → Allow**.

## 6. Wire the URL into the form
1. After deploy, copy the **Web app URL** — it ends in **`/exec`**.
2. Open **`quote-request.html`**, find this line near the top of the `<script>`:
   ```js
   const SCRIPT_URL = "PASTE_APPS_SCRIPT_EXEC_URL_HERE";
   ```
   Replace the placeholder with your `/exec` URL.
3. Host `quote-request.html` anywhere (or open it locally) and submit a test.

---

## Re-deploying after a `Code.gs` change
Apps Script keeps the old code live until you publish a new version:
**Deploy → Manage deployments → (edit ✏️) → Version: New version → Deploy.**
The `/exec` URL stays the same, so you do **not** need to update the form.

## Acceptance checks (from the directive)
- [ ] Submitting the live form creates a new row in the **Quotes** sheet with all fields populated.
- [ ] Every uploaded file appears in the Drive folder, and its link is in the sheet row.
- [ ] An email alert arrives at `NOTIFY_EMAIL` with details + file links + Drive folder link.
- [ ] Tested with a small PDF, a phone photo, and one STEP/CAD file.
- [ ] A >25 MB upload is blocked with the link-instead message.
- [ ] The customer never sees a Google sign-in prompt.
- [ ] Success screen shows on submit; error box shows if the script is unreachable.

## If submissions fail silently
That's almost always **CORS** (the directive's known failure point #1). The form is built
to avoid it by sending a plain-string body with **no custom headers** — do not add a
`Content-Type: application/json` header to the `fetch`, and do not try to set response
headers in `Code.gs`. If reading the response is still unreliable, switch the `fetch` to
`mode: "no-cors"` (see the comment by the `fetch` call) and treat a non-throwing request
as success.
