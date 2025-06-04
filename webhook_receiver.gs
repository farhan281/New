/**
 *  Google Apps Script: CSV-to-Sheet Importer
 *  ==========================================
 *
 *  यह doPost(e) उस JSON को पार्स करता है जो Python स्क्रिप्ट भेजती है:
 *    { "csv": "Company,URL,Email 1,...\nAcme,...\n..." }
 *  फिर Utilities.parseCsv से CSV टेक्स्ट को 2D ऐरे में बदलकर
 *  "Scraped Data" (या आपकी पसंद का नाम) शीट में लिख देता है।
 */

function doPost(e) {
  try {
    // 1) JSON पार्स करें (Python payload में आपको payload["csv"] भेजा है)
    var requestData = JSON.parse(e.postData.contents);
    if (!requestData.csv) {
      throw new Error("Request JSON में 'csv' फ़ील्ड नहीं मिला।");
    }
    var csvText = requestData.csv.toString();

    // 2) CSV को 2D ऐरे में बदलें
    var allRows = Utilities.parseCsv(csvText);

    // 3) Spreadsheet और target शीट खोलें/बनाएँ
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = "Scraped Data"; // आप इसे “Csv to json” या जो भी नाम चाहते हों बदल सकते हैं
    var sheet = ss.getSheetByName(sheetName);

    if (sheet) {
      // अगर शीट है, तो पुराना डेटा साफ कर दें
      sheet.clear();
    } else {
      // अगर नहीं है, तो नई शीट बना लें
      sheet = ss.insertSheet(sheetName);
    }

    // 4) अब सब CSV रो एक ही बार में शीट में लिखें
    //    allRows.length = कितनी रो हैं, allRows[0].length = कितने कॉलम
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
