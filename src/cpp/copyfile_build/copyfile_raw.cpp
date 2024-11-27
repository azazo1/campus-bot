#include <shlobj.h>
#include <windows.h>
#include <Python.h>

// #define TEST_STR

int CopyFileToClipboard(PCWSTR filePath) {
    if (!OpenClipboard(nullptr)) {
        return 1;
    }

    if (!EmptyClipboard()) {
        CloseClipboard();
        return 2;
    }

    size_t wstrLen = wcslen(filePath);
    size_t totalSize = sizeof(DROPFILES) + (wstrLen + 2) * sizeof(WCHAR);
    HGLOBAL hGlobal = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, totalSize);
    if (!hGlobal) {
        CloseClipboard();
        return 3;
    }

    void *pData = GlobalLock(hGlobal);
    if (!pData) {
        GlobalFree(hGlobal);
        CloseClipboard();
        return 4;
    }

    auto pDropFiles = static_cast<LPDROPFILES>(pData);
    pDropFiles->fWide = TRUE;
    pDropFiles->pFiles = sizeof(DROPFILES);

    auto filePathDest = static_cast<char *>(pData) + sizeof(DROPFILES);
    memcpy(filePathDest,
           filePath,
           wstrLen * sizeof(WCHAR));
    filePathDest[wstrLen*sizeof(WCHAR)] = L'\0';
    filePathDest[(wstrLen + 1) * sizeof(WCHAR)] = L'\0';


    GlobalUnlock(hGlobal);

    if (!SetClipboardData(CF_HDROP, hGlobal)) {
        GlobalFree(hGlobal);
        CloseClipboard();
        return 5;
    }

    CloseClipboard();
    return 0;
}

int CopyFileToClipboard(PyObject *filePath_) {
    if (!PyBytes_Check(filePath_)) {
        PyErr_SetString(PyExc_TypeError, "filepath must be a bytes");
        return 10;
    }
    auto filePath_bytes = reinterpret_cast<PyBytesObject *>(filePath_);
    const auto filePath = reinterpret_cast<wchar_t *>(
        &filePath_bytes->ob_sval[0]
    );
#ifdef TEST_STR // 用于测试 cpp 是否正确接受了宽字符串.
    PyObject *unicodeObj = PyUnicode_DecodeUTF16(
        &filePath_bytes->ob_sval[0],
        PyBytes_GET_SIZE(filePath_bytes), "strict",
        nullptr
    );
    if (!PyUnicode_Check(unicodeObj)) {
        PyErr_SetString(PyExc_ValueError, "unicode decode error");
    } else {
        PyErr_SetString(PyExc_Exception, PyUnicode_AsUTF8(unicodeObj));
    }
    return 10;
#else
    return CopyFileToClipboard(filePath);
#endif
}
