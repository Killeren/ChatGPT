from together import Together

client = Together()
response = client.images.generate(
    prompt="generate image of mg gandhi",
    model="black-forest-labs/FLUX.1-schnell-Free",
    steps=4,
    n=1
)
if response.data and response.data[0].url:
    print("Image URL:", response.data[0].url)
else:
    print("No image generated.")