/**
 * PWD Manufacturing — Quote Request intake web app.
 *
 * Receives a JSON POST from quote-request.html, saves every uploaded file to a
 * Drive folder, appends a row to the Quotes sheet, and emails the shop an alert.
 *
 * Deploy: Deploy > New deployment > Web app > Execute as: Me >
 *         Who has access: Anyone. Paste the /exec URL into SCRIPT_URL in the form.
 *
 * NOTE ON CORS: Apps Script web apps cannot answer a CORS preflight (OPTIONS).
 * The form avoids triggering one by sending a plain string body with no custom
 * headers (a "simple request"). Do NOT try to set response headers here to
 * "fix" CORS — that is the wrong layer and will not work.
 */

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
    const dueDate    = payload.dueDate    || '';
    const dimensions = payload.dimensions || '';
    const processing = payload.processing || '';
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
      'Files (' + fileLinks.length + '):',
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
