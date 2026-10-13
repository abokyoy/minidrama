# 官方 H3 原版 DiT 模型 —— 下载清单

> 生成时间：2026-10-06 21:00
> 数据来源：Hugging Face 官方 API 实时查询（不是凭记忆）

## 需要下载的文件（就这一个）

| 项 | 值 |
|---|---|
| **文件名** | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| **仓库** | `Comfy-Org/MiniMax-H3` |
| **仓库内路径** | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| **准确字节数** | `20970379616`（约19.53 GiB / 20.97 GB） |
| **SHA256（X-Linked-ETag）** | `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a` |
| Xet 分块哈希 | `c44113203bfee16cc28b9d344d14a306943708c3828f6a765962deb83e10651c` |

## 下载地址（两个都可用，优先第1 个）

**① 国内直连快（推荐，走 hf-mirror 镜像）**
```
https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
```

**② 官方源（需要代理 10808）**
```
https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
```

## ⭐ 存放到哪里（路径必须一字不差）

```
D:\h3models\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors
```

- 目录 `D:\h3models\diffusion_models\` **已经存在**，直接放进去就行。
- **文件名必须完全一致**，不要改、不要加 `(1)`、不要改扩展名。
- 下好后**不要改名、不要移动**，直接告诉我一声，我来做校验。

## 下完后必须做的两步验证

### 1. 看大小（不够就是没下完）
文件属性里应该是 **19,527 MB**（20970379616 字节）。

### 2. 让我跑内容校验（这一步千万别省）
我这边有脚本 `_check_quant.py`，会读模型内部的量化配置来验证内容真伪。
**这一步是必须的** —— 之前有一份文件**大小完全正确、头部也完整，但数据区全是错位的**，
所有自动校验都通过了，只有内容探针才抓出来，害得白下了两次 20GB。

所以下好后你只要说一句「下好了」，我马上跑校验。

## ⛔ 下载时务必注意（我踩过的坑）

1. **不要用带"断点续传"的下载器反复重试同一下载**。
   我上一版脚本就是 `curl --retry` + 追加写，结果重试时把同一段数据写了两遍，
   20GB 全部错位。**要么一次下完，要么整个重下，不要拼接。**

2. **一定要下完整 20970379616 字节**。如果显示的是 20970379616 但下载器说"完成"，
   还是要校验 —— 尺寸对不等于内容对。

3. 如果中途断了，**从头重新下**，不要续传。

## 备选方案（如果上面这个下不动）

同仓库还有这些版本，都是原版模型，**不要**下错：

| 文件 | 说明 |
|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | ⭐ **要这个**（官方蓝图用的就是这个） |
| `minimax_h3_fl2va_pruned_bf16.safetensors` | 同架构bf16 版，**更大（40GB+）且 16GB 显存跑不动**，不要选 |
| `minimax_h3_fl2va_int8_convrot.safetensors` | 未剪枝版，21GB 左右，官方 API 用；本机跑不动 |

## 另外两个模型（已经下好了，不用管）

| 文件 | 位置 | 状态 |
|---|---|---|
| `minimax_h3_video_vae_fp16.safetensors` | `D:\h3models\vae\` | ✅ 5.2GB 已验过 |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | `D:\h3models\loras\` | ✅ 1.9GB 已验过 |