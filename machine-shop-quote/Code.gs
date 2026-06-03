/**
 * PWD Manufacturing — Quote Request intake web app.
 *
 * Receives a JSON POST from quote-request.html, saves every uploaded file to a
 * Drive folder, appends a row to the Quotes sheet, and emails the shop an alert.
 *
 * Deploy: Deploy > New deployment > Web app > Execute as: Me >
 *         Who has access: Anyone. Paste the /exec URL into SCRIPT_URL in the form.
 *
 * NOTE ON CORS: Apps Script web apps cannot answer a CORS preflight (OPTIONS) —
 * the platform never routes OPTIONS to doPost/doGet, and you cannot set custom
 * response headers, so there is NO server-side way to satisfy a preflight. The
 * only reliable fix is on the form: send a plain string body with no custom
 * headers (a "simple request"), which skips the preflight entirely. See
 * INTEGRATION.md. The doGet() below is a health check so you can confirm the
 * deployment is live independently of any form/CORS question.
 */

/**
 * Health check. Open the /exec URL in a browser (a GET) and you should see
 * {"ok":true,"status":"alive"}. If this works but form POSTs don't, the problem
 * is the form sending a non-simple request (a custom Content-Type header) and
 * triggering a preflight — fix it on the form, not here.
 */
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, status: 'alive' }))
    .setMimeType(ContentService.MimeType.JSON);
}

// ─── Config — fill these in ────────────────────────────────────────────────
const FOLDER_ID    = 'PASTE_DRIVE_FOLDER_ID_HERE';   // Drive folder for uploads
const SHEET_ID     = 'PASTE_SPREADSHEET_ID_HERE';    // Spreadsheet (must have a "Quotes" tab)
const NOTIFY_EMAIL = 'PASTE_SHOP_EMAIL_HERE';        // Where the alert is sent
// ───────────────────────────────────────────────────────────────────────────

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);

    // Field set — must match the form and the sheet column order.
    const name       = payload.name       || '';
    const company    = payload.company    || '';
    const email      = payload.email      || '';
    const phone      = payload.phone      || '';
    const material   = payload.material   || '';
    const quantity   = payload.quantity   || '';
    const dueDate    = payload.due_date   || '';
    const dimensions = payload.dimensions || '';
    const processing = payload.processing || '';
    // "Anything else" — also where customers paste a Dropbox/Drive/WeTransfer
    // share link for files too big to upload (over the form's ~25 MB guard).
    const notes      = payload.notes      || '';

    // 1. Save each uploaded file to the Drive folder, collecting share links.
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const files = Array.isArray(payload.files) ? payload.files : [];
    const fileLinks = [];
    files.forEach(function (f) {
      const blob = Utilities.newBlob(Utilities.base64Decode(f.dataB64), f.mimeType, f.name);
      const file = folder.createFile(blob);
      fileLinks.push(file.getUrl());
    });

    // 2. Append the quote as a row in the Quotes sheet.
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Quotes');
    sheet.appendRow([
      new Date(), name, company, email, phone, material, quantity,
      dueDate, dimensions, processing, notes, fileLinks.join('\n')
    ]);

    // 3. Email the shop an alert with all fields + links.
    const folderUrl = folder.getUrl();
    const subject = 'PWD quote request — ' + name + ' (' + material + ' x' + quantity + ')';
    const bodyLines = [
      'New quote request received via the PWD Manufacturing website.',
      '',
      'Name:       ' + name,
      'Company:    ' + company,
      'Email:      ' + email,
      'Phone:      ' + phone,
      'Material:   ' + material,
      'Quantity:   ' + quantity,
      'Due date:   ' + dueDate,
      'Dimensions: ' + dimensions,
      'Processing: ' + processing,
      'Notes:      ' + notes,
      '',
      'Uploaded files (' + fileLinks.length + '):',
      fileLinks.length ? fileLinks.join('\n') : '(none uploaded)',
      '',
      'Drive folder: ' + folderUrl
    ];
    MailApp.sendEmail(NOTIFY_EMAIL, subject, bodyLines.join('\n'));

    // 4. Success.
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    console.error('Quote intake failed: ' + err);
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err && err.message ? err.message : err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
