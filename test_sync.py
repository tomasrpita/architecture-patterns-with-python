import shutil
import tempfile
from pathlib import Path
from sync import sync


def test_when_a_file_exists_in_source_but_not_the_destination():
    try:
        source = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()
        
        content = "I am a very useful file"
        (Path(source, "my-file")).write_text(content)

        sync(source, dest)

        expected_path = Path(dest, "my-file")
        assert expected_path.exists()
        assert expected_path.read_text() == content

    finally:
        shutil.rmtree(source)
        shutil.rmtree(dest)

def test_when_a_file_has_been_renamed_in_the_source():
    try:
        source = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()

        content = "I am a file that was renamed"
        source_path = Path(source, "source-file")
        old_dest_path = Path(dest, "dest-file")
        espected_desd_path = Path(dest, "source-file")

        source_path.write_text(content)
        old_dest_path.write_text(content)

        sync(source, dest)

        assert old_dest_path.exists() == False
        assert espected_desd_path.exists()
        assert espected_desd_path.read_text() == content
        
    finally:
        shutil.rmtree(source)
        shutil.rmtree(dest)
