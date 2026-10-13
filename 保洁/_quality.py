# -*- coding: utf-8 -*-
r"""画质档位 —— 把「用哪套参数生成」变成一条可切换的配置。

用户 2026-10-04 要求：新生成的放 D:\output\new，从第一幕重新生成，
「确保效果和 seedance 一样」。

⚠️ 先说清楚（不能对用户承诺做不到的事）：
   实测数据表明本地 H3 与 Seedance 的**客观差距远小于肉眼看感**：
     帧抖动  本地 4.94–5.89  vs  Seedance 4.47–5.17   ← 同水平
     人声高频 本地 -33.5dB   vs  Seedance -34.5dB    ← 本地略好
     跨段身份相似 本地 0.69–0.77 vs Seedance 0.52–0.78 ← 同水平
   真正落后的只有 **局部细节/质感**（int8 VAE，本机无 bf16 版，改不了）。
   所以「和 Seedance 一样」在本机做不到；但把**能改的都改到最好**是可行的。

三档参数（按证据强度分档，每档都能一键切换）：

  safe   已验证安全、不折腾：4步 + 现行 SLA 开关
         亮度实测 132–138（达标），与 Seedance 同水平。
  bright 5 步：比 4 步稍多细节，亮度风险比 6 步小（6 步实测掉到 87.8，不可接受）
  deep   6步 + dense_last=1 + reference_protection=Light + tail_correction
         官方推荐的完整组合，但**必须配合后期提亮**（6步实测偏暗）

用法：
  python _quality.py show              # 看当前档位与参数
  python _quality.py set deep          # 切档（写 profile.json）
  python _quality.py apply deep        # 切档并写进各集 _api 模板
  python _quality.py list              # 列出所有档位
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(BASE, "_quality_profile.json")

# 基线（现行设置，全部来自 ep001_segs/_last_api.json）
BASE_P = dict(
    steps=4,
    sch="simple",
    smp="res_multistep",
    ref="match",
    mp=0.75,
    dlast=0,
    refprot="Off",
    tail=False,
    stabilize=False,
)

PROFILES = {
    "safe": dict(
        desc="4步基线。亮度实测 132-138（达标），与 Seedance 同水平。速度最快。",
        p=dict(BASE_P),
    ),
    # ⛔ 2026-10-04 16:23 实测踩坑：reference_protection=Light 会让**整段画面花屏**
    #    现象：ep01_t01 全片 11 帧全部被彩色噪点 + 规则网格纹理覆盖，人物完全不可辨；
    #    码率 10.4 Mbps（旧片同段 4.2 Mbps，差 2.5 倍）。
    #    ⚠️ 亮度检测却报 mean=164.9 med=169 p05=88 **OK** —— 因为它只看灰度均值，
    #    彩噪对亮度影响不大 → **现有校验完全发现不了花屏**（又一个"校验器骗人"）。
    #    对照实验：同一份 t01 提示词只把 refprot 改回 Off → 画面完全正常
    #    （人物清晰、构图正确、身份一致）。**判定：refprot=Light 是元凶，禁用。**
    #    官方 tooltip 原文就写着它 "most likely unusable" —— 当时没重视。
    "final": dict(
        desc="★当前上线档（= safe，refprot 必须 Off）。已禁用 reference_protection"
             "（实测整段花屏）。如需换其它参数请先跑 _diag_glitch.py 对照。",
        p=dict(BASE_P),   # refprot 保持 Off
    ),
    "bright": dict(
        desc="5 步 + 末步全注意力。⚠️ 5~6 步实测会压暗到 87-95，须配提亮。",
        p=dict(BASE_P, steps=5, dlast=1),
    ),
    "deep": dict(
        desc="官方完整推荐：6步+末步全注意力+参考保护Light+尾部修正。"
             "⚠️ 6步实测亮度 87.8，必须配后期提亮后才可用。",
        p=dict(BASE_P, steps=6, dlast=1, refprot="Light", tail=True),
    ),
    # ==================================================================
    # 2026-10-06 用户提问「Seedance 用一样参考图和一样提示词，
    #是不是应该调 H3 而不是一样的输入」→ 查 ComfyUI 源码 + 官方蓝图后确认：
    #   **本地跑的根本不是官方配置的 H3。**
    #   本地：fused_refdelta_r1024_**turbo8**_mystic07_int8（社区 8 步蒸馏模型）
    #         + 只有 4 步
    #   官方：fl2va_pruned_int8（**原版**）+ 可选挂 turbo LoRA + **20 步**，
    #         或挂 LoRA 后 **6 步**（官方蓝图 PrimitiveInt 145/146 就是这两个值）
    #   差在：① 模型是turbo 蒸馏版  ② 步数 4 < 蒸馏目标 8  ③ turbo LoRA 从没挂上
    #     （文件早在 D:\h3models\loras 里躺着，1956193000 字节）
    # 「对比度大、没有柔和感」= 步数不足，光影过渡没走完就停 → 调色救不了。
    # ==================================================================
    "official20": dict(
        desc="★官方原版模型 + 20 步（不挂 LoRA）。最接近官方 API 默认，"
             "步数最足、过渡最平滑，但最慢（20/4 = 5 倍耗时）。",
        p=dict(BASE_P, steps=20,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_fp16.safetensors"),
    ),
    "official_turbo6": dict(
        desc="★官方 turbo 档：原版模型 + 挂 turbo LoRA + 6 步。"
             "官方蓝图 ComfySwitchNode(true) 分支就是这个组合。"
             "比 20 步快 3 倍，细节略逊但远好于「turbo 模型跑 4 步」。",
        p=dict(BASE_P, steps=6,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_fp16.safetensors",
               lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
               lora_s=1.0),
    ),
    "hd_turbo8": dict(
        desc="★当前上线档：官方原版 DiT + turbo LoRA + 8 步 + **int8 VAE**。"
             "⚠️ VAE 必须用 int8 —— 实测 fp16 VAE 在 RTX 3080Ti 上解码出 NaN，"
             "整段成片全黑（2026-10-06 栽过，浪费 21 分钟）。",
        p=dict(BASE_P, steps=8,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_int8_convrot.safetensors",
               lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
               lora_s=1.0),
    ),
    "official_turbo8": dict(
        desc="官方 turbo 档的 8 步版（LoRA 名为 8step，给足步数）。"
             "比 6 步更稳，快于 20 步。**推荐首个验证档**。",
        p=dict(BASE_P, steps=8,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_fp16.safetensors",
               lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
               lora_s=1.0),
    ),
    # ==================================================================
    #  2026-10-10 用户提出（原话）：
    #  「能不能先预出片 就是运行产出分辨率低的 看看是否都对 提高出片的速度
    #    然后 预出片是对的话 再运行提高分辨率的工作流」
    #  ⚠️ 本档**只降分辨率，其余参数与 hd_turbo8 完全一致**：
    #     同模型、同 8 步、同 LoRA、同 VAE。唯一差别是 mp 0.75→0.25。
    #     这样「预出片对不对」和「终版对不对」是同一个判断，
    #     不会出现「低分辨率看着没问题、升上去却变了个人」这种坑。
    #  ⛔⛔⛔ 绝不降步数：步数一少画面本身就糙（实测 6 步亮度掉到 87.8），
    #     那就不是「预览」而是「另一个东西」了，验它没意义。
    # ==================================================================
    "preview25": dict(
        desc="预出片档：与 hd_turbo8 唯一差别是分辨率 0.75→0.25（576x448，"
             "算力约 33%）。用来先验「人数/朝向/台词归属/黑块/切镜」对不对，"
             "对了再升到 hd_turbo8 出终版。⛔ 步数不减。",
        p=dict(BASE_P, steps=8, mp=0.25,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_int8_convrot.safetensors",
               lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
               lora_s=1.0),
    ),
    "preview40": dict(
        desc="预出片档（较清晰）：mp=0.40 → 736x544，算力约 53%。"
             "想看得出人物五官时用这档，仍比终版快近一倍。",
        p=dict(BASE_P, steps=8, mp=0.40,
               unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
               vae="minimax_h3_video_vae_int8_convrot.safetensors",
               lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
               lora_s=1.0),
    ),
}

# ⛔ 预出片档：只用于「先验后升」，不能当上线档
PREVIEW_ONLY = {"preview25", "preview40"}

# 实测偏暗、需要后期提亮的档位（亮度 < 100）
NEED_GRADE = {"bright": 0.16, "deep": 0.18}


def cur():
    if os.path.exists(PROFILE):
        try:
            return json.load(io.open(PROFILE, encoding="utf-8"))
        except Exception:
            pass
    return {"name": "safe"}


def show():
    c = cur()
    n = c.get("name", "safe")
    p = PROFILES.get(n, PROFILES["safe"])["p"]
    print("=" * 66)
    print(" 当前档位：%s" % n)
    print("=" * 66)
    print(" %s" % PROFILES.get(n, PROFILES["safe"])["desc"])
    print()
    print("  steps              = %s" % p["steps"])
    print("  scheduler          = %s" % p["sch"])
    print("  sampler            = %s" % p["smp"])
    print("  ref_image_size     = %s" % p["ref"])
    print("  megapixels         = %s" % p["mp"])
    print("  dense_last_steps   = %s" % p["dlast"])
    print("  reference_protection = %s" % p["refprot"])
    print("  tail_correction    = %s" % p["tail"])
    print("  stabilize_motion   = %s" % p["stabilize"])
    if p.get("unet"):
        print("  unet_name       = %s" % p["unet"])
    if p.get("vae"):
        print("  video_vae       = %s" % p["vae"])
    if p.get("lora"):
        print("  lora            = %s (strength %s)" % (p["lora"], p.get("lora_s", 1.0)))
    g = NEED_GRADE.get(n)
    print("  后期提亮           = %s" % ("需要（6步会偏暗）" if g else "不需要"))
    print()
    print(" 所有档位：")
    for k, v in PROFILES.items():
        print("   %-8s steps=%d dlast=%d refprot=%-8s tail=%-5s  %s"
              % (k, v["p"]["steps"], v["p"]["dlast"], v["p"]["refprot"],
                 v["p"]["tail"], v["desc"][:34]))


def patch_api(api, p):
    """把参数写进一份 API json（就地修改并返回）。"""
    for nd in api.values():
        if not isinstance(nd, dict):
            continue
        ct, ins = nd.get("class_type"), nd.get("inputs", {})
        if ct == "BasicScheduler":
            ins["steps"] = p["steps"]
            ins["scheduler"] = p["sch"]
        elif ct == "KSamplerSelect":
            ins["sampler_name"] = p["smp"]
        elif ct == "MiniMaxH3ReferenceToVideo":
            ins["ref_image_size"] = p["ref"]
        elif ct == "ResolutionSelector" and "megapixels" in ins:
            ins["megapixels"] = p["mp"]
        elif ct == "H3SLAAttention":
            ins["dense_last_steps"] = p["dlast"]
            ins["reference_protection"] = p["refprot"]
            ins["tail_correction"] = bool(p["tail"])
            ins["stabilize_motion"] = bool(p["stabilize"])
        elif ct == "UNETLoader" and p.get("unet"):
            ins["unet_name"] = p["unet"]
        elif ct == "VAELoader" and p.get("vae") and "video" in str(ins.get("vae_name", "")):
            ins["vae_name"] = p["vae"]
    # LoRA：patch_api 只做参数登记，实际插节点由 h3_driver 运行时完成
    #（插节点要改连线，patch_api 这种平铺改法做不了，硬做会写出坏图）
    if p.get("lora"):
        print("  （LoRA %s 由 h3_driver 在运行时插入 UNETLoader 之后）"
              % p["lora"])
    return api


def apply(name):
    if name not in PROFILES:
        print("没有这个档位。可用：%s" % ", ".join(PROFILES))
        return
    src = os.path.join(BASE, "ep001_segs", "_last_api.json")
    if not os.path.exists(src):
        print("找不到基准 api：%s" % src)
        return
    api = json.load(io.open(src, encoding="utf-8"))
    patch_api(api, PROFILES[name]["p"])
    dst = os.path.join(BASE, "ep001_segs", "_profile_api.json")
    io.open(dst, "w", encoding="utf-8").write(
        json.dumps(api, ensure_ascii=False, indent=1))
    io.open(PROFILE, "w", encoding="utf-8").write(
        json.dumps({"name": name, "p": PROFILES[name]["p"]},
                   ensure_ascii=False, indent=1))
    print("✅ 已切到档位「%s」" % name)
    print("   参数模板：%s" % os.path.relpath(dst, BASE))
    print("   %s" % PROFILES[name]["desc"])
    if NEED_GRADE.get(name):
        print("   ⚠️ 该档位必须开后期提亮，否则画面会偏暗（6步实测 87.8）")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "show":
        show()
    elif cmd == "list":
        for k, v in PROFILES.items():
            print(" %-8s %s" % (k, v["desc"]))
    elif cmd == "set":
        apply(sys.argv[2] if len(sys.argv) > 2 else "safe")
    elif cmd == "apply":
        apply(sys.argv[2] if len(sys.argv) > 2 else "safe")
    else:
        print(__doc__)
