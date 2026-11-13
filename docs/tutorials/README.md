# SDFlow 视频配套资料

老刀Cheney前 5 期视频的 HTML 画面与播放器。总入口为 [index.html](index.html)，每期说明页包含 B站、YouTube、博客和 HTML 连播入口。

## 本地浏览

直接打开 `index.html`；若浏览器限制本地嵌入页面，在本目录运行 `python3 -m http.server 8000`，访问 `http://localhost:8000`。无需安装 SDFlow 或运行示例项目。

## 内容范围

- 各期 HTML、CSS、JavaScript、画面图片和必要回放素材。
- 不包含完整视频、原声、制作评审、账号后台资料或完整开发会话。HTML 连播没有完整口播，观看讲解请使用视频入口。
- 保留历史画面及命令；使用工具时对照当前版本文档。终端画面不会执行本机命令。
- 录屏只导出页面实际使用的片段或静态帧，移除音轨；时间映射记录在 `media-excerpts.json`。第 1 期 S20 使用原片 185–221 秒；第 3 期按画面的分段与停帧导出；第 5 期使用原片 199–203 秒。

## 文件组织

`episodes.json` 记录各期标题和链接；各期目录中的 `index.html` 为说明页，`assets/html/player/play.html` 为播放器入口；`shared/fonts/` 保存共用字体与许可证。

## 许可证

项目自有页面与播放器沿用项目的 [Apache-2.0 许可证](LICENSE)，本目录保留许可证副本，方便独立分发。第三方 asciinema-player 的许可证保留在各期 `assets/html/lib/`；字体许可证保留在 `shared/fonts/`。引用内容的权利归原作者，页面中的来源标注保留。
