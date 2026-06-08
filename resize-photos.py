#!/usr/bin/env python3
"""
Resize & compress semua foto di folder photos/
- Max width: 1200px
- Max size: ~300KB
- Format: JPEG (kualitas 85)
"""
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system("pip3 install Pillow -q")
    from PIL import Image

PHOTOS_DIR = Path(__file__).parent / "photos"
MAX_WIDTH = 1200
MAX_SIZE_KB = 300
QUALITY = 85

def resize_photo(filepath):
    img = Image.open(filepath)
    
    # Convert RGBA to RGB
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Resize if wider than max
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        print(f"  Resized to {new_size[0]}x{new_size[1]}")
    
    # Save with compression
    output = filepath.with_suffix('.jpg')
    img.save(output, 'JPEG', quality=QUALITY, optimize=True)
    
    # Check file size
    size_kb = output.stat().st_size / 1024
    if size_kb > MAX_SIZE_KB:
        # Reduce quality until under limit
        q = QUALITY
        while q > 30 and size_kb > MAX_SIZE_KB:
            q -= 5
            img.save(output, 'JPEG', quality=q, optimize=True)
            size_kb = output.stat().st_size / 1024
        print(f"  Compressed to {size_kb:.0f}KB (quality={q})")
    else:
        print(f"  Output: {size_kb:.0f}KB")
    
    return output

def main():
    if not PHOTOS_DIR.exists():
        print("❌ Folder photos/ tidak ditemukan!")
        return
    
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    photos = [f for f in PHOTOS_DIR.iterdir() 
              if f.suffix.lower() in extensions and f.name != 'README.txt']
    
    if not photos:
        print("❌ Tidak ada foto di folder photos/")
        print("   Taruh foto dulu, lalu jalankan script ini lagi.")
        return
    
    print(f"📸 Ditemukan {len(photos)} foto\n")
    
    for photo in photos:
        print(f"Processing: {photo.name}")
        try:
            result = resize_photo(photo)
            # Remove original if different format
            if result != photo and photo.suffix.lower() not in {'.jpg', '.jpeg'}:
                photo.unlink()
                print(f"  Removed original: {photo.name}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n✅ Selesai! Foto siap di folder photos/")

if __name__ == '__main__':
    main()
