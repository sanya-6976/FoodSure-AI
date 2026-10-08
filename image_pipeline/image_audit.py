from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_ROOT = (
    PROJECT_ROOT.parent
    / "Multimodal Dataset for Turmeric Adulteration Detec"
    / "Image"
)

print("Image folder:")
print(IMAGE_ROOT)

print("\nDoes this folder exist?")
print(IMAGE_ROOT.exists())

classes = [
    folder.name
    for folder in IMAGE_ROOT.iterdir()
    if folder.is_dir()
    and folder.name != "EfficientNetB0_Image_Features"
]

print("\nClasses found:")
print(classes)

print("\nImage audit:")

for class_name in classes:

    class_folder = IMAGE_ROOT / class_name

    image_files = list(class_folder.glob("*.JPG"))

    print(f"\n--- {class_name} ---")
    print("Number of images:", len(image_files))

    sizes = set()
    modes = set()
    bad_images = []

    for image_path in image_files:

        try:
            with Image.open(image_path) as img:
                sizes.add(img.size)
                modes.add(img.mode)

        except Exception as e:
            bad_images.append(image_path.name)

    print("Image sizes:", sizes)
    print("Image modes:", modes)
    print("Corrupted images:", len(bad_images))

    if bad_images:
        print("Bad files:", bad_images)