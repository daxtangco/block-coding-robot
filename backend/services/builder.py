import asyncio
import uuid
from pathlib import Path
from typing import Tuple, Optional

BUILDS_DIR = Path("builds")
BUILDS_DIR.mkdir(exist_ok=True)

async def compile_arduino(sketch_content: str, board_fqbn: str = "esp32:esp32:esp32") -> Tuple[bool, str, Optional[Path]]:
    """
    Compiles Arduino sketch using arduino-cli.
    Returns (success, output_log, binary_path).
    """
    build_id = str(uuid.uuid4())
    build_dir = BUILDS_DIR / build_id
    build_dir.mkdir()

    sketch_dir = build_dir / "sketch"
    sketch_dir.mkdir()
    sketch_file = sketch_dir / "sketch.ino"
    sketch_file.write_text(sketch_content)

    # Compile command
    cmd = [
        "arduino-cli", "compile",
        "--fqbn", board_fqbn,
        "--output-dir", str(build_dir),
        str(sketch_dir)
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await process.communicate()
        output = stdout.decode()

        if process.returncode == 0:
            # Find .bin file
            bin_file = build_dir / "sketch.ino.bin"
            if bin_file.exists():
                return True, output, bin_file
            else:
                return False, f"Build succeeded but .bin not found\n{output}", None
        else:
            return False, output, None
    except FileNotFoundError:
        return False, "arduino-cli not found. Please install and configure it (see docs/ARDUINO_CLI_SETUP.md)", None
    except Exception as e:
        return False, f"Build error: {str(e)}", None
