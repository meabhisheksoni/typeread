"""
Integration tests for the API Dispatcher covering all operations in api.json.
"""

import tempfile
import pytest

from src.app import create_app


@pytest.fixture
def test_app():
    with tempfile.TemporaryDirectory() as data_dir:
        app = create_app(data_dir=data_dir)
        yield app


def test_api_dispatcher_full_lifecycle(test_app):
    dispatcher = test_app.dispatcher

    # 1. Create a markdown sample file to import
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# Chapter 1: Introduction\nThis is a typing test passage.\n")
        sample_path = f.name

    # POST /documents/import
    res_import = dispatcher.dispatch("POST", "/documents/import", body={"filePath": sample_path})
    assert res_import.status_code == 201
    doc_id = res_import.data["document_id"]
    assert doc_id != ""

    # POST /documents/{id}/commit
    res_commit = dispatcher.dispatch(
        "POST",
        f"/documents/{doc_id}/commit",
        body={"title": "Custom Title", "chapters": []},
    )
    assert res_commit.status_code == 201
    assert res_commit.data["title"] == "Custom Title"

    # GET /documents
    res_list = dispatcher.dispatch("GET", "/documents")
    assert res_list.status_code == 200
    assert len(res_list.data) == 1
    assert res_list.data[0]["id"] == doc_id

    # GET /documents/{id}
    res_get = dispatcher.dispatch("GET", f"/documents/{doc_id}")
    assert res_get.status_code == 200
    assert res_get.data["id"] == doc_id

    # GET /documents/{id}/structure
    res_struct = dispatcher.dispatch("GET", f"/documents/{doc_id}/structure")
    assert res_struct.status_code == 200
    chap_id = res_struct.data["chapters"][0]["id"]
    sec_id = res_struct.data["chapters"][0]["sections"][0]["id"]

    # PATCH /documents/{id}/exclusions
    res_excl = dispatcher.dispatch(
        "PATCH",
        f"/documents/{doc_id}/exclusions",
        body={"targetType": "chapter", "targetId": chap_id, "includedInPractice": False},
    )
    assert res_excl.status_code == 200

    # GET /documents/{id}/sections/{sec_id}/content
    res_content = dispatcher.dispatch("GET", f"/documents/{doc_id}/sections/{sec_id}/content")
    assert res_content.status_code == 200
    assert len(res_content.data["paragraphs"]) >= 1

    # POST /sessions/start
    res_start = dispatcher.dispatch(
        "POST",
        "/sessions/start",
        body={
            "documentId": doc_id,
            "chapterId": chap_id,
            "sectionId": sec_id,
            "typingMode": "standard",
            "errorHandlingMode": "allow_with_backspace",
        },
    )
    assert res_start.status_code == 201
    sess_id = res_start.data["id"]

    # POST /sessions/{id}/keystrokes
    res_strokes = dispatcher.dispatch(
        "POST",
        f"/sessions/{sess_id}/keystrokes",
        body={
            "keystrokes": [
                {"timestamp_ms": 1000, "key": "T", "expected_char": "T", "position": 0, "is_backspace": False},
                {"timestamp_ms": 1150, "key": "h", "expected_char": "h", "position": 1, "is_backspace": False},
            ]
        },
    )
    assert res_strokes.status_code == 200
    assert res_strokes.data["currentPosition"] == 2
    assert res_strokes.data["currentMetrics"]["correct_keystrokes"] == 2

    # POST /sessions/{id}/state (Pause)
    res_pause = dispatcher.dispatch("POST", f"/sessions/{sess_id}/state", body={"state": "paused"})
    assert res_pause.status_code == 200
    assert res_pause.data["state"] == "paused"

    # GET /sessions/active
    res_act = dispatcher.dispatch("GET", "/sessions/active")
    assert res_act.status_code == 200
    assert res_act.data["id"] == sess_id

    # POST /sessions/{id}/complete
    res_comp = dispatcher.dispatch("POST", f"/sessions/{sess_id}/complete")
    assert res_comp.status_code == 200
    assert res_comp.data["state"] == "completed"

    # GET /analytics/overview
    res_overview = dispatcher.dispatch("GET", "/analytics/overview")
    assert res_overview.status_code == 200
    assert res_overview.data["totalCharactersTyped"] >= 2

    # GET /analytics/trends
    res_trends = dispatcher.dispatch("GET", "/analytics/trends", params={"days": 7})
    assert res_trends.status_code == 200
    assert len(res_trends.data["days"]) == 7

    # GET /analytics/documents/{id}
    res_doc_an = dispatcher.dispatch("GET", f"/analytics/documents/{doc_id}")
    assert res_doc_an.status_code == 200
    assert res_doc_an.data["documentId"] == doc_id

    # POST /practice/drills/generate
    res_drill = dispatcher.dispatch(
        "POST",
        "/practice/drills/generate",
        body={"wordCount": 25, "documentId": doc_id},
    )
    assert res_drill.status_code == 200
    assert res_drill.data["word_count"] == 25

    # POST /search
    res_search = dispatcher.dispatch("POST", "/search", body={"query": "typing"})
    assert res_search.status_code == 200
    assert res_search.data["total_matches"] >= 1

    # Bookmarks
    p_id = res_content.data["paragraphs"][0]["id"]
    res_bm_post = dispatcher.dispatch(
        "POST",
        "/bookmarks",
        body={
            "documentId": doc_id,
            "chapterId": chap_id,
            "sectionId": sec_id,
            "paragraphId": p_id,
            "characterOffset": 5,
            "title": "Start Bookmark",
        },
    )
    assert res_bm_post.status_code == 201
    bm_id = res_bm_post.data["id"]

    res_bm_list = dispatcher.dispatch("GET", "/bookmarks")
    assert res_bm_list.status_code == 200
    assert len(res_bm_list.data) == 1

    res_bm_del = dispatcher.dispatch("DELETE", f"/bookmarks/{bm_id}")
    assert res_bm_del.status_code == 204

    # Notes
    res_note_post = dispatcher.dispatch(
        "POST",
        "/notes",
        body={
            "documentId": doc_id,
            "chapterId": chap_id,
            "sectionId": sec_id,
            "paragraphId": p_id,
            "content": "A thoughtful note",
        },
    )
    assert res_note_post.status_code == 201
    note_id = res_note_post.data["id"]

    res_note_put = dispatcher.dispatch("PUT", f"/notes/{note_id}", body={"content": "Updated note"})
    assert res_note_put.status_code == 200
    assert res_note_put.data["content"] == "Updated note"

    res_note_del = dispatcher.dispatch("DELETE", f"/notes/{note_id}")
    assert res_note_del.status_code == 204

    # Settings
    res_settings_get = dispatcher.dispatch("GET", "/settings")
    assert res_settings_get.status_code == 200

    # Backup Export, Validate, Restore
    with tempfile.TemporaryDirectory() as dest_backup_dir:
        res_export = dispatcher.dispatch("POST", "/backup/export", body={"destinationDirectory": dest_backup_dir})
        assert res_export.status_code == 201
        b_file = res_export.data["backupFilePath"]

        res_val = dispatcher.dispatch("POST", "/backup/validate", body={"backupFilePath": b_file})
        assert res_val.status_code == 200
        assert res_val.data["is_valid"] is True

        res_rest = dispatcher.dispatch("POST", "/backup/restore", body={"backupFilePath": b_file})
        assert res_rest.status_code == 200
        assert res_rest.data["success"] is True

    # DELETE /documents/{id}
    res_doc_del = dispatcher.dispatch("DELETE", f"/documents/{doc_id}")
    assert res_doc_del.status_code == 204
