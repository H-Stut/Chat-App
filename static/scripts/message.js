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
let recursiveFunction = function (arr, x, start, end) {
    if (start > end) return false;
    let mid = Math.floor((start + end) / 2);
    if (arr[mid] === x) return true;
    if (arr[mid] > x)
        return recursiveFunction(arr, x, start, mid - 1);
    else
        return recursiveFunction(arr, x, mid + 1, end);
}
content = "";

let id = "";

document.addEventListener("contextmenu", function (e) {
    e.preventDefault();
    let context = document.getElementById("context-username");
    let children = context.children;
    for (let i = 0; i < children.length; i++) {
        if (children[i].id != "line1") {
            children[i].hidden = true;
        }
    }

    menuPosition = getPosition(e);
    context.style.top = menuPosition.y;
    context.style.left = menuPosition.x;

    context.hidden = false;

    if (e.target.className == "content") {
        content = e.target.textContent;
        document.getElementById("copyText").hidden = false;

        if (e.target.parentElement.children[1].id == curruser || curruser == owner) {
            document.getElementById("deleteMess").hidden = false;
            id = e.target.parentElement.children[3].id;
        }
    }
    else if (e.target.className == "username") {
        let kick = document.getElementById("kick");
        document.getElementById("copyUser").hidden = false;
        let owner2 = document.getElementById("owner");

        var username = e.target.id;
        usernameh = e.target.id;

        if (username == owner) {
            owner2.hidden = false;
        }
        else {
            owner2.hidden = true;
        }

        if (recursiveFunction(users, username, 0, users.length - 1) && username != owner && curruser == owner) {
            kick.hidden = false;
            usertokick = e.target.id
        }
        else {
            kick.hidden = true;
        }
    }
    else {
        context.hidden = true;
    }
});
let usertokick = "";
document.addEventListener("click", function (e) {
    try {
        contextmen = e.target.parentElement.parentElement.parentElement;
        if (contextmen.className == "context-username" || contextmen.className == "") {
            return;
        }
    }
    catch {
        if (e.target == "context-username") {
            return;
        }
        else {
            document.getElementById("context-username").hidden = true;
            return;
        }
    }
    document.getElementById("context-username").hidden = true;
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
    socket.emit('connected', {
        "timezone": new Date().getTimezoneOffset()
    });
    let div = document.createElement("div");
    let currentDiv = document.getElementById("users")
    let text = document.createElement("p");
    text.textContent = curruser;
    div.append(text);
    div.id = "user";
    div.className = curruser
    if (div.className == "undefined" || div.className == "") {
        return;
    }
    currentDiv.append(div)
});

var form = $("#copyUser").on("submit", function (e) {
    e.preventDefault();
    document.getElementById("context-username").hidden = true;
})
var form = $("#copyText").on("submit", function (e) {
    e.preventDefault();
    document.getElementById("context-username").hidden = true;
})
var form = $("#deleteMess").on("submit", function (e) {
    e.preventDefault();
    socket.emit("delete message", {
        "id": id
    })
    document.getElementById("context-username").hidden = true;
})
var form = $("#kick").on("submit", function (e) {
    e.preventDefault();
    socket.emit("kick", {
        "username": usertokick
    })
    document.getElementById("context-username").hidden = true;
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
        document.getElementById("confirm-delete").style.left = "0px"
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
        document.getElementById("confirm-leave").style.left = "0px"
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
    if (curruser == owner) {
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
let users = [];
socket.on("user leave", function (content) {
    let user = content["user"];
    for (let i = 0; i < users.length; i++) {
        if (users[i] == user) {
            let rem = document.getElementsByClassName(user)
            rem[0].remove();
            users.splice(i, 1);
        }
    }
})

socket.on("user join", function (content) {
    let user = content["user"];
    let found = false;
    for (let i = 0; i < users.length; i++) {
        if (users[i] == user) {
            found = true;
            break;
        }
    }
    if (!found) {
        users.push(user);
        let div = document.createElement("div");
        let currentDiv = document.getElementById("users")
        let text = document.createElement("p");
        text.textContent = user;
        div.append(text);
        div.id = "user";
        div.className = user
        if (div.className == "undefined") {
            return;
        }
        currentDiv.append(div)
    }
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
        "message": user_input,
        "username": "bruh",
        "timezone": new Date().getTimezoneOffset()
    });
    $("input.message").val("").focus();
});
var owner = "";
var curruser = "";
var ids = [];
socket.on("get", function (content) {
    let content2 = content["content"];
    let author = content["author"];
    let time = content["time"];
    let username = content["username"];
    users = content["users"];
    owner = content["owner"];
    ids = content["ids"];

    let currentDiv = document.getElementById("msg-insert");
    for (let i = 0; i < content2.length; i++) {
        let div2 = document.createElement("div");
        let currentDiv2 = document.getElementById("users")
        let text = document.createElement("p");
        text.textContent = users[i];
        div2.append(text);
        div2.id = "user";
        div2.className = users[i];
        if (div2.className != "undefined") {
            currentDiv2.append(div2)
        }

        const div = document.createElement("div");
        const contentEl = document.createElement("h1");
        const timeEl = document.createElement("h2");
        const usernameEl2 = document.createElement("span");
        const testID = document.createElement("div");

        contentEl.textContent = content2[i];
        timeEl.textContent = time[i];
        usernameEl2.textContent = author[i];
        usernameEl2.id = author[i];
        usernameEl2.className = "username";
        contentEl.className = "content";
        testID.id = ids[i];
        curruser = username;

        div.append(usernameEl2);
        div.removeAttribute("span");
        div.append(timeEl);
        div.append(usernameEl2);
        div.append(contentEl);
        div.append(testID);
        div.className = "msg-send";

        const body = document.getElementById("chat-body");
        currentDiv.append(div);
        timeEl.style.left += $("#" + author[i]).width() + 65;
        body.scrollTop = body.scrollHeight;
    }

});

socket.on("message deleted", function (content) {
    let id2 = content["id"];
    let usern = document.getElementById(id2);
    let div = usern.parentElement;
    div.remove();
})

socket.on("message recieved", function (content) {
    const div = document.createElement("div");
    let content2 = content["content"];
    let author = content["author"];
    let time = content["time"];
    ids.push(content["id"]);

    let currentDiv = document.getElementById("msg-insert");

    div.textContent = ""

    const contentEl = document.createElement("h1");
    const timeEl = document.createElement("h2");
    const usernameEl = document.createElement("span");
    const testID = document.createElement("div");

    contentEl.textContent = content2;
    timeEl.textContent = time;
    testID.id = content["id"];

    usernameEl.textContent = author;
    usernameEl.id = author;
    usernameEl.className = "username";
    contentEl.className = "content";

    div.append(usernameEl);
    div.removeAttribute("span");
    div.append(timeEl);
    div.append(usernameEl);
    div.append(contentEl);
    div.append(testID);
    div.className = "msg-send";

    const body = document.getElementById("chat-body");
    const top = document.getElementById("chat-head");
    currentDiv.append(div);
    timeEl.style.left += $("#" + author).width() + 65;
    body.style.height = top.style.height;
    body.scrollTop = body.scrollHeight;

});