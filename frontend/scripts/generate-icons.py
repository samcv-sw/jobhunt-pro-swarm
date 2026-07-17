import os
import struct
import zlib

def make_png(width, height, color=(108, 99, 255)):
    # PNG signature
    png = bytearray(b'\x89PNG\r\n\x1a\n')
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    
    def make_chunk(tag, data):
        chunk = bytearray()
        chunk.extend(struct.pack('>I', len(data)))
        chunk.extend(tag)
        chunk.extend(data)
        crc = zlib.crc32(tag + data)
        chunk.extend(struct.pack('>I', crc))
        return chunk

    png.extend(make_chunk(b'IHDR', ihdr_data))
    
    # IDAT chunk (pixel data)
    row = b'\x00' + bytes(color) * width
    raw_data = row * height
    idat_data = zlib.compress(raw_data)
    png.extend(make_chunk(b'IDAT', idat_data))
    
    # IEND chunk
    png.extend(make_chunk(b'IEND', b''))
    
    return png

def main():
    public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../public'))
    icons_dir = os.path.join(public_dir, 'icons')
    screenshots_dir = os.path.join(public_dir, 'screenshots')
    
    os.makedirs(icons_dir, exist_ok=True)
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # PWA icons
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    for size in sizes:
        icon_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        png_data = make_png(size, size, color=(108, 99, 255))
        with open(icon_path, 'wb') as f:
            f.write(png_data)
            
    # Screenshots
    screenshot_path = os.path.join(screenshots_dir, 'dashboard.png')
    png_data = make_png(1280, 720, color=(15, 15, 26))
    with open(screenshot_path, 'wb') as f:
        f.write(png_data)
        
    print("Done")

if __name__ == '__main__':
    main()
