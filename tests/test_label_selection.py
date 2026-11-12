import os
from unittest.mock import patch

import pytest
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtWidgets import QApplication, QDialog

from app.gui.main_window import MainWindow
from app.items.annotator_items import RectItem


@pytest.fixture(scope="module")
def application():
    with patch.dict(os.environ, {"QT_QPA_PLATFORM": "offscreen"}):
        application = QApplication.instance() or QApplication([])
        yield application


@pytest.fixture
def labeled_window(application, tmp_path):
    image_path = tmp_path / "cars.png"
    Image.new("RGB", (500, 500)).save(image_path)
    (tmp_path / "cars.txt").write_text(
        "0 0.2 0.2 0.1 0.1\n0 0.5 0.5 0.1 0.1\n0 0.8 0.8 0.1 0.1\n"
    )
    window = MainWindow()
    window.dataset_service.open_folder(str(tmp_path))
    window.session.files = window.dataset_service.get_all_files()
    window.session.current_index = 0
    window.image_panel.load_image(str(image_path))
    window.session_controller.load_labels(str(tmp_path), "yolo")
    window.show()
    application.processEvents()
    yield window, str(image_path)
    window.close()


@pytest.mark.parametrize("selection", ["box", "handle", "cross", "none", "multiple"])
def test_remove_only_selected_imported_labels(labeled_window, selection):
    window, image_path = labeled_window
    panel = window.image_panel
    original = list(window.label_service.get_labels(image_path))
    assert len({label["id"] for label in original}) == 3
    assert window.box_count.text() == "Bounding boxes: 3"
    annotations = sorted(
        (item for item in panel.scene().items() if isinstance(item, RectItem)),
        key=lambda item: item.label_id,
    )
    if selection == "handle":
        annotations[1].start_handle.setSelected(True)
    elif selection != "none":
        annotations[1].setSelected(True)
    if selection == "multiple":
        annotations[2].setSelected(True)

    if selection == "cross":
        assert panel.delete_button.isVisible()
        QTest.mouseClick(panel.delete_button, Qt.LeftButton)
    else:
        if selection in ("none", "multiple"):
            assert panel.delete_button.isHidden()
        panel.delete_selected_items()

    removed_ids = set()
    if selection != "none":
        removed_ids.add(original[1]["id"])
    if selection == "multiple":
        removed_ids.add(original[2]["id"])
    expected = [label for label in original if label["id"] not in removed_ids]
    assert window.label_service.get_labels(image_path) == expected
    assert window.box_count.text() == f"Bounding boxes: {len(expected)}"
    assert len(
        [item for item in panel.scene().items() if isinstance(item, RectItem)]
    ) == len(expected)
    assert panel.delete_button.isHidden()


def test_edit_and_add_imported_labels_independently(labeled_window):
    window, image_path = labeled_window
    service = window.label_service
    original = [dict(label) for label in service.get_labels(image_path)]
    changed_coords = [(1, 2), (30, 40)]
    service.update_label(image_path, original[1]["id"], changed_coords)
    labels = service.get_labels(image_path)
    assert labels[0] == original[0]
    assert labels[1]["coords"] == changed_coords
    assert labels[2] == original[2]
    service.add_label(image_path, 0, "rect", [(50, 60), (70, 80)])
    assert len({label["id"] for label in service.get_labels(image_path)}) == 4


def test_double_click_removes_only_clicked_box(labeled_window):
    window, image_path = labeled_window
    panel = window.image_panel
    window.session.label_mode = "rect"
    window.session.current_class = 0
    draw_requests = QSignalSpy(panel.rectangleDrawRequested)
    original = list(window.label_service.get_labels(image_path))
    annotations = sorted(
        (item for item in panel.scene().items() if isinstance(item, RectItem)),
        key=lambda item: item.label_id,
    )
    annotations[0].setSelected(True)
    target = annotations[1]
    position = panel.mapFromScene(target.mapToScene(target.rect().center()))
    QTest.mouseDClick(panel.viewport(), Qt.LeftButton, pos=position)
    assert window.label_service.get_labels(image_path) == [original[0], original[2]]
    assert window.box_count.text() == "Bounding boxes: 2"
    assert len(draw_requests) == 0
    assert not panel.is_drawing
    assert (
        len([item for item in panel.scene().items() if isinstance(item, RectItem)]) == 2
    )


def test_double_click_background_leaves_boxes_unchanged(labeled_window):
    window, image_path = labeled_window
    panel = window.image_panel
    original = list(window.label_service.get_labels(image_path))
    position = panel.mapFromScene(20, 480)
    QTest.mouseDClick(panel.viewport(), Qt.LeftButton, pos=position)
    assert window.label_service.get_labels(image_path) == original


def test_double_click_empty_image_arms_rectangle_then_drag_draws(labeled_window):
    window, image_path = labeled_window
    panel = window.image_panel
    window.session.label_mode = "rect"
    window.session.current_class = 0
    original = list(window.label_service.get_labels(image_path))
    position = panel.mapFromScene(20, 480)
    QTest.mouseDClick(panel.viewport(), Qt.LeftButton, pos=position)
    QTest.mouseRelease(panel.viewport(), Qt.LeftButton, pos=position)
    assert panel.is_drawing
    assert panel.label_type == "rect"
    assert panel.selected_class == 0
    assert panel.temp_rect is None
    assert window.label_service.get_labels(image_path) == original
    start = panel.mapFromScene(30, 420)
    end = panel.mapFromScene(80, 470)
    QTest.mousePress(panel.viewport(), Qt.LeftButton, pos=start)
    QTest.mouseMove(panel.viewport(), end)
    QTest.mouseRelease(panel.viewport(), Qt.LeftButton, pos=end)
    labels = window.label_service.get_labels(image_path)
    assert len(labels) == 4
    assert labels[:3] == original
    assert labels[-1]["type"] == "rect"
    assert not panel.is_drawing


def test_double_click_does_not_start_rectangle_in_polygon_mode(labeled_window):
    window, image_path = labeled_window
    panel = window.image_panel
    window.session.label_mode = "polygon"
    window.session.current_class = 0
    original = list(window.label_service.get_labels(image_path))
    position = panel.mapFromScene(20, 480)
    QTest.mouseDClick(panel.viewport(), Qt.LeftButton, pos=position)
    assert not panel.is_drawing
    assert window.label_service.get_labels(image_path) == original


def test_box_count_updates_on_add_and_ignores_polygons(labeled_window):
    window, image_path = labeled_window
    window.session_controller.add_label(image_path, 0, "rect", [(1, 2), (30, 40)])
    assert window.box_count.text() == "Bounding boxes: 4"
    window.session_controller.add_label(
        image_path, 0, "polygon", [(1, 2), (30, 40), (50, 60)]
    )
    assert window.box_count.text() == "Bounding boxes: 4"


def test_image_progress_navigation_boundaries_and_new_dataset(labeled_window, tmp_path):
    window, image_path = labeled_window
    for filename in ("second.png", "third.png"):
        Image.new("RGB", (100, 100)).save(tmp_path / filename)
    with patch(
        "app.gui.main_window.LabelTypeDialog.exec_", return_value=QDialog.Accepted
    ):
        window.session_controller.open_folder(str(tmp_path))
    assert window.image_progress.text() == "Image 1 / 3   |   Passed: 0   |   Left: 2"
    assert window.box_count.text() == "Bounding boxes: 0"
    first_path = window.session.files[0]["path"]
    window.session_controller.add_label(first_path, 0, "rect", [(1, 2), (30, 40)])
    assert window.box_count.text() == "Bounding boxes: 1"
    window.session_controller.show_next_file()
    assert window.image_progress.text() == "Image 2 / 3   |   Passed: 1   |   Left: 1"
    assert window.box_count.text() == "Bounding boxes: 0"
    window.session_controller.show_next_file()
    window.session_controller.show_next_file()
    assert window.image_progress.text() == "Image 3 / 3   |   Passed: 2   |   Left: 0"
    window.session_controller.show_prev_file()
    assert window.image_progress.text() == "Image 2 / 3   |   Passed: 1   |   Left: 1"
    window.session_controller.show_prev_file()
    window.session_controller.show_prev_file()
    assert window.image_progress.text() == "Image 1 / 3   |   Passed: 0   |   Left: 2"
    assert window.box_count.text() == "Bounding boxes: 1"
    with patch(
        "app.gui.main_window.LabelTypeDialog.exec_", return_value=QDialog.Accepted
    ):
        window.session_controller.open_file(image_path)
    assert window.image_progress.text() == "Image 1 / 1   |   Passed: 0   |   Left: 0"
    assert window.box_count.text() == "Bounding boxes: 0"


def test_empty_image_progress(application):
    window = MainWindow()
    assert window.image_progress.text() == "Image 0 / 0   |   Passed: 0   |   Left: 0"
    assert window.box_count.text() == "Bounding boxes: 0"
    assert not window.clear_labels_button.isEnabled()
    window.close()


@pytest.fixture
def filtered_window(labeled_window, tmp_path):
    window, _ = labeled_window
    folder = tmp_path / "batch"
    folder.mkdir()
    for index, count in enumerate((0, 1, 2, 3, 1, 2)):
        Image.new("RGB", (100, 100)).save(folder / f"image_{index}.png")
        (folder / f"image_{index}.txt").write_text("0 0.5 0.5 0.1 0.1\n" * count)
    with patch(
        "app.gui.main_window.LabelTypeDialog.exec_", return_value=QDialog.Accepted
    ):
        window.session_controller.open_folder(str(folder))
    window.session.files.sort(key=lambda file: file["path"])
    window.session_controller.load_labels(str(folder), "yolo")
    window.session_controller.show_file(window.session.files[0]["path"])
    return window, folder


@pytest.mark.parametrize(
    "count, indices", [(0, [0]), (1, [1, 4]), (2, [2, 5]), (3, [3])]
)
def test_box_filter_list_and_navigation(filtered_window, count, indices):
    window, _ = filtered_window
    original_files = list(window.session.files)
    window.box_filter.setCurrentIndex(window.box_filter.findData(count))
    assert window.session_controller.visible_file_indices() == indices
    assert window.session.current_index == indices[0]
    parent = window.dataset_panel.tree_widget.topLevelItem(0)
    assert parent.childCount() == len(indices)
    assert [parent.child(index).data(0, 1) for index in range(parent.childCount())] == [
        original_files[index]["path"] for index in indices
    ]
    assert window.box_count.text() == f"Bounding boxes: {count}"
    window.session_controller.show_next_file()
    assert window.session.current_index == indices[-1]
    window.session_controller.show_next_file()
    assert window.session.current_index == indices[-1]
    window.session_controller.show_prev_file()
    assert window.session.current_index == indices[0]
    window.box_filter.setCurrentIndex(0)
    assert window.session_controller.visible_file_indices() == list(range(6))
    assert window.session.files == original_files


def test_clear_filtered_image_only_and_save_all_images(filtered_window):
    window, folder = filtered_window
    window.box_filter.setCurrentIndex(window.box_filter.findData(3))
    image_path = window.session.files[3]["path"]
    original_labels = {
        path: list(labels) for path, labels in window.label_service.labels.items()
    }
    label_path = folder / "image_3.txt"
    original_contents = label_path.read_text()
    window.clear_labels_button.click()
    assert window.box_count.text() == "Bounding boxes: 0"
    assert window.session.current_index == 3
    assert window.session_controller.visible_file_indices() == []
    assert window.dataset_panel.tree_widget.topLevelItemCount() == 0
    assert "Current image does not match filter" in window.image_progress.text()
    assert window.label_service.get_labels(image_path) == []
    assert label_path.read_text() == original_contents
    for path, labels in original_labels.items():
        if path != image_path:
            assert window.label_service.get_labels(path) == labels
    window.session_controller.save(str(folder), "yolo")
    assert label_path.read_text() == ""
    assert len((folder / "image_5.txt").read_text().splitlines()) == 2
    assert not any(
        isinstance(item, RectItem) for item in window.image_panel.scene().items()
    )
    window.box_filter.setCurrentIndex(0)
    assert window.session_controller.visible_file_indices() == list(range(6))


def test_filtered_file_selection_and_filter_reset(filtered_window):
    window, _ = filtered_window
    window.box_filter.setCurrentIndex(window.box_filter.findData(1))
    parent = window.dataset_panel.tree_widget.topLevelItem(0)
    window.dataset_panel.on_tree_item_clicked(parent.child(1), 0)
    assert window.session.current_index == 4
    with patch(
        "app.gui.main_window.LabelTypeDialog.exec_", return_value=QDialog.Accepted
    ):
        window.session_controller.open_file(window.session.files[0]["path"])
    assert window.box_filter.currentIndex() == 0
    assert window.session_controller.box_count_filter is None
    assert window.image_progress.text() == "Image 1 / 1   |   Passed: 0   |   Left: 0"


def test_three_plus_filter_includes_three_and_more_boxes(filtered_window):
    window, _ = filtered_window
    image_path = window.session.files[5]["path"]
    for _ in range(2):
        window.label_service.add_label(image_path, 0, "rect", [(1, 2), (30, 40)])
    window.box_filter.setCurrentIndex(window.box_filter.findData("3+"))
    assert window.session_controller.visible_file_indices() == [3, 5]
    assert window.session.current_index == 3
    assert window.box_count.text() == "Bounding boxes: 3"
    parent = window.dataset_panel.tree_widget.topLevelItem(0)
    assert parent.childCount() == 2
    window.session_controller.show_next_file()
    assert window.session.current_index == 5
    assert window.box_count.text() == "Bounding boxes: 4"
    window.session_controller.show_prev_file()
    assert window.session.current_index == 3
    window.box_filter.setCurrentIndex(window.box_filter.findData(3))
    assert window.session_controller.visible_file_indices() == [3]
