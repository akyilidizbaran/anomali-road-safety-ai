from scripts.benchmarks.prepare_phone_finetune_samples import (
    face_near_crop_bbox,
    parse_frame_set,
)


def test_parse_frame_set_accepts_ranges():
    assert parse_frame_set(["10", "12-14"]) == {10, 12, 13, 14}


def test_face_near_crop_clamps_to_frame():
    assert face_near_crop_bbox([10, 10, 30, 40], 100, 100)[0] == 0
