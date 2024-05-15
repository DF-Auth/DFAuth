
const wsAddress = document.getElementById("ws_address").innerText;
const ws = new WebSocket(wsAddress);

const code = document.getElementById("code").innerText;

const redir_loc = document.getElementById("redir-loc").innerText;

ws.addEventListener("open", (event) => {
    ws.send(code)
})

ws.addEventListener("message", (event) => {
    var data = JSON.parse(event.data);
    var type = data["type"];
    if (type == "ping") {
        console.log("ping");
        ws.send("ping");
    } else if (type == "ready") {
        var ready_token = data["token"];
        console.log("READY");
        var redir = redir_loc+"?token="+ready_token
        console.log(redir);
        document.location.href = redir;
    } else {
        console.log(data);
    }
})