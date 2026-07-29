# 文件格式规范

> **定位声明**：本规范针对**文本文件的编码与换行符**，确保仓内所有文本文件格式一致，消除跨平台开发中的编码/换行符问题。

## 规则

### 1. 编码：统一 UTF-8

所有文本文件（代码、脚本、文档、配置）**必须**使用 UTF-8 编码，不带 BOM。

- 新建文件时确认编辑器使用 UTF-8
- 不得使用 GBK、GB2312、Latin-1 等其他编码
- `.editorconfig`（项目根）声明 `charset = utf-8`，编辑器自动遵守

### 2. 换行符：统一 LF

所有文本文件使用 LF (`\n`) 换行，**不用** CRLF (`\r\n`)。

- `.gitattributes` 配置 `* text=auto eol=lf`，git 层强制保证
- `.editorconfig` 声明 `end_of_line = lf`，编辑器层配合
- 例外：`.bat` 和 `.ps1`（Windows 原生脚本）使用 CRLF

### 3. 尾行换行

文件末尾**必须**有一个换行符（`insert_final_newline = true`）。

## 配置文件

| 文件 | 管什么 | 管在哪一层 |
|---|---|---|
| `.editorconfig` | 编码、缩进、换行符、尾行换行 | 编辑器层（写入时） |
| `.gitattributes` | 换行符归一化 | git 层（checkout/checkin 时） |

两者互补：`.editorconfig` 保证编辑器写出正确格式，`.gitattributes` 保证即使编辑器没配对、进入 git 后也会归一化。
