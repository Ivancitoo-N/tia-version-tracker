"""
Generate PNG favicons from SVG source.
Run this script to create favicon.ico and various PNG sizes.
"""

from pathlib import Path

try:
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg
    from PIL import Image
    
    # Paths
    static_dir = Path(__file__).parent / "static"
    svg_path = static_dir / "favicon.svg"
    
    # Convert SVG to different sizes
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        drawing = svg2rlg(svg_path)
        # Scale drawing
        drawing.width = size
        drawing.height = size
        drawing.scale(size/512, size/512)
        
        png_path = static_dir / f"favicon-{size}.png"
        renderPM.drawToFile(drawing, str(png_path), fmt="PNG")
        print(f"Created {png_path}")
        
        # Open for ICO creation
        if size in [16, 32, 48]:
            images.append(Image.open(png_path))
    
    # Create .ico file
    ico_path = static_dir / "favicon.ico"
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(16,16), (32,32), (48,48)]
    )
    print(f"\nCreated {ico_path}")
    print("\nFavicons generated successfully!")
    
except ImportError as e:
    print("Optional dependencies not installed. To generate PNG/ICO favicons:")
    print("  pip install svglib pillow")
    print("\nThe SVG favicon will still work in modern browsers.")
