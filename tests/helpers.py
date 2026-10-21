import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# Hồ sơ nhạc không tồn tại -> dùng mặc định 80 BPM, để kiểm thử không phụ thuộc bài nhạc đang chọn.
TEST_PROFILE = "test-default-80"
