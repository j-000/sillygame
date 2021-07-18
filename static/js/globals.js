const SERVER = 'http://127.0.0.1:5000'

$.postJSON = function(url, data, callback) {
    return jQuery.ajax({
      'type': 'POST',
      'url': url,
      'contentType': 'application/json; charset=utf-8',
      'data': JSON.stringify(data),
      'dataType': 'json',
      'success': callback
    });
  };

$.getJSON = function(url, callback) {
  return jQuery.ajax({
    'type': 'GET',
    'url': url,
    'dataType': 'json',
    'success': callback
  });
};


function clearForm(formId){
  let f = document.getElementById(formId);
  Object.values(f.children).forEach(
    (e) => {
      if(e.tagName == 'INPUT'){
        e.value = ''
      }
    }
  );
}