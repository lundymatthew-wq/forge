# Putting the Quote Form on a Wix Site

The shop's website is on **Wix**. Wix won't run our form as a raw page, but it
embeds external content cleanly. Below are three ways to do it, easiest first.
All three talk to the same backend (`Code.gs`) — nothing about the Google side
changes.

> Do `DEPLOY.md` first so you have the deployed `/exec` URL. Whichever embed
> method you pick, the form's `SCRIPT_URL` must point at that `/exec` URL.

---

## Option 1 — Host the form, embed by URL (recommended)

This is the most reliable: the form runs on **its own web address** inside an
iframe, so file uploads and reading the `{ok:true}` response both work normally.

1. **Host `quote-request.html`** somewhere public (free):
   - Netlify drag-and-drop (`https://app.netlify.com/drop`), or GitHub Pages, or
     any static host. You'll get a URL like `https://pwd-quote.netlify.app`.
   - (See `PROCESS.md` → "Go live" for the hosting steps.)
2. Make sure that hosted form's `SCRIPT_URL` is set to your `/exec` URL.
3. In the **Wix Editor**: **Add (+) → Embed Code → Embed a Site** (a.k.a. the
   iframe/"Embed a Site" element).
4. Paste the hosted form URL (e.g. `https://pwd-quote.netlify.app/quote-request.html`).
5. Resize the iframe box to fit the form; place it on a "Request a Quote" page.
6. Publish. Customers fill it out inside the Wix page; it posts straight to Google.

**Why this one:** the iframe loads your own origin, so the browser lets the form
read the response and there are no surprises with file inputs. Cleanest path.

---

## Option 2 — Paste the form code into Wix (no separate host)

If you'd rather not host a file anywhere:

1. In the **Wix Editor**: **Add (+) → Embed Code → Embed HTML** → choose **Code**.
2. Paste the **entire contents** of `quote-request.html` into the code box.
3. Set `SCRIPT_URL` (top of the `<script>`) to your `/exec` URL.
4. Resize the box, publish.

**Caveats vs. Option 1:**
- Wix runs this in a **sandboxed iframe** on a Wix domain. The POST still works
  (it's a CORS-safe "simple request"), but **reading the response can be flaky**
  in the sandbox. If success/error detection misbehaves, use the **`no-cors`
  fallback** documented in `INTEGRATION.md` §3 (treat a non-throwing submit as
  success).
- The code box has a size limit; our form fits, but if you heavily expand it,
  prefer Option 1.

---

## Option 3 — Wix Velo (advanced, most robust)

If the site already uses **Velo** (Wix's dev mode), you can skip browser CORS
entirely by calling Apps Script from the **backend**:

1. Build the form with native Wix elements + a Wix **Upload Button**.
2. In a backend web module (`backend/quotes.jsw`), use `wix-fetch` to POST the
   JSON payload to your `/exec` URL **server-to-server** (no CORS at all).
3. Call that web module from the page code on submit.

More work, but it's the sturdiest option and lets you use Wix's own file upload.
Use this only if you're already comfortable in Velo; Options 1–2 need no code mode.

---

## How "download the files" works (for the owners)

Customers never see Google. When a quote comes in:

- **Uploaded files** are saved to your **Google Drive folder**. The alert email
  and the Sheet row both contain **direct Drive links** — the owners click to
  **view or download** each file.
- **Large files (>25 MB)**: instead of uploading, the customer pastes a
  **Dropbox / Google Drive / WeTransfer** share link into the form's
  **"Link to large files"** field. That link shows up in the email and the Sheet
  row, and the owners download from there.

Either way the owner gets everything they need to download from the **one alert
email**, sent the moment the form is submitted.

---

## Quick checklist
- [ ] `Code.gs` deployed; `/exec` URL in hand (`DEPLOY.md`).
- [ ] Form's `SCRIPT_URL` = the `/exec` URL.
- [ ] Embedded via Option 1 (URL), 2 (pasted code), or 3 (Velo).
- [ ] Test submit from the published Wix page: file lands in Drive, row in Sheet,
      alert email arrives.
- [ ] Test a >25 MB case: form steers you to the "Link to large files" field.
- [ ] If response detection is flaky in a Wix-hosted iframe, switch to the
      `no-cors` fallback (`INTEGRATION.md`).
