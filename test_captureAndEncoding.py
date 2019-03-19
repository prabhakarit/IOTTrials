import realsensesavecolorimage
import base64

image_name="color_image_simple.png"

def convertImageToBase64():
 with open(image_name, "rb") as image_file:
  encoded = base64.b64encode(image_file.read())
  return encoded

print (convertImageToBase64())
