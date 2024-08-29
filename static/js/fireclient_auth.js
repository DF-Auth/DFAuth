// Script to authenticate via FireClient (https://github.com/AlignedCookie88/FireClient/wiki/Authentication)

const public_key = document.getElementById("fireclient_auth_public_key").innerText;

const fcWS = new WebSocket("ws://localhost:39870");

const fc_redir_loc = document.getElementById("redir-loc").innerText;

let STATE = "waiting_for_welcome";

let connection_id = null;

fcWS.addEventListener("message", event => {
    var data = JSON.parse(event.data);
    if (STATE == "waiting_for_welcome") {
        welcome_received(data);
    } else if (STATE == "setting_identity") {
        identity_set(data);
    } else if (STATE == "authenticating") {
        auth_finished(data);
    }
})

function welcome_received(data) {
    connection_id = data["id"];
    console.log("Connected to FireClient API, id: "+connection_id);
    STATE = "setting_identity";
    fcWS.send(JSON.stringify({
        "type": "identify",
        "data": {
            "name": "DFAuth"
        }
    }));
}

function identity_set(data) {
    console.log("Identity set");
    STATE = "authenticating";
    fcWS.send(JSON.stringify({
        "type": "do_auth",
        "data": {
            "publicKey": public_key
        }
    }));
}

function auth_finished(data) {
    console.log("Auth finished!");
    STATE = "done";
    fcWS.close();
    secretKey = data["response"]["secretKey"];
    username = data["response"]["username"];

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            let response = JSON.parse(xmlHttp.responseText);
            let token = response["token"];
            var redir = redir_loc+"?token="+token;
            document.location.href = redir;
        }
    }
    xmlHttp.open("GET", "/.fireclient_auth_finish?secretKey="+encodeURIComponent(secretKey)+"&username="+username, true); // true for asynchronous 
    xmlHttp.send(null);
}