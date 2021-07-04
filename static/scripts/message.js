function getPosition(e) {
    var posx = 0;
    var posy = 0;

    if (!e) var e = window.event;

    if (e.pageX || e.pageY) {
        posx = e.pageX;
        posy = e.pageY;
    } else if (e.clientX || e.clientY) {
        posx = e.clientX + document.body.scrollLeft +
            document.documentElement.scrollLeft;
        posy = e.clientY + document.body.scrollTop +
            document.documentElement.scrollTop;
    }

    return {
        x: posx,
        y: posy
    }
}
var usernameh = "";
document.addEventListener("contextmenu", function (e) {
    if (e.target.className == "username") {
        e.preventDefault();
        let context = document.getElementById("context-username");
        context.hidden = false;
        menuPosition = getPosition(e);
        context.style.top = menuPosition.y;
        context.style.left = menuPosition.x;
        var username = e.target.id;
        usernameh = e.target.id;
        if (username == owner) {
            let owner2 = document.getElementById("owner");
            owner2.hidden = false;
        }
        else {
            let owner2 = document.getElementById("owner");
            owner2.hidden = true;
        }
    }
});
document.addEventListener("click", function (e) {
    let contextmen = e.target;
    let parent = contextmen.parentElement.parentElement.parentElement.className;
    if (e.target.parentElement.parentElement.className == "copyUser") {
        let context = document.getElementById("context-username");
        context.hidden = true;
    }
    else if (e.target.className != "context-username" && parent !="context-username") {
        let context = document.getElementById("context-username");
        context.hidden = true;
    }
})
document.addEventListener("contextmenu", function (e) {
    e.preventDefault();
    let contextmen = e.target;
    let parent = contextmen.parentElement.parentElement.parentElement.className;
    if (e.target.className != "username" && e.target.className !="context-username" && parent != "context-username") {
        let context = document.getElementById("context-username");
        context.hidden = true;
    }
})
document.getElementById("confirm-leave").style.display = "none";
document.getElementById("confirm-delete").style.display = "none";
function changeWindowSize() {
    var w = $(window).width();
    $('.chat-body').css('width', w);
    $('.chat-head').css('width', w);
    $('.chat-box').css('width', w);
}
changeWindowSize();
window.onresize = changeWindowSize;
var socket = io();
socket.on('connect', function () {
    socket.emit('connected', { data: 'I\'m connected!' });
});

var form = $("#copyUser").on("submit", function (e) {
    e.preventDefault();
})
var form = $("#owner").on("submit", function (e) {
    e.preventDefault();
})
var form = $("#remove").on("submit", function (e) {
    e.preventDefault();
    if (document.getElementById("confirm-leave").style.display == "flex") {
        let confirmlev = document.getElementById("confirm-delete")
        confirmlev.style.display = "flex";
        confirmlev.style.left = "200px";
        document.getElementById("confirm-leave").style.left = "-200px"
    }
    else {
        document.getElementById("confirm-delete").style.display = "flex";
    }
})
var form = $("#leave").on("submit", function (e) {
    e.preventDefault();
    if (document.getElementById("confirm-delete").style.display == "flex") {
        let confirmlev = document.getElementById("confirm-leave")
        confirmlev.style.display = "flex";
        confirmlev.style.left = "200px";
        document.getElementById("confirm-delete").style.left = "-200px"
    }
    else {
        document.getElementById("confirm-leave").style.display = "flex";
    }
})
var form = $("#confirm-leave-yes").on("click", function (e) {
    e.preventDefault();
    socket.emit("leave");
})
var form = $("#confirm-delete-yes").on("click", function (e) {
    e.preventDefault();
    socket.emit("remove");
})
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
socket.on("redirect", async function (content) {
    let url = content["url"]
    if (curruser == owner){
        if (content["alert"]) {
            document.getElementById("alert").hidden = false;
            for (let i = 3; i > 0; i--) {
                document.getElementById("alert").innerText = "The host has deleted the room, you will be redirected in " + i + " seconds";
                await sleep(1000);
            }
        }
    }
    window.location.replace(url)
})

var form = $("#SendMess").on("submit", function (e) {
    var w = $(window).width();
    $('.chat-body').css('width', w);
    $('.chat-head').css('width', w);
    $('.chat-box').css('width', w);
    e.preventDefault();
    let user_input = $("input.message").val();
    if (user_input.length == 0) {
        return;
    }
    socket.emit("message sent", {
        message: user_input,
        username: "bruh",
    });
    $("input.message").val("").focus();
});
var owner = "";
var curruser = "";
socket.on("get", function (content) {
    let content2 = content["content"];
    let author = content["author"];
    let time = content["time"];
    let username = content["username"];
    owner = content["owner"];
    let currentDiv = document.getElementById("msg-insert-right");
    for (let i = 0; i < content2.length; i++) {
        const div = document.createElement("div");
        const contentEl = document.createElement("h1");
        const timeEl = document.createElement("h2");
        const usernameEl2 = document.createElement("span");

        contentEl.textContent = content2[i];
        timeEl.textContent = time[i];
        usernameEl2.textContent = author[i];
        usernameEl2.id = author[i];
        usernameEl2.className = "username";
        curruser=username;

        div.append(usernameEl2);
        div.removeAttribute("span");
        div.append(timeEl);
        div.append(usernameEl2);
        div.append(contentEl);
        div.className = "msg-send";



        if (author[i] == username) {
            currentDiv = document.getElementById("msg-insert-right");
        }
        else {
            currentDiv = document.getElementById("msg-insert-left");
        }
        const body = document.getElementById("chat-body");
        currentDiv.append(div);
        timeEl.style.left += $("#" + author[i]).width() + 65;
        body.scrollTop = body.scrollHeight;
    }

});
socket.on("message recieved", function (content) {
    const div = document.createElement("div");
    let content2 = content["content"];
    let author = content["author"];
    let time = content["time"];
    let username = content["username"];
    let session = content["session"]

    let currentDiv = document.getElementById("msg-insert-left");

    div.textContent = ""

    const contentEl = document.createElement("h1");
    const timeEl = document.createElement("h2");
    const usernameEl = document.createElement("span");

    contentEl.textContent = content2;
    timeEl.textContent = time;

    usernameEl.textContent = author;
    usernameEl.id = author;
    usernameEl.className = "username";

    div.append(usernameEl);
    div.removeAttribute("span");
    div.append(timeEl);
    div.append(usernameEl);
    div.append(contentEl);
    div.className = "msg-send";

    if (author == username) {
        currentDiv = document.getElementById("msg-insert-right");
    }
    else {
        currentDiv = document.getElementById("msg-insert-left");
    }
    const body = document.getElementById("chat-body");
    const top = document.getElementById("chat-head");
    currentDiv.append(div);
    timeEl.style.left += $(".username").width() + 65;
    body.style.height = top.style.height;
    body.scrollTop = body.scrollHeight;

});