# YoloTagger

**YoloTagger** is a lightweight, desktop Python application for labeling images for object detection datasets.  
It supports **JSON (raw), YOLO, and COCO** formats, allows **class management**, and can leverage **pretrained YOLO models** for automatic predictions.

![Demo](docs/demo.gif)

---

## Features

- Open **single images, folders, or datasets** with train/val splits
- Add, edit, and remove **object classes** with customizable colors
- Draw **bounding boxes** (rectangles) and **polygon masks**
- Load existing labels in **JSON, YOLO, or COCO** format
- Save annotations in the same formats
- Load **YOLO `.pt` models** for automatic prediction
- Automatically maps model predictions to your dataset classes
- Lightweight and modular architecture


---

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/wojciechc1/YoloTagger.git
    cd YOLOTagger
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage 
1. Launch the GUI:
    ```bash
    python main.py
    ```
2. Open a file, folder, or dataset.
3. Add object classes or edit existing ones.
4. Draw bounding boxes or masks on images.
5. Optionally, load a pretrained YOLO .pt model to auto-predict labels.
6. Save your annotations in JSON, YOLO, or COCO format.

---

## Demo

---

## File Structure
```bash 
YoloTagger/
│   README.md
│   LICENSE
│   requirements.txt
│
├───app/
│   ├───core/           # Dataset management, model manager, label & session logic
│   ├───gui/            # PyQt5 GUI (panels, dialogs)
│   ├───items/          # Custom annotation items
│   └───temp/           # Temporary session/cache files
│
├───docs/               
└───examples/           # Example datasets and YOLO models
```

---

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Roadmap
- Edge-case handling and error prevention
- Auto-syncing of unique classes with model predictions
- Support for more annotation shapes
- Better model integration
- Performance optimizations for large datasets

---

## Contributing
Feel free to submit issues or pull requests.
For now, this is a student/experimental project, so contributions are welcome but may not be fully merged.

---

## Acknowledgements
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- Inspiration from LabelImg Annotate