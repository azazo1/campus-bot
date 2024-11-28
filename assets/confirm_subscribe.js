// 确认预约的加密操作, 结合注释分析这部分代码.
function used_by_service(config) {
    let encryptRequest = ["/api/login/resetpass", "/api/login/login", "/api/login/forget", "/api/Seat/confirm", "/api/Seminar/confirm", "/reserve/index/confirm", "/api/Enter/confirm", "/api/Seat/touch_qr_books", "/api/seat/qrcode", "/api/seat/qrcode_not_card", "/api/Study/StudyOrder", "/api/login/updateUserInfo", "/api/seat/xuzuoconfirm"];
    let token = sessionStorage.getItem("token") || "";
    let lang = localStorage.getItem("lang") || "zh";
    if (token) {
        config.headers.authorization = `bearer${token}`;
        config.headers.lang = lang;
        if (config != null && config.customHeaders) {
            config.headers = {...config.headers, ...config.customHeaders};
        }
        delete config.customHeaders;
        if (encryptRequest.includes(config.url)) {
            // 加密操作发生的位置, encrypt 函数见本文件后半部分.
            let g = encrypt("encrypt", config.data);
            config.data = {
                aesjson: g // 加密的数据存储到 aesjson 中.
            }
        }
        config.data = {
            ...eval(config.data),
            authorization: config.headers.authorization
        }
    } else {
        if (encryptRequest.includes(config.url)) {
            let g = encrypt("encrypt", config.data);
            config.data = {
                aesjson: g
            }
        }
        config.data = {
            ...eval(config.data)
        }
    }
    if (!config.customLoading) {
        let g = sessionStorage.getItem("axiosReq")
            , y = [];
        Toast.loading({
            message: config.loadingMsg,
            forbidClick: !0,
            duration: 0
        }),
            g ? y = [...JSON.parse(g), config == null ? void 0 : config.url] : y = [config == null ? void 0 : config.url],
            y = [...new Set(y)],
            sessionStorage.setItem("axiosReq", JSON.stringify(y))
    }
    return config
}

// 加密数据函数.
function encrypt(g, y) {
    // exchangeDateTime 见下文.
    var k = exchangeDateTime(new Date, 41);
    // .split("") 就是按照每个字符分割字符串.
    k = `${k}${k.split("").reverse().join("")}`; // AES 密钥.
    // 调试发现 k 可能为 "2024112882114202", 就是当前日期年月日这个字符串和他的倒转相加.
    var j = k;
    var pe = "ZZWBKJ_ZHIHUAWEI"; // AES iv 向量.
    if (g == "encrypt")
        // 加密操作, 见下文.
        return crypto.encrypt(JSON.stringify(y), j, pe);
    if (g == "decrypt") {
        console.log("decrypt", y, j, pe);
        return crypto.decrypt(y, j, pe)
    }
}

// cryptoJs 内的加密算法见下, 其实加密的全部就在这了, 后面就是库内容, 统一的, 调用的是 CryptoJS 库, 可以看看它的文档.
const CryptoJS = cryptoJs.exports
const crypto = {
    encrypt(g, j, pe) { // 这里的 j 就是密钥, 就是上文 encrypt 中的 k 变量.
        // CryptoJS.enc.Utf8.parse 是 CryptoJS 中的一个方法, 用于将普通字符串转换为 CryptoJS 的 WordArray 对象, 不涉及加密操作.
        var j = CryptoJS.enc.Utf8.parse(j);
        var pe = CryptoJS.enc.Utf8.parse(pe);
        var Ce = CryptoJS.AES.encrypt(g, j, { // CryptoJS.AES.encrypt(message, key, options)
            iv: pe,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        return Ce.toString()
    },
    decrypt(g, y, k) {
        var j = CryptoJS.enc.Utf8.parse(y)
            , pe = CryptoJS.enc.Utf8.parse(k)
            , Ce = CryptoJS.AES.decrypt(g, j, {
            iv: pe,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        return Ce.toString(CryptoJS.enc.Utf8)
    }
};
// cryptoJs 在此定义.
(function (g, y) {
        (function (k, j, pe) {
                g.exports = j(requireCore(), requireX64Core(), requireLibTypedarrays(), requireEncUtf16(), requireEncBase64(), requireEncBase64url(), requireMd5(), requireSha1(), requireSha256(), requireSha224(), requireSha512(), requireSha384(), requireSha3(), requireRipemd160(), requireHmac(), requirePbkdf2(), requireEvpkdf(), requireCipherCore(), requireModeCfb(), requireModeCtr(), requireModeCtrGladman(), requireModeOfb(), requireModeEcb(), requirePadAnsix923(), requirePadIso10126(), requirePadIso97971(), requirePadZeropadding(), requirePadNopadding(), requireFormatHex(), requireAes(), requireTripledes(), requireRc4(), requireRabbit(), requireRabbitLegacy(), requireBlowfish())
            }
        )(commonjsGlobal, function (k) {
            return k
        })
    }
)(cryptoJs);

// 加密函数中用到.
const exchangeDateTime = (g /*new Date*/, y = "" /*41*/) => {
    let k = useLanguage();
    switch (y) {
        case 43:
            return hooks(g).format("HH:mm:ss");
        case 42:
            return k == "zh" ? hooks(g).format("YYYY\u5E74MM\u6708DD\u65E5") : hooks(g).format("DD MMM YYYY");
        case 41:
            return hooks(g).format("YYYYMMDD"); // 这行.
        case 40:
            return hooks(g).format("MM-DD");
        case 39:
            return hooks(g).format("YYYY-MM");
        case 38:
            return k == "zh" ? hooks(g).format("MM\u6708DD\u65E5") : hooks(g).format("DD MMM");
        case 37:
            return hooks(g).format("DD MMM YYYY h:mm A");
        case 36:
            return hooks(g).format("DD-MM-YYYY H:mm A");
        case 35:
            return hooks(g).format("DD/MM/YYYY H:mm A");
        case 34:
            return hooks(g).format("DD/MM/YYYY H:mm");
        case 33:
            return hooks(g).format("HH:mm");
        case 32:
            return hooks().isSame(g, "day");
        case 31:
            return hooks(g).format("dddd");
        case 30:
            return hooks(g).format("DD-MM-YYYY");
        case 29:
            return hooks().format("DD MMM YYYY, hh:mma");
        case 28:
            return hooks(g).valueOf();
        case 27:
            return hooks(g).add(3, "year");
        case 26:
            return hooks(hooks(g).format("YYYY-MM-DD")).valueOf();
        case 25:
            return hooks(g).add(1, "day");
        case 24:
            return hooks(g).format("dd MMM DD YYYY");
        case 23:
            return hooks(g).format("YYYY-MM-DD HH:mm:ss");
        case 22:
            return hooks(g).format("DD MMM YYYY,HH:mm");
        case 20:
            return hooks(g).format("DD MMM YYYY,ddd");
        case 18:
            return hooks(g).format("DD MMM YYYY");
        case 17:
            return hooks(g).format("DD MMMM YYYY,ddd");
        case 16:
            return hooks(g).valueOf();
        case 15:
            return hooks(g).format("MMMM YYYY");
        case 14:
            return hooks(g).format("YYYY-MM-DD H:mm:ss");
        case 13:
            return hooks(g).format("DD MMMM YYYY, HH:mm");
        case 12:
            return hooks(g).toDate();
        case 11:
            return hooks(g).format("dddd, DD MMMM YYYY");
        case 10:
            return hooks(g).day();
        case 9:
            return hooks(g).format("DD MMMM YYYY");
        case 8:
            return hooks(g).format("HH:mm");
        case 7:
            return hooks(g).format("DD MMM H:mm A");
        case 6:
            return hooks(g).format("H:mm a");
        case 5:
            return hooks(g).format("DD MMM");
        case 4:
            return hooks(g).format("dddd");
        case 3:
            return hooks(g).format("YYYY-MM-DD H:mm");
        case 2:
            return hooks(g).format("YYYY-MM-DD");
        case 1:
            return hooks(g).format("H:mm");
        default:
            return hooks(g).format("DD/MM/YYYY")
    }
}