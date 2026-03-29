from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import Flask, render_template, request

ROOT_DIR = Path(__file__).resolve().parent.parent
Q1_DIR = ROOT_DIR / "q1-bilibili-downloader"
Q2_DIR = ROOT_DIR / "q2-ai-chat-pipeline"
Q1_SCRIPT = Q1_DIR / "download_bilibili.py"
Q2_SCRIPT = Q2_DIR / "process_chat_logs.py"
DEFAULT_ENV_FILE = Q2_DIR / ".env"
DEFAULT_RESULT_FILE = Q2_DIR / "result.json"
PYTHON_BIN = Path(sys.executable)


@dataclass
class UiState:
    mode: str = "q1"
    message_input: str = ""
    command: str = ""
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    result_preview: str = ""
    q1_output_dir: str = str(Q1_DIR / "downloads")
    q1_cookie_file: str = ""
    q1_proxy: str = ""
    q1_audio_only: bool = False
    q2_limit: str = "20"
    q2_character_name: str = "星语陪伴师"
    q2_result_file: str = str(DEFAULT_RESULT_FILE)
    q2_processed_status: str = "completed"
    q2_mock: bool = False
    q2_dry_run: bool = False


app = Flask(__name__)


def resolve_input_path(raw_value: str, base_dir: Path) -> Path:
    path = Path(raw_value)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def run_command(command: list[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout, completed.stderr


def read_result_preview(path: Path) -> str:
    if not path.exists():
        return f"未找到结果文件：{path}"
    return path.read_text(encoding="utf-8", errors="replace")


def state_from_form(form: Any) -> UiState:
    mode = (form.get("mode") or "q1").strip().lower()
    if mode not in ("q1", "q2"):
        mode = "q1"

    return UiState(
        mode=mode,
        message_input=(form.get("message_input") or "").strip(),
        q1_output_dir=(form.get("q1_output_dir") or str(Q1_DIR / "downloads")).strip(),
        q1_cookie_file=(form.get("q1_cookie_file") or "").strip(),
        q1_proxy=(form.get("q1_proxy") or "").strip(),
        q1_audio_only=form.get("q1_audio_only") == "on",
        q2_limit=(form.get("q2_limit") or "20").strip(),
        q2_character_name=(form.get("q2_character_name") or "星语陪伴师").strip(),
        q2_result_file=(form.get("q2_result_file") or str(DEFAULT_RESULT_FILE)).strip(),
        q2_processed_status=(form.get("q2_processed_status") or "completed").strip(),
        q2_mock=form.get("q2_mock") == "on",
        q2_dry_run=form.get("q2_dry_run") == "on",
    )


def build_q1_command(state: UiState) -> list[str]:
    command = [
        str(PYTHON_BIN),
        str(Q1_SCRIPT),
        state.message_input,
        "-o",
        state.q1_output_dir,
    ]
    if state.q1_cookie_file:
        command.extend(["--cookie-file", state.q1_cookie_file])
    if state.q1_proxy:
        command.extend(["--proxy", state.q1_proxy])
    if state.q1_audio_only:
        command.append("--audio-only")
    return command


def build_q2_command(state: UiState) -> list[str]:
    limit = state.q2_limit
    try:
        limit = str(max(1, int(limit)))
    except ValueError:
        limit = "20"

    command = [
        str(PYTHON_BIN),
        str(Q2_SCRIPT),
        "--env-file",
        str(DEFAULT_ENV_FILE),
        "--limit",
        limit,
        "--character-name",
        state.q2_character_name,
        "--processed-status",
        state.q2_processed_status,
        "--result-file",
        state.q2_result_file,
    ]
    if state.q2_mock:
        command.append("--mock")
    if state.q2_dry_run:
        command.append("--dry-run")
    return command


def build_assistant_message(state: UiState) -> str:
    if state.exit_code is None:
        return "请输入一条消息并点击发送（可选参数默认收起在下方）。"
    if state.exit_code == 0:
        if state.mode == "q1":
            return "题目 1 执行成功（退出码 0）。可继续输入下一条视频链接。"
        return "题目 2 执行成功（退出码 0）。请在下方核对 result.json 字段。"
    return f"执行失败（退出码 {state.exit_code}）。请根据日志检查参数或网络。"


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    state = UiState()

    if request.method == "POST":
        state = state_from_form(request.form)

        if state.mode == "q1":
            if not state.message_input:
                state.exit_code = 1
                state.stderr = "题目 1 需要在输入框填写 Bilibili 视频链接（必填）。"
            else:
                command = build_q1_command(state)
                state.command = subprocess.list2cmdline(command)
                code, out, err = run_command(command, cwd=ROOT_DIR)
                state.exit_code = code
                state.stdout = out
                state.stderr = err
        else:
            command = build_q2_command(state)
            state.command = subprocess.list2cmdline(command)
            code, out, err = run_command(command, cwd=ROOT_DIR)
            state.exit_code = code
            state.stdout = out
            state.stderr = err

    preview_path = resolve_input_path(state.q2_result_file, ROOT_DIR)
    state.result_preview = read_result_preview(preview_path)
    assistant_message = build_assistant_message(state)
    return render_template("index.html", state=state, assistant_message=assistant_message)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False)
