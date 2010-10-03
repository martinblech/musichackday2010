// The background page is asking us to find an address on the page.
if (window == top) {
  chrome.extension.onRequest.addListener(function(req, sender, sendResponse) {
    sendResponse(findText());
  });
}

var findText = function() {
    var text = document.body.innerText;
    return text;
}
