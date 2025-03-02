from PIL import ImageFont

try:
    # Try to load a specific font (e.g., Arial)
    font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 24)
    print("Font is accessible!")
except IOError:
    print("Font not found or not accessible!")
