from imagekit.specs import ImageSpec 
from imagekit import processors 

# first we define our thumbnail resize processor 
class ResizeThumb(processors.Resize): 
    width = 180
    height = 130 
    #crop = True
    
class ResizeThumb_2(processors.Resize): 
    width = 160
    height = 160 
    #crop = True
    
class ResizeFull(processors.Resize):
    width = 600
    height = 600 
    
class EnchanceThumb(processors.Adjustment): 
    contrast = 1.0
    sharpness = 1.0

class Thumbnail(ImageSpec): 
    access_as = 'thumbnail' 
    pre_cache = True 
    quality = 90
    processors = [ResizeThumb, EnchanceThumb] 
    
class Thumbnail_2(ImageSpec): 
    access_as = 'thumbnail_inner' 
    quality = 90
    processors = [ResizeThumb_2, EnchanceThumb] 
    
class Full(ImageSpec):
    access_as = 'fullimage' 
    quality = 90
    processors = [ResizeFull]
