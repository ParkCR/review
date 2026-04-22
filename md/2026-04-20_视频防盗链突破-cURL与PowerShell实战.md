# 突破双重防盗链：从失败到成功的下载实战

**日期**：2026-04-20  
**标签**：🏷️ 视频下载, 🏷️ 防盗链, 🏷️ cURL, 🏷️ PowerShell, 🏷️ 一次性令牌  
**摘要**：解决网站Referer+Token双重防盗链的视频下载问题，通过复制浏览器请求实现成功下载。

## 📌 问题简述

- **现象**：网站可正常在线播放，但 IDM 捕获地址后提示“没有权限”（403 Forbidden）；浏览器扩展“猫抓”仅下载 5 秒无效视频；直接复制视频链接到 IDM 新建任务同样返回 403。
- **根本原因**：网站启用了 `Referer` 校验 + **一次性令牌（One-Time Token）**。令牌仅对浏览器的第一次请求有效，IDM/猫抓发起的第二次请求导致令牌失效。

## ⚖️ 核心对比：为什么 Video DownloadHelper 成功，而 IDM/猫抓失败？

| 特性     | IDM / 猫抓（失败）                                 | Video DownloadHelper（成功）               |
| -------- | -------------------------------------------------- | ------------------------------------------ |
| 工作位置 | 外部程序 / 扩展嗅探后重新请求                      | 浏览器扩展，拦截网络层数据                 |
| 请求方式 | 二次发起 HTTP 请求                                 | 直接复制浏览器已收到的数据流，不发起新请求 |
| 令牌处理 | 浏览器首次请求已消耗令牌，第二次请求令牌失效 → 403 | 与浏览器共享同一有效令牌，服务器无感知     |
| 适用场景 | 无令牌或静态链接                                   | 复杂防盗链、一次性令牌、HLS 流             |

> 📌 **补充说明**：对话中用户还尝试了 `FetchV` 扩展，同样不支持一次性令牌。最终通过浏览器开发者工具复制 cURL/PowerShell 命令并手动修正转义符，成功下载。

## 📄 关键证据：成功下载的核心命令（完整）

以下命令均源自对话中的实际成功案例，包含完整的请求头、Cookie（含 `cf_clearance` 令牌）和 `Referer`。

### ✅ CMD 环境（成功案例）

    curl "https://cdn.red52.kr/play/20260419/dc7f14ce-d62c-4a95-82ed-43c1fd752c06.mp4" ^
      -H "accept: */*" ^
      -H "accept-language: zh-CN,zh;q=0.9" ^
      -H "cache-control: no-cache" ^
      -b "user_device_id=9e5293cc5d924ce580aa89dfd6ee7c22; cf_clearance=95_BUgZKv3x_HSaluG3eGMVR6aPkUnq8doUiirkiRJQ-1776676427-1.2.1.1-eQYBCItj20FLg9l2iKZJVq.X_KW4mmLjZx0gYHeE5x2x4GlfkfzhDSCMHtp5mtrcIoEqiUcJP74tdPOSBCI1P4IgceadKUIppmcLzsv0dg.XU9sZyOK1GQC17y5QsSJ9ecFvsb00p3pBbcvy2smRQ.xDNYid8XfKZYlZZHKRsX_lLykT9qynoUACUgJlfL3TpUqPI0vIr.PuwMCRgN0_FcGXAqzT1NugMolKGhSarCgSOuTvi0XeuPIZooNgJyYb_ybZoQZD9N9anq0Wa1eOXzR7xaiyALSr2TvV8plzoK_rpVlMs_gdV_DOel4ZliYhJ5JT8thSOog2PBCYUOzUJw" ^
      -H "dnt: 1" ^
      -H "pragma: no-cache" ^
      -H "priority: i" ^
      -H "range: bytes=0-" ^
      -H "referer: https://red52.kr/" ^
      -H "sec-ch-ua: \"Chromium\";v=\"146\", \"Not-A.Brand\";v=\"24\", \"Google Chrome\";v=\"146\"" ^
      -H "sec-ch-ua-mobile: ?0" ^
      -H "sec-ch-ua-platform: \"Windows\"" ^
      -H "sec-fetch-dest: video" ^
      -H "sec-fetch-mode: no-cors" ^
      -H "sec-fetch-site: same-site" ^
      -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36" ^
      --output "%USERPROFILE%\Desktop\video.mp4"

> **注意**：从浏览器复制 `cURL (cmd)` 格式后，必须手动删除所有的 `^` 和反斜杠转义，使双引号保持正常。

### ✅ PowerShell 环境（成功案例）

    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    $session.Cookies.Add((New-Object System.Net.Cookie("user_device_id", "9e5293cc5d924ce580aa89dfd6ee7c22", "/", ".red52.kr")))
    $session.Cookies.Add((New-Object System.Net.Cookie("cf_clearance", "95_BUgZKv3x_HSaluG3eGMVR6aPkUnq8doUiirkiRJQ-1776676427-1.2.1.1-eQYBCItj20FLg9l2iKZJVq.X_KW4mmLjZx0gYHeE5x2x4GlfkfzhDSCMHtp5mtrcIoEqiUcJP74tdPOSBCI1P4IgceadKUIppmcLzsv0dg.XU9sZyOK1GQC17y5QsSJ9ecFvsb00p3pBbcvy2smRQ.xDNYid8XfKZYlZZHKRsX_lLykT9qynoUACUgJlfL3TpUqPI0vIr.PuwMCRgN0_FcGXAqzT1NugMolKGhSarCgSOuTvi0XeuPIZooNgJyYb_ybZoQZD9N9anq0Wa1eOXzR7xaiyALSr2TvV8plzoK_rpVlMs_gdV_DOel4ZliYhJ5JT8thSOog2PBCYUOzUJw", "/", ".red52.kr")))
    Invoke-WebRequest -UseBasicParsing -Uri "https://cdn.red52.kr/play/20260419/dc7f14ce-d62c-4a95-82ed-43c1fd752c06.mp4" `
    -WebSession $session `
    -Headers @{
      "authority"="cdn.red52.kr"
      "method"="GET"
      "path"="/play/20260419/dc7f14ce-d62c-4a95-82ed-43c1fd752c06.mp4"
      "scheme"="https"
      "accept"="*/*"
      "accept-encoding"="identity;q=1, *;q=0"
      "accept-language"="zh-CN,zh;q=0.9"
      "cache-control"="no-cache"
      "dnt"="1"
      "pragma"="no-cache"
      "priority"="i"
      "referer"="https://red52.kr/"
      "sec-ch-ua"="`"Chromium`";v=`"146`", `"Not-A.Brand`";v=`"24`", `"Google Chrome`";v=`"146`""
      "sec-ch-ua-mobile"="?0"
      "sec-ch-ua-platform"="`"Windows`""
      "sec-fetch-dest"="video"
      "sec-fetch-mode"="no-cors"
      "sec-fetch-site"="same-site"
    } -OutFile "$env:USERPROFILE\Desktop\video.mp4"

> **注意**：PowerShell 格式可直接使用，无需手动修改转义符，只需在末尾添加 `-OutFile` 指定保存路径。

## 🧭 决策流程图

1. **尝试浏览器扩展**（Video DownloadHelper / Stream Recorder）  
   ➡️ 2. **扩展失败** → 打开 F12 开发者工具 → Network 面板，筛选 `.mp4` 或 `.m3u8`  
   ➡️ 3. **右键请求** → 选择“复制为 cURL (cmd)”或“复制为 PowerShell 格式”  
   ➡️ 4. **修正命令**：  
   - cmd 格式：删除所有 `^` 和反斜杠转义，确保双引号正常  
   - PowerShell 格式：直接使用，末尾加 `-OutFile`  
   ➡️ 5. **执行命令** → 视频保存到指定路径

> 📌 若令牌极短（<10秒），可考虑 `yt-dlp --cookies-from-browser` 自动化刷新；若为 DRM 加密则此方法无效。

## 📊 适用场景速查表

| ✅ 此方法适用                       | ❌ 不适用场景                           |
| ---------------------------------- | -------------------------------------- |
| 一次性令牌（URL 带 token/expires） | Widevine / PlayReady DRM（Netflix等）  |
| Referer / Origin 校验              | 动态 JavaScript 加密地址（需逆向）     |
| Cookie / Session 验证              | 令牌刷新间隔小于命令执行时间（需脚本） |
| 普通 MP4 / HLS 无 DRM 流           | IP 地区限制（需配合代理）              |

## 🏆 成功配置复盘

- **最终方案**：从浏览器开发者工具中完整复制请求，转换为可执行的命令行脚本。
- **必须携带的请求头**：`Referer`、`User-Agent`、`Cookie`（包含 `cf_clearance` 等一次性令牌）。
- **输出参数**：`--output` (curl) 或 `-OutFile` (PowerShell) 指定保存路径。
- **环境变量差异**：CMD 使用 `%USERPROFILE%`，PowerShell 使用 `$env:USERPROFILE`。
- **结果**：成功下载完整 MP4 文件（大小正常，非 4.98KB 错误页面），绕过 Referer + 一次性令牌双重限制。

## 📌 核心收获

- 🔹 **一次性令牌是 IDM 类工具的克星**：任何二次发起的请求都会导致令牌失效，必须“偷看”浏览器的原始请求。
- 🔹 **浏览器扩展并非万能**：Video DownloadHelper 成功，但猫抓、FetchV 等因实现机制不同而失败，需针对性选择。
- 🔹 **开发者工具是最后的武器**：`Copy as cURL` + 手动修正转义符可以解决绝大多数非 DRM 防盗链。
- 🔹 **PowerShell 格式更友好**：无需手动删除大量 `^`，直接添加 `-OutFile` 即可使用。
- 🔹 **理解请求头的作用**：Referer、Cookie、User-Agent 缺一不可，服务器可能同时校验多个头部。

## 💡 归档建议

保存为 `2026-04-20_视频防盗链突破-cURL与PowerShell实战.md`  
本文档基于真实对话整理，补充部分已用 📌 标注。所有命令均经过验证有效。