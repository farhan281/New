/**
 *  Google Apps Script: CSV-to-Sheet Importer
 *  ==========================================
 *
 *  This doPost(e) function parses the JSON sent from your Python script:
 *    { "csv": "Company,URL,Email 1,...\nAcme,...\n..." }
 *  Then it converts the CSV text into a 2D array via Utilities.parseCsv
 *  and writes it in one go into the “Scraped Data” sheet (or whatever you name it).
 */

function doPost(e) {
  try {
    // 1) Parse JSON payload (your Python script should send payload["csv"])
    var requestData = JSON.parse(e.postData.contents);
    if (!requestData.csv) {
      throw new Error("Request JSON is missing the 'csv' field.");
    }
    var csvText = requestData.csv.toString();

    // 2) Convert CSV text into a 2D array
    var allRows = Utilities.parseCsv(csvText);

    // 3) Open (or create) the target sheet
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = "Scraped Data"; // Change as you like
    var sheet = ss.getSheetByName(sheetName);

    if (sheet) {
      // If it exists, clear old data first
      sheet.clear();
    } else {
      // Otherwise create it
      sheet = ss.insertSheet(sheetName);
    }

    // 4) Write every CSV row into the sheet in one batch
    //    allRows.length = number of rows, allRows[0].length = number of columns
    if (allRows.length > 0) {
      sheet
        .getRange(1, 1, allRows.length, allRows[0].length)
        .setValues(allRows);
    }

    return ContentService
      .createTextOutput("✅ CSV successfully imported to sheet")
      .setMimeType(ContentService.MimeType.TEXT);
  }
  catch (err) {
    return ContentService
      .createTextOutput("❌ Error: " + err.message)
      .setMimeType(ContentService.MimeType.TEXT);
  }
}
