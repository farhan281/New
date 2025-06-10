function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var timestamp = new Date();

  if (!e || !e.postData || !e.postData.contents) {
    sheet.appendRow([timestamp, "❌ Invalid POST request"]);
    return ContentService.createTextOutput("Missing postData");
  }

  try {
    var data = JSON.parse(e.postData.contents);
    var url = data.url || "NO URL PROVIDED";
    var status_code = data.status_code || "NO STATUS CODE";
    sheet.appendRow([timestamp, url, status_code]);
    return ContentService.createTextOutput("✅ Success");
  } catch (error) {
    sheet.appendRow([timestamp, "❌ JSON parse error: " + error]);
    return ContentService.createTextOutput("JSON Error");
  }
}
