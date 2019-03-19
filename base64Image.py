import base64

def convertImageToBase64():
 with open("image_test.jpg", "rb") as image_file:
 encoded = base64.b64encode(image_file.read())
 return encoded

convertImageToBase64()
