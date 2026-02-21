from tea_kitsune.storage import Storage


def test_user_note_and_visit_flow(tmp_path):
    db = tmp_path / "test.db"
    store = Storage(str(db))

    user = store.get_or_create_user(1001, "Tea Lover")
    same_user = store.get_or_create_user(1001, "Tea Lover")
    assert same_user.qr_code == user.qr_code

    store.add_note(1001, "Да Хун Пао", "минеральный", "глубокий и сладкий")
    notes = store.get_notes(1001)
    assert len(notes) == 1
    assert notes[0]["tea_name"] == "Да Хун Пао"

    tg_id = store.add_visit_by_code(user.qr_code)
    assert tg_id == 1001
    assert store.visits_count(1001) == 1

    assert store.add_visit_by_code("UNKNOWN") is None
