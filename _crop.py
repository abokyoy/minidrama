from PIL import Image
im = Image.open(r'E:\LLM\try\minidrama\第一百三十八个名字_角色设定\小唐_设定_final.png')
w, h = im.size
print(im.size)
box = (int(0.37*w), int(0.08*h), int(0.57*w), int(0.95*h))
im.crop(box).save(r'E:\LLM\try\minidrama\.crop_xt.png')
print('ok')
