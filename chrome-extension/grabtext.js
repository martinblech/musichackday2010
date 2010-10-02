var txt = document.body.innerText;
$.post("http://localhost:8080/search", { "q": txt }, function(data) {
    alert(data);
});
