# Image to SVG Converter

This tool automatically converts images to SVG format, with intelligent optimization for large images or images with too many colors. It's designed to work seamlessly as part of an automated workflow in macOS.

## Features

- Automatic image resizing for large images
- Color reduction with dithering for better visual quality
- Intelligent SVG path generation to reduce file size
- Optimized for macOS Automator workflows

## Requirements

- Python 3.6+
- PIL/Pillow (Python Imaging Library)
- NumPy

## Setup Instructions

### 1. Set up a Python virtual environment

```bash
# Navigate to the project directory
cd /path/to/test/convertImageToSVG

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install numpy, Image
```

### 2. Test the script manually

Before setting up Automator, test the script to ensure it works correctly:

```bash
python convertImageToSvg.py /path/to/test/image.png
```

### 3. Set up macOS Automator

#### Creating a Quick Action (Service) Workflow

1. Open **Automator** (found in `/Applications`)
2. Create a new document and select **Quick Action** as the type
3. Configure the workflow to:
   - Receive current **files or folders** in **Finder**
   - Image files only (optional)
4. Add a **Run Shell Script** action from the Actions library
5. Set the shell to `/bin/zsh`
6. Set "Pass input" to "as arguments"
7. Paste the following script (update PATH_TO_FOLDER to the actual path):

```bash
# Replace with your actual project directory
PATH_TO_FOLDER="/Users/dharmin/Dev/Projects/convertImageToSVG"

for f in "$@"
do
    "$PATH_TO_FOLDER/venv/bin/python3" "$PATH_TO_FOLDER/convertImageToSvg.py" "$f"
done
```

8. Save the workflow with a meaningful name like "Convert to SVG"

#### Alternative: Copy the Workflow file to `~/Library/Services`
You can also copy the workflow file directly to your Services directory:

```bash
cp /path/to/your/Convert Image to SVG.workflow ~/Library/Services/
```


## Usage

### Via Quick Action (Service)

1. In Finder, select one or more image files
2. Right-click and select "Quick Actions" → "Convert to SVG"
3. The SVG files will be created in the same directory as the original images

## Advanced Configuration

You can modify the Automator workflow to pass additional parameters to the script:

```bash
for f in "$@"
do
    "$PATH_TO_FOLDER/venv/bin/python3" "$PATH_TO_FOLDER/convertImageToSvg.py" "$f" --max-size 300 --max-colors 64
done
```

### Available Parameters

- `--max-size` (default: 500): Maximum dimension (width or height) for automatic resizing
- `--max-colors` (default: 256): Maximum number of colors for automatic color reduction
- `--force-full`: Force processing the full image without any optimizations

## Troubleshooting

If you encounter permission issues:

```bash
chmod +x /Users/dharmin/Dev/Projects/convertImageToSVG/convertImageToSvg.py
```

If the virtual environment doesn't work in Automator:

1. Try using the absolute path to Python instead:
   ```bash
   /usr/bin/python3 "$PATH_TO_FOLDER/convertImageToSvg.py" "$f"
   ```

2. Install the required packages globally:
   ```bash
   pip3 install pillow numpy
   ```

## License

This project is available under the MIT License.
