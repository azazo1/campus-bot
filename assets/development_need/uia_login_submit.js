function desDecrypt(t, n) { // t 的值取 #login-croypto 的 innerHTML
    const e = ot.enc.Base64.parse(t);
    return ot.DES.decrypt(n, e, { // e 就是加密密钥, n 就是要加密的内容.
        mode: ot.mode.ECB,
        padding: ot.pad.Pkcs7
    }).toString(ot.enc.Utf8)
}

function submit() {
    const t = (null === (o = document.getElementById("login-croypto")) || void 0 === o ? void 0 : o.innerText) || "";
    const r = document.createElement("input");
    r.setAttribute("name", "password");
    r.setAttribute("value", desEncrypt(t, this.password));
    r.setAttribute("style", "display: none");
    document.forms[1].appendChild(r);
    document.forms[1].submit();
}