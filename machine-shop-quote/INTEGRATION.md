# Frontend Integration Contract — Quote Form → `Code.gs`

This is what the **branded quote form HTML** must do to work with the backend
(`Code.gs`). The HTML can look like anything; it just has to send the right
request. Hand this doc to whoever builds the form.

> A working reference implementation lives in `quote-request.html` — copy its
> submit logic if useful. This doc is the spec; that file is one example of it.

---

## 1. Endpoint

POST to the deployed Apps Script web app URL (ends in `/exec`). You get this
after deploying per `DEPLOY.md`.

```js
const SCRIPT_URL = "https://script.google.com/macros/s/XXXXX/exec";
```

## 2. Payload shape (JSON)

Send a single JSON object. **Field names and the file object shape matter** —
the backend reads these keys exactly and writes them to the sheet in this order:

```json
{
  "name":       "Jane Smith",
  "company":    "Acme Co",
  "email":      "jane@acme.com",
  "phone":      "555-123-4567",
  "material":   "Aluminum",
  "quantity":   "10",
  "dueDate":    "2026-07-01",
  "dimensions": "120 x 80 x 25 mm, ±0.05",
  "processing": "CNC Milling",
  "notes":      "Anodized finish preferred",
  "files": [
    { "name": "part.step", "mimeType": "application/step", "dataB64": "<base64>" }
  ]
}
```

**Sheet column order** (for reference — the backend handles this, do not send it):
`timestamp · name · company · email · phone · material · quantity · dueDate · dimensions · processing · notes · fileLinks`

- All text fields are optional except whatever you choose to validate client-side.
- `files` is an array; send `[]` if none.
- Each file: `name` (string), `mimeType` (string), `dataB64` (base64 **without**
  the `data:...;base64,` prefix).

## 3. ⚠️ CORS — the rule that makes or breaks this

Apps Script web apps **cannot answer a CORS preflight (OPTIONS)** request. To
avoid triggering one, send the request as a **"simple request":** a plain string
body with **NO custom headers**.

```js
const res = await fetch(SCRIPT_URL, {
  method: "POST",
  body: JSON.stringify(payload)   // string body → browser sends text/plain → no preflight
});
```

- **DO NOT** set `headers: { "Content-Type": "application/json" }`. That single line
  triggers the preflight that silently kills the submission. The backend reads
  `e.postData.contents` and `JSON.parse`s it regardless of the content-type label.
- **DO NOT** try to "fix" CORS by adding response headers in `Code.gs` — the platform
  never routes the `OPTIONS` preflight to your code and won't let you set those
  headers, so there is no server-side fix. Structure the request correctly instead.

### Two-tier approach (recommended → guaranteed)

**Tier 1 (recommended):** the simple request above. Apps Script answers the POST,
then 302-redirects to a `script.googleusercontent.com` URL that serves the result
with `Access-Control-Allow-Origin: *`; `fetch` follows that redirect automatically,
so you can read `{ ok: true }` back and show real success/error states. Use this.

**Tier 2 (guaranteed fallback):** if reading the response ever proves flaky in
production, switch to `mode: "no-cors"`:

```js
await fetch(SCRIPT_URL, { method: "POST", body: JSON.stringify(payload), mode: "no-cors" });
// Response is "opaque" — you CANNOT read it. The backend still runs (file saved,
// row written, email sent). Treat a non-throwing fetch as success.
```

Trade-off: with `no-cors` you can't detect a server-side `{ok:false}`, so you lose
the precise error message — but submissions still go through. Only drop to this if
Tier 1 misbehaves.

### Diagnosing fast
`Code.gs` has a `doGet` health check. Paste the `/exec` URL straight into a browser:
- See `{"ok":true,"status":"alive"}` → the deployment is live and reachable.
- Health check works but form POSTs fail → it's a **preflight** problem: the form is
  sending a custom `Content-Type` header. Remove it (Tier 1) or use Tier 2.
- Health check fails too → it's a **deploy** problem (wrong access setting / not
  deployed), not CORS. Re-check `DEPLOY.md` step 4 ("Who has access: Anyone").

## 4. Encoding files to base64

Read each `File` with `FileReader.readAsDataURL`, then strip the data-URI prefix:

```js
function readAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result || "";
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result); // strip "data:...;base64,"
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}
```

## 5. File-size guard (required)

Apps Script + base64 can't take unlimited payloads. Before posting, sum file sizes;
if the total exceeds **~25 MB**, block the submit and tell the user to paste a
shareable Drive/Dropbox link into the "Anything else" (`notes`) field instead.
Put a one-line helper near the upload control noting the ~25 MB limit + link option.

```js
const MAX_TOTAL_BYTES = 25 * 1024 * 1024;
const total = selectedFiles.reduce((s, f) => s + f.size, 0);
if (total > MAX_TOTAL_BYTES) { /* show message, abort submit */ }
```

## 6. Response handling

The backend returns JSON:

- Success: `{ "ok": true }` → show the success screen.
- Failure: `{ "ok": false, "error": "<message>" }` → show the error state.

```js
const data = await res.json();
if (!data.ok) throw new Error(data.error || "Server error");
```

---

## Drop-in submit function

Adapt the field reads to the branded markup; the request itself must stay as-is.

```js
async function submitQuote(formData, selectedFiles) {
  // formData = { name, company, email, phone, material, quantity, dueDate, dimensions, processing, notes }
  // selectedFiles = array of File objects

  // 25 MB guard
  const MAX_TOTAL_BYTES = 25 * 1024 * 1024;
  const total = selectedFiles.reduce((s, f) => s + f.size, 0);
  if (total > MAX_TOTAL_BYTES) {
    throw new Error("Files exceed ~25 MB. Paste a shareable Drive/Dropbox link in \"Anything else\" instead.");
  }

  // Encode files
  const files = [];
  for (const f of selectedFiles) {
    files.push({
      name: f.name,
      mimeType: f.type || "application/octet-stream",
      dataB64: await readAsBase64(f)
    });
  }

  const payload = { ...formData, files };

  // CORS-safe simple request: string body, NO custom headers.
  const res = await fetch(SCRIPT_URL, {
    method: "POST",
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "Server error");
  return data; // { ok: true }
}
```

---

## Checklist for the form builder
- [ ] `SCRIPT_URL` points at the deployed `/exec` URL.
- [ ] Payload uses the exact field names in §2.
- [ ] Files sent as `{ name, mimeType, dataB64 }`, base64 with prefix stripped.
- [ ] `fetch` has **no** `Content-Type` header; body is a JSON string.
- [ ] 25 MB total guard with the link-instead message.
- [ ] Success on `{ok:true}`, error on `{ok:false}` / network failure.
- [ ] Customer never hits a Google sign-in prompt.
