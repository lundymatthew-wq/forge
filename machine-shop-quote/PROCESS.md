# PWD Manufacturing — Quote Form: Go-Live & Operating Process

This covers the whole picture: the files, how they fit together, how to put them
**live on the web**, and the **day-to-day process** for handling incoming quotes.

For the Google-account setup (Sheet, Drive folder, Apps Script deploy), see
**`DEPLOY.md`** — do that first; this doc references it.

---

## The pieces

| File | What it is | Who hosts it |
|---|---|---|
| `index.html` | Branded landing page. Drives visitors to the quote form. | Your web host |
| `quote-request.html` | The quote form. Collects details + files, POSTs to the Apps Script. | Your web host |
| `Code.gs` | Google Apps Script web app. Saves files to Drive, writes the Sheet row, emails the shop. | Google (script.google.com) |

Flow:

```
visitor → index.html → "Get a Quote" → quote-request.html
              → POST → Code.gs (Apps Script web app)
                          ├─ saves files to Drive folder
                          ├─ appends a row to the "Quotes" sheet
                          └─ emails NOTIFY_EMAIL with details + links
```

---

## Part 1 — Go live (hosting)

You need the two HTML files reachable at a public URL. **`Code.gs` is already
"hosted" by Google** once deployed per `DEPLOY.md` — it is not part of this step.

> Order of operations: complete `DEPLOY.md` first so you have the `/exec` URL,
> paste it into `quote-request.html` (`SCRIPT_URL`), **then** upload the files.

### Option A — Netlify drag-and-drop (fastest, free)
1. Put `index.html` and `quote-request.html` together in one folder.
2. Go to <https://app.netlify.com/drop> and drag that folder onto the page.
3. You get a live URL instantly (e.g. `https://pwd-quote.netlify.app`).
   - Landing page: `…/index.html` (or just the root URL)
   - Form: `…/quote-request.html`
4. (Optional) In Netlify → Domain settings, point `www.pwdmanufacturing.com`
   (or a subdomain like `quote.pwdmanufacturing.com`) at the site.

### Option B — GitHub Pages (free, version-controlled)
1. The files already live in the repo under `machine-shop-quote/`.
2. Repo **Settings → Pages → Build from branch**, pick the branch and `/`(root)
   or move the two HTML files to a `/docs` folder and serve from there.
3. Site publishes at `https://<user>.github.io/<repo>/machine-shop-quote/index.html`.

### Option C — Wix (the shop's site) ← see `WIX.md`
The PWD site is on Wix. Wix doesn't run our form as a native page, but it embeds
it cleanly. Recommended: host `quote-request.html` (Option A above) and drop it
into the Wix page via **Add → Embed Code → Embed a Site** (iframe by URL). Full
step-by-step (plus a paste-the-code option and a Velo option) is in **`WIX.md`**.

### After uploading — smoke test
- Open the landing page; click **Get a Quote** → the form loads.
- Submit a test with a small file. Confirm: Drive file appears, Sheet row added,
  alert email arrives. If nothing happens, see the CORS note in `DEPLOY.md`.

---

## Part 2 — Operating process (handling a quote)

When a request comes in, here's the loop:

1. **Alert email** lands at `NOTIFY_EMAIL` (the dedicated Gmail/shop address).
   Subject: `PWD quote request — {name} ({material} x{quantity})`. It contains
   every field, the uploaded file links, and a link to the Drive folder.
2. **Open the file links** (drawings / STEP / photos) right from the email, or
   open the Drive folder to see everything in one place.
3. **Review the row** in the `Quotes` Google Sheet — one row per request, in order.
   This is your running log of all incoming work.
4. **Price it** and reply to the customer (their email is in the row / alert).
5. **Track status.** Recommended: add a couple of columns to the `Quotes` sheet
   by hand for your own workflow, e.g.:
   - `Status` — New / Quoted / Won / Lost
   - `Quoted $` — the number you sent
   - `Notes` — internal follow-up notes
   These live to the **right** of the auto-filled columns so the script never
   touches them (it only ever appends a new row using columns A–L).

### Roles / who sees what
- **Customers** never sign into Google and never see the Sheet or Drive — they
  only see the form and the success screen.
- **The shop** sees everything through the one dedicated Google account that owns
  the Sheet, the Drive folder, and the Apps Script.

### Good habits
- Keep the dedicated Gmail logged in (or forwarding to whoever quotes) so alerts
  aren't missed.
- Periodically tidy the Drive folder (e.g. subfolders by month) — the script always
  drops new files at the top level of `FOLDER_ID`.
- If spam ever becomes an issue, add a simple required "What are you making?" field
  or a honeypot; ask and I'll wire it in.

---

## Changing things later
- **Branding/colors/copy:** edit the `:root` tokens and text in the HTML files.
- **Form fields:** if you add/remove a field, it must be added in the same order to
  the `appendRow([...])` in `Code.gs` (and the Sheet header) so columns stay aligned.
- **Re-deploying `Code.gs`:** Deploy → Manage deployments → edit → New version.
  The `/exec` URL stays the same, so the form needs no change.
