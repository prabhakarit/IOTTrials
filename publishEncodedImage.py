import math

packet_size=3000

def publishEncodedImage(encoded):
 end = packet_size
 start = 0
 length = len(encoded)
 picId = randomword(8)
 pos = 0
 no_of_packets = math.ceil(length/packet_size)
 while start <= len(encoded):
  data = {"data": encoded[start:end], "pic_id":picId, "pos": pos, "size": no_of_packets}
  client.publishEvent("Image-Data",json.JSONEncoder().encode(data))
  end += packet_size
  start += packet_size
  pos = pos +1
