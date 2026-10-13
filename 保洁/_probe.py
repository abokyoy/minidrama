import glob, os, json, subprocess
FF = r"E:/Program Files/ffmpeg/bin/ffmpeg.exe"
FP = r"E:/Program Files/ffmpeg/bin/ffprobe.exe"
for f in ["D:/output/_raw/ep01_t01_00001-audio.mp4",
          "D:/output/_raw/ep01_t01_00001.mp4",
          "D:/output/ep01_t73_00001-audio.mp4"]:
    if not os.path.exists(f):
        print("缺失", f); continue
    r = subprocess.run([FP,"-v","error","-show_entries","stream=codec_type,codec_name,width,height,sample_rate,bit_rate",
                        "-of","csv=p=0", f], capture_output=True, text=True)
    print(os.path.basename(f), "->", r.stdout.strip().replace("\n"," | "))
