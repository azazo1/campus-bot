document.addEventListener("DOMContentLoaded", function () {
    const slider = document.getElementById("notice-slider");
    const valueDisplay = document.getElementById("notice-value");
    const saveBtn = document.getElementById("save-btn");

    // 按照 toml 中的配置加载初始值
    fetch("/api/get_param")
        .then(response => response.json())
        .then(data => {
            slider.value = data.value;
            valueDisplay.textContent = data.value;
        });

    // 实时更新滑动框的值
    slider.addEventListener("input", () => {
        valueDisplay.textContent = slider.value;
    });

    // 保存配置
    saveBtn.addEventListener("click", () => {
        fetch("/api/set_param", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ value: slider.value })
        })
        .then(response => response.json())
        .then(data => {
            alert(`The new value is：${data.new_value} seconds`);
        })
        .catch(error => {
            alert("Save Error! Please try again later.");
            console.error(error);
        });
    });
});
