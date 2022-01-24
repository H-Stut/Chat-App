function dropDown() {
    if (curruser == owner) {
        document.getElementById("bannedUsersSearch").classList.toggle("show");
        var div = document.getElementById("arrow1");
        var div2 = document.getElementById("arrow2");
        let deg = getRotationAngle(div);
        let deg2 = getRotationAngle(div2);
        deg += 90;
        deg2 += 90;
        div.style.transform = "rotate(" + deg + "deg)"
        div2.style.transform = "rotate(" + deg2 + "deg)"
    }
}

function getRotationAngle(target) {
    const obj = window.getComputedStyle(target, null);
    const matrix = obj.getPropertyValue('-webkit-transform') ||
        obj.getPropertyValue('-moz-transform') ||
        obj.getPropertyValue('-ms-transform') ||
        obj.getPropertyValue('-o-transform') ||
        obj.getPropertyValue('transform');

    let angle = 0;

    if (matrix !== 'none') {
        const values = matrix.split('(')[1].split(')')[0].split(',');
        const a = values[0];
        const b = values[1];
        angle = Math.round(Math.atan2(b, a) * (180 / Math.PI));
    }

    return (angle < 0) ? angle += 360 : angle;
}
function filterFunction() {
    var input, filter, ul, li, a, i;
    input = document.getElementById("bannedSearchInput");
    filter = input.value.toUpperCase();
    div = document.getElementById("bannedUsersSearch");
    a = div.getElementsByClassName("show");
    for (i = 0; i < a.length; i++) {
        txtValue = a[i].textContent || a[i].innerText;
        txtValue = txtValue.toUpperCase();
        if (txtValue.search(filter) == 0) {
            a[i].style.display = "";
        }
        else {
            a[i].style.display = "none";
        }
    }
}
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
let search = function (arr, x, start, end) {
    if (start > end) return false;
    let mid = Math.floor((start + end) / 2);
    if (arr[mid] === x) return true;
    if (arr[mid] > x)
        return search(arr, x, start, mid - 1);
    else
        return search(arr, x, mid + 1, end);
}
let id = "";
let usertounban = "";
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

    let rect = context.getBoundingClientRect();

    if (rect.bottom > window.innerHeight){
        context.style.top = window.innerHeight - rect.height;
    }



    let target = null;

    if (e.target.className == "content") {
        document.getElementById("copyText").hidden = false;

        if (e.target.parentElement.children[1].id == curruser || curruser == owner) {
            document.getElementById("deleteMess").hidden = false;
            id = e.target.parentElement.children[3].id;
        }
        if (e.target.parentElement.children[1].id == curruser) {
            document.getElementById("editMes").hidden = false;
            id = e.target.parentElement.children[3].id;
        }

        return;
    }
    else if (e.target.parentElement.id == "user") {
        target = e.target.parentElement.className;
    }
    else if (e.target.className == "username") {
        target = e.target.id;
    }
    else if (e.target.className == "show") {
        target = e.target.id;
        let unban = document.getElementById("unban");
        document.getElementById("copyUser").hidden = false;
        unban.hidden = false;
        usertounban = target;
        return;
    }
    else {
        context.hidden = true;
    }
    let kick = document.getElementById("kick");
    let ban = document.getElementById("ban");
    document.getElementById("copyUser").hidden = false;
    let owner2 = document.getElementById("owner");

    var username = target;
    if (username == owner) {
        owner2.hidden = false;
    }
    else {
        owner2.hidden = true;
    }
    if (curruser == owner && target != curruser) {
        ban.hidden = false;
        usertokick = target;
    }
    else {
        ban.hidden = true;
    }
    if (search(users, username, 0, users.length) && username != owner && curruser == owner) {
        kick.hidden = false;
        usertokick = target
    }
    else {
        kick.hidden = true;
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
var socket = io();
function changeWindowSize() {
    var w = $(window).width();
    $('.chat-body').css('width', w);
    $('.chat-head').css('width', w);
    $('.chat-box').css('width', w);
}
changeWindowSize();
window.onresize = changeWindowSize;
socket.on("connect", function () {
    socket.emit("connected")
})
socket.on("disconnect", function() {
    socket.emit("discnnected")
})

socket.on("pfps", function (content) {
    for (let i = 0; i < content["pfps"].length; i++) {
        if (content["pfps"][i] == ""){
            continue;
        }
        let pfpDiv = document.createElement("div")
        pfpDiv.id = "imageWrapper";
        pfpDiv.className = "imageWrapper";
        let pfpImg = document.createElement("img");
        pfpImg.id = "display-image";
        pfpImg.src = content["pfps"][i];
        pfpImg.className = "display-image";

        pfpDiv.append(pfpImg);
        let div2Get = document.getElementsByClassName(users[i])
        try {
            if (div2Get[0].children.length == 1) {
                div2Get[0].appendChild(pfpDiv)
            }
        }
        catch {

        }


        var mess = document.getElementsByClassName("msg-send")
        for (let j = 0; j < mess.length; j++) {
            if (mess[j].children[1].id == users[i]) {
                let pfpDiv_to_add = document.createElement("div")
                pfpDiv_to_add.id = "imageWrapper"
                pfpDiv_to_add.className = "imageWrapper2"
                let img = document.createElement("img");
                img.id = "display-image";
                img.src = content["pfps"][i];
                img.className = "display-image"
                pfpDiv_to_add.appendChild(img)
                mess[j].appendChild(pfpDiv_to_add)
            }
        }
    }

})

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

let temp;
let new2;
var form = $("#editMes").on("submit", function (e) {
    e.preventDefault();

    document.getElementById("context-username").hidden = true;
    let div = document.getElementById(id);
    let children = div.parentElement.children;

    temp = children[2];

    let d = document.createElement("div");
    d.id = "editText";
    d.className = "content";
    d.innerHTML = children[2].innerHTML;
    d.setAttribute("contentEditable", "true");

    let h3 = document.createElement("h3");
    h3.id = "charCount";
    h3.className = "charCount";
    h3.textContent = temp.textContent.length + "/2000";
    h3.setAttribute("contentEditable", "false");

    newText = temp.textContent;

    children[2].parentNode.replaceChild(d, children[2]);
    children[2].parentNode.appendChild(h3);

    d.focus();

    new2 = d;

    document.getElementById("editText").onkeydown = onKeyDown;
    document.getElementById("editText").onkeyup = onKeyUp;
})
let newText = "";
document.onkeydown = onKeyDown2;
function onKeyDown2(e) {
    let charCount = document.getElementById("charCount");
    if (temp == undefined) {
        return;
    }
    try {
        if (e.key == "Escape") {
            new2.parentElement.replaceChild(temp, new2);
            charCount.remove();
        }
    }
    catch {

    }

}
function onKeyUp(e) {
    let charCount = document.getElementById("charCount");
    charCount.textContent = e.target.textContent.length + "/2000";
    if (e.target.textContent.length > 2000) {
        charCount.style.color = "red";
    }
    else {
        charCount.style.color = "white";
    }
}
function onKeyDown(e) {
    let charCount = document.getElementById("charCount");
    charCount.textContent = e.target.textContent.length + "/2000";
    if (e.target.textContent.length > 2000) {
        charCount.style.color = "red";
    }
    else {
        charCount.style.color = "white";
    }
    if (e.key == "Enter" && !e.shiftKey) {
        newText = e.target.textContent;
        e.preventDefault();
        if (newText.length == 0) {
            return;
        }
        if (newText.length > 2000) {
            return;
        }
        temp.textContent = newText;
        e.target.parentElement.replaceChild(temp, e.target);
        charCount.remove();
        socket.emit("edit message", {
            "id": id,
            "text": newText
        })
    }
    else if (e.key == "Escape") {
        e.target.parentElement.replaceChild(temp, e.target);
        charCount.remove();
    }
}
var form = $("#kick").on("submit", function (e) {
    e.preventDefault();
    socket.emit("kick", {
        "username": usertokick
    })
    document.getElementById("context-username").hidden = true;
})
var form = $("#ban").on("submit", function (e) {
    e.preventDefault();
    socket.emit("ban", {
        "username": usertokick
    })
    document.getElementById("context-username").hidden = true;
})
var form = $("#unban").on("submit", function (e) {
    e.preventDefault();
    usertounban = usertounban.trimStart();
    socket.emit("unban", {
        "username": usertounban
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
function isElementInViewport(el) {
    var rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}
let wrapper = document.getElementById("chat-body");
wrapper.onscroll = msgLoader;
let toScroll;
let scrollPos;
let scrollHeight;
let temp_stop;
function msgLoader(event) {
    if (finish || temp_stop) return
    test = document.getElementById("chat-body");
    scrollPos = test.scrollTop;
    scrollHeight = test.scrollHeight;
    elem = document.getElementsByClassName("msg-send")
    if (isElementInViewport(elem[0])) {
        socket.emit("get messages", {
            "counter": counter
        })
        temp_stop = true;
    }
}

let finish = false
socket.on("appendMess", function (content) {
    finish = content["finished"]
    if (finish) return
    for (let i = content.messages.length - 1; i >= 0; i--) {
        const element = content.messages[i];
        div = createMsgDiv(element, false);
        counter++;
    }
    socket.emit("get pfp", {
        "users": users
    });
    let chatBody = document.getElementById("chat-body");
    let scrollAmount = (chatBody.scrollHeight - scrollHeight) + scrollPos;
    $("#chat-body").scrollTop(scrollAmount)
    temp_stop = false
})

//socket.on("")
let canMessage = true;
socket.on("redirect", async function (content) {
    canMessage = false;
    let url = content["url"];
    let text = content["text"];
    if (curruser != owner) {
        if (content["alert"]) {
            document.getElementById("alert").hidden = false;
            for (let i = 3; i > 0; i--) {
                document.getElementById("alert").innerText = text + "you will be redirected in " + i + " seconds";
                await sleep(1000);
            }
        }
    }
    window.location.replace(url)
})
let users = [];
socket.on("user leave", function (content) {
    if (!canMessage) {
        return;
    }
    let user = content["user"];
    users.splice(users.findIndex(client => client == user), 1);
    try {
        let rem = document.getElementsByClassName(user)
        rem[0].remove();
    }
    catch {
    }
})

socket.on("user join", function (content) {
    if (!canMessage) {
        return;
    }
    let user = content["user"];
    let length = document.getElementsByClassName(user).length;
    if (length == 0) {
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
    socket.emit("get pfp", {
        "users": users
    });
})
var form = $("#SendMess").on("submit", function (e) {
    e.preventDefault();
    if (!canMessage) {
        return;
    }
    var w = $(window).width();
    $('.chat-body').css('width', w);
    $('.chat-head').css('width', w);
    $('.chat-box').css('width', w);
    let user_input = $("input.message").val();
    if (user_input.length == 0) {
        return;
    }
    socket.emit("message sent", {
        "message": user_input,
    });
    $("input.message").val("").focus();
});
var owner = "";
var curruser = "";
var ids = [];
let match = 0
socket.on("check status", () => {
    socket.emit("socket active");
})
socket.on("user ban", function (content) {
    let banDiv = document.getElementById("banList");
    let toReplace = document.createElement("p");
    toReplace.id = " " + content["user"];
    toReplace.className = "show";
    toReplace.innerText = content["user"];
    banDiv.appendChild(toReplace);
})
socket.on("unbanned", function (content) {
    let classname = document.getElementsByClassName("show");
    content["user"] = " " + content["user"];
    for (let i = 0; i < classname.length; i++) {
        const name = classname[i];
        if (content["user"] == name.id) {
            name.remove();
        }

    }
});
function createMsgDiv(content, append) {
    let content2 = content["content"];
    let author = content["author"];
    let time = content["time"];
    let id = content["id"]

    ids.push(id);
    const div = document.createElement("div");
    const contentEl = document.createElement("h1");
    const timeEl = document.createElement("h2");
    const usernameEl2 = document.createElement("span");
    const testID = document.createElement("div");

    var date = new Date(time * 1000);
    var day = date.getDate();
    var month = date.toDateString().split(' ')[1]
    var year = date.getFullYear();
    var time3 = date.toLocaleTimeString().split(':');
    var hours = time3[0] + ":" + time3[1]
    var dayofWeek = date.toDateString().split(' ')[0]

    contentEl.textContent = content2;
    timeEl.textContent = dayofWeek + " " + day + " " + month + " " + year + " " + hours;
    usernameEl2.textContent = author;
    usernameEl2.id = author;
    usernameEl2.className = "username";
    contentEl.className = "content";
    testID.id = id;
    div.append(usernameEl2);
    div.removeAttribute("span");
    div.append(timeEl);
    div.append(usernameEl2);
    div.append(contentEl);
    div.append(testID);
    div.className = "msg-send";
    let currentDiv = document.getElementById("msg-insert");


    const body = document.getElementById("chat-body");
    if (append){
        currentDiv.append(div);
    }
    else{
        currentDiv.prepend(div);
    }
    let timeEL = div.children[0];
    timeEL.style.left += $("#" + author).width() + 65;
    body.scrollTop = body.scrollHeight;

    return div;

}
function createUsrDiv(user) {
    let div = document.createElement("div");
    let text = document.createElement("p");
    text.textContent = user;
    div.append(text);
    div.id = "user";
    div.className = user;
    return div;
}
function getUserPFPs(message_data, users) {
    if (message_data) {
        message_data.forEach(message => {
            user = message.author;
            if (!users.includes(user)) {
                users.push(user);
            }
        });
    }
    socket.emit("get pfp", {
        "users": users
    });
}
function createBanDiv(bans) {
    for (let i = 0; i < bans.length; i++) {
        const ban = bans[i];
        let banDiv = document.getElementById("banList");
        let line = document.createElement("div");
        line.id = "line2";
        line.className = "line2";
        let toReplace = document.createElement("p");
        toReplace.id = " " + ban;
        toReplace.className = "show";
        toReplace.innerText = ban;
        banDiv.appendChild(toReplace);
        if (i != bans.length - 1) {
            banDiv.appendChild(line);
        }
    }
}
function showOwnerContent(owner){
    if (curruser == owner) {
        document.getElementById("bannedUsers").hidden = false;
        document.getElementById("dropButton").hidden = false;
        document.getElementById("arrow1").hidden = false;
        document.getElementById("arrow2").hidden = false;
    }
}
let counter = 0;
let message_data;
socket.on("get", function (content) {
    curruser = content["username"];
    
    users = content["users"];
    bans = content["bans"];
    owner = content["owner"];
    message_data = content["message_data"];

    if (message_data) {
        message_data.forEach(message => {
            div = createMsgDiv(message, true);
            counter++;
        });
    }
    users.forEach(user => {
        if ($("." + user).length < 1){
            let currentDiv = document.getElementById("users");
            let div = createUsrDiv(user);
            currentDiv.append(div);
        }
    });
    getUserPFPs(message_data, users);
    createBanDiv(bans);
    showOwnerContent(owner);
});
socket.on("message deleted", function (content) {
    if (!canMessage) {
        return;
    }
    if (content["large"]) {
        content["id"].forEach(id => {
            let usern = document.getElementById(id);
            let div = usern.parentElement;
            div.remove();
        });
    }
    else {
        let id2 = content["id"];
        let usern = document.getElementById(id2);
        let div = usern.parentElement;
        div.remove();
    }
    counter--;

})
socket.on("message edited", function (content) {
    if (!canMessage) {
        return;
    }
    let id2 = content["id"];
    let text = content["text"];
    let mesCont = document.getElementById(id2);
    mesCont.parentElement.children[2].textContent = text;
})