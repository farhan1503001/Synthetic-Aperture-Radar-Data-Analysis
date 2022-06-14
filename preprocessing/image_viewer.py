import numpy as np
import cv2
import PIL
from PIL import Image
PIL.Image.MAX_IMAGE_PIXELS = None
filename='Gamma0_VH.png'
def read_image(filename):
    image=Image.open(filename)
    if image is not None:
        print("Succesfully loaded")
        print("Format: ",image.format)
        print("Size: ",image.mode)
        print("Mode: ",image.mode)
    return image
def convert_array(image):
    image_array=np.asarray(image)
    if len(image_array.shape) > 2 and image_array.shape[2] == 4:
    #convert the image from RGBA2RGB
       img = cv2.cvtColor(image_array, cv2.COLOR_BGRA2BGR)
    return image_array,img
def visualize_pixel_values(image,size):
    if image is not None:
        print(image.shape)
    copy_image=image.resize((size,size))
    copy_image=np.asarray(copy_image,dtype=np.uint8)
    copy_image.tofile("Smaller_resized.csv",sep=',')
    image.tofile('Original_image.csv',sep=',')
    
def showing_image_rgba(image,mode='rgba'):
    img=Image.fromarray(image,mode=mode)
    img.show("RGBA image read")
if __name__=='__main__':
    #Just viewing the gamma image we just recently downloaded
    image=read_image(filename)
    rgba_img,rgb_img=convert_array(image)
    visualize_pixel_values(rgba_img,512)