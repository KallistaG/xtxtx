import json

from bible_automation.core import Verse, choose_verse, make_caption


def test_choose_verse_loads_curated_entry(tmp_path, monkeypatch):
    source = tmp_path / "verses.json"
    source.write_text(json.dumps([{"reference": "Psalm 1:1", "text": "Blessed is the man."}]))
    verse = choose_verse(source)
    assert verse == Verse("Psalm 1:1", "Blessed is the man.")


def test_caption_includes_quote_reference_translation_and_tags():
    caption = make_caption(Verse("John 3:16", "For God so loved the world."))
    assert "For God so loved the world." in caption
    assert "John 3:16 (KJV)" in caption
    assert "#BibleVerse" in caption
