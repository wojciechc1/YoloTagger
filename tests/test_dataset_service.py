# tests/test_dataset_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.core.dataset.dataset_service import DatasetService


@pytest.fixture
def service():
    return DatasetService()


def test_get_extensions(service):
    assert service.get_extensions() == (".jpg", ".jpeg", ".png")


def test_open_file_sets_current_item(service):
    with patch("app.core.dataset.dataset_service.FileItem") as MockFile:
        mock_file = MagicMock(path="x.jpg")
        MockFile.return_value = mock_file
        service.open_file("x.jpg")
        assert service.current_item == mock_file
        MockFile.assert_called_once_with("x.jpg")


def test_open_folder_sets_current_item(service):
    with patch("app.core.dataset.dataset_service.FolderItem") as MockFolder:
        mock_folder = MagicMock(files=[MagicMock(path="a.jpg")])
        MockFolder.return_value = mock_folder
        service.open_folder("images/")
        assert service.current_item == mock_folder
        MockFolder.assert_called_once_with("images/")


def test_open_dataset_sets_current_item(service):
    with patch("app.core.dataset.dataset_service.DatasetItem") as MockDataset:
        mock_dataset = MagicMock(train=[MagicMock()], val=[MagicMock()])
        MockDataset.return_value = mock_dataset
        service.open_dataset("dataset/")
        assert service.current_item == mock_dataset


def test_load_json_calls_correct_function(service):
    with patch("app.core.dataset.dataset_service.load_labels_json") as mock_load:
        mock_load.return_value = {"img": []}
        result = service.load_json("labels.json", ["img"])
        mock_load.assert_called_once_with("labels.json", ["img"])
        assert result == {"img": []}


def test_save_json_calls_correct_function(service):
    with patch("app.core.dataset.dataset_service.save_labels_json") as mock_save:
        data = {"x.jpg": []}
        service.save_json(data, "out.json")
        mock_save.assert_called_once_with(data, "out.json")


def test_get_all_files_single_file(service):
    mock_item = MagicMock(path="a.jpg", img_size=(100, 200))
    service.current_item = mock_item
    files = service.get_all_files()
    assert files == [{"path": "a.jpg", "size": (100, 200), "type": "file"}]


def test_set_img_size_updates_file(service):
    mock_file = MagicMock(path="a.jpg", img_size=(10, 10))
    service.current_item = MagicMock(files=[mock_file])
    service.get_file_item = MagicMock(return_value=mock_file)
    service.set_img_size("a.jpg", (200, 300))
    assert mock_file._img_size == (200, 300)
