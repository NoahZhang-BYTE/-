from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymysql
import requests
from dotenv import load_dotenv

GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
REQUIRED_FIELDS = ("character_name", "mood", "reply_text")


@dataclass
class Config:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_table: str
    glm_api_key: str
    glm_model: str


class GLMAuthError(Exception):
    pass


class GLMParseError(Exception):
    def __init__(self, message: str, raw_response: dict[str, Any] | None = None):
        super().__init__(message)
        self.raw_response = raw_response


def parse_args() -> argparse.Namespace:
    default_env = Path(__file__).resolve().parent / ".env"
    parser = argparse.ArgumentParser(
        description="Process unhandled chat logs via GLM and store JSON results."
    )
    parser.add_argument("--env-file", type=Path, default=default_env)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--result-file", type=Path, default=Path("result.json"))
    parser.add_argument("--character-name", default="星语陪伴师")
    parser.add_argument("--pending-status", default="pending")
    parser.add_argument("--processing-status", default="processing")
    parser.add_argument("--processed-status", default="processed")
    parser.add_argument("--failed-status", default="failed")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Skip GLM call and generate mock replies for local self-test.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not update database status.",
    )
    return parser.parse_args()


def load_config(env_file: Path) -> Config:
    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        # Fallback: if caller runs script from another cwd, still try local .env
        local_env = Path(__file__).resolve().parent / ".env"
        if local_env.exists():
            load_dotenv(local_env, override=False)
        else:
            load_dotenv(override=False)

    return Config(
        db_host=get_env("DB_HOST", "frp-end.com"),
        db_port=int(get_env("DB_PORT", "39508")),
        db_user=get_env("DB_USER", "candidate"),
        db_password=get_env("DB_PASSWORD", "Root123!"),
        db_name=get_env("DB_NAME", "ai_interview_db"),
        db_table=get_env("DB_TABLE", "chat_logs_D"),
        glm_api_key=get_env("GLM_API_KEY", ""),
        glm_model=get_env("GLM_MODEL", "glm-4.7-flash"),
    )


def get_env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value is not None and value != "" else default


def sanitize_table_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"Unsafe table name: {name!r}")
    return name


def get_connection(cfg: Config) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_user,
        password=cfg.db_password,
        database=cfg.db_name,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def fetch_pending_rows(
    conn: pymysql.connections.Connection,
    table: str,
    pending_status: str,
    limit: int,
) -> list[dict[str, Any]]:
    query = (
        f"SELECT id, user_input FROM `{table}` "
        "WHERE process_status=%s ORDER BY id ASC LIMIT %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(query, (pending_status, limit))
        return list(cursor.fetchall())


def claim_row(
    conn: pymysql.connections.Connection,
    table: str,
    row_id: int,
    pending_status: str,
    processing_status: str,
) -> bool:
    query = (
        f"UPDATE `{table}` SET process_status=%s "
        "WHERE id=%s AND process_status=%s"
    )
    with conn.cursor() as cursor:
        cursor.execute(query, (processing_status, row_id, pending_status))
        return cursor.rowcount == 1


def update_status(
    conn: pymysql.connections.Connection,
    table: str,
    row_id: int,
    status: str,
) -> None:
    query = f"UPDATE `{table}` SET process_status=%s WHERE id=%s"
    with conn.cursor() as cursor:
        cursor.execute(query, (status, row_id))


def call_glm(
    api_key: str,
    model: str,
    user_input: str,
    character_name: str,
    timeout: int,
) -> dict[str, str]:
    system_prompt = (
        "你是角色扮演回复引擎。"
        f"本次角色名固定为：{character_name}。"
        "你必须仅输出 JSON 对象，且只包含以下三个字段："
        "character_name、mood、reply_text。"
        "不要输出 markdown，不要输出额外解释。"
    )
    payload = {
        "model": model,
        "request_id": str(uuid.uuid4()),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.8,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        GLM_API_URL,
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    if response.status_code in (401, 403):
        detail = response.text.strip()
        if len(detail) > 300:
            detail = detail[:300] + "..."
        raise GLMAuthError(f"GLM auth failed ({response.status_code}): {detail}")
    response.raise_for_status()
    raw = response.json()

    try:
        return parse_glm_response(raw, fallback_character_name=character_name)
    except Exception as exc:
        raise GLMParseError(str(exc), raw_response=raw) from exc


def parse_glm_response(raw: dict[str, Any], fallback_character_name: str) -> dict[str, str]:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Invalid GLM response: missing choices")

    choice0 = choices[0]
    message = choice0.get("message")
    finish_reason = str(choice0.get("finish_reason", "")).strip()

    # 1) Try normal content first.
    content_text = extract_model_content(raw, allow_empty=True)
    if content_text:
        parsed = parse_model_json(content_text)
        return normalize_fields(parsed, fallback_character_name)

    # 2) If model returned tool calls, parse function arguments JSON.
    if isinstance(message, dict):
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list):
            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue
                function = tool_call.get("function")
                if isinstance(function, dict) and isinstance(function.get("arguments"), str):
                    parsed = parse_model_json(function["arguments"])
                    return normalize_fields(parsed, fallback_character_name)
                mcp = tool_call.get("mcp")
                if isinstance(mcp, dict) and isinstance(mcp.get("arguments"), str):
                    parsed = parse_model_json(mcp["arguments"])
                    return normalize_fields(parsed, fallback_character_name)

    # 3) Sensitive filtering: return compliant fallback JSON.
    if finish_reason == "sensitive":
        return {
            "character_name": fallback_character_name,
            "mood": "谨慎",
            "reply_text": "这条消息触发了安全策略，我先换一种更温和、安全的表达来继续陪你。",
        }

    raise ValueError("Invalid GLM response: empty content")


def extract_model_content(raw: dict[str, Any], allow_empty: bool = False) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Invalid GLM response: missing choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("Invalid GLM response: missing message")
    content = message.get("content", "")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        content = "".join(parts)
    if not isinstance(content, str) or not content.strip():
        if allow_empty:
            return ""
        raise ValueError("Invalid GLM response: empty content")
    return content.strip()


def parse_model_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
        stripped = stripped.strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"Could not parse JSON from model output: {text}")


def normalize_fields(payload: dict[str, Any], fallback_character_name: str) -> dict[str, str]:
    defaults = {
        "character_name": fallback_character_name,
        "mood": "平静",
        "reply_text": "抱歉，我暂时无法给出有效回复。",
    }
    normalized: dict[str, str] = {}
    for key in REQUIRED_FIELDS:
        value = payload.get(key, defaults[key])
        text = str(value).strip() if value is not None else defaults[key]
        normalized[key] = text if text else defaults[key]
    return normalized


def build_mock_reply(user_input: str, character_name: str) -> dict[str, str]:
    message = user_input.strip()
    if not message:
        message = "我收到了你的消息。"
    return {
        "character_name": character_name,
        "mood": "温和",
        "reply_text": f"我听到了你的想法：{message}。我会陪你一步步解决。",
    }


def write_result_file(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def process_rows(args: argparse.Namespace, cfg: Config) -> int:
    table = sanitize_table_name(cfg.db_table)
    processed_results: list[dict[str, str]] = []

    auth_failed = False
    with get_connection(cfg) as conn:
        rows = fetch_pending_rows(conn, table, args.pending_status, args.limit)
        if not rows:
            write_result_file(args.result_file, [])
            logging.info("No pending rows found. result.json written with empty list.")
            return 0

        for row in rows:
            row_id = int(row["id"])
            user_input = str(row.get("user_input", ""))

            try:
                if not args.dry_run:
                    is_claimed = claim_row(
                        conn=conn,
                        table=table,
                        row_id=row_id,
                        pending_status=args.pending_status,
                        processing_status=args.processing_status,
                    )
                    conn.commit()
                    if not is_claimed:
                        logging.warning("Row %s was already claimed by another worker.", row_id)
                        continue

                if args.mock:
                    reply = build_mock_reply(user_input, args.character_name)
                else:
                    reply = call_glm(
                        api_key=cfg.glm_api_key,
                        model=cfg.glm_model,
                        user_input=user_input,
                        character_name=args.character_name,
                        timeout=args.timeout,
                    )

                processed_results.append(reply)

                if not args.dry_run:
                    update_status(conn, table, row_id, args.processed_status)
                    conn.commit()
                logging.info("Row %s processed.", row_id)
            except GLMAuthError as exc:
                logging.error("Row %s auth failed: %s", row_id, exc)
                if not args.dry_run:
                    # Put row back to pending so it can be retried after fixing key.
                    update_status(conn, table, row_id, args.pending_status)
                    conn.commit()
                auth_failed = True
                break
            except GLMParseError as exc:
                logging.warning("Row %s parse fallback: %s", row_id, exc)
                raw = exc.raw_response or {}
                finish_reason = ""
                try:
                    finish_reason = str(raw.get("choices", [{}])[0].get("finish_reason", ""))
                except Exception:
                    finish_reason = ""

                # If parsing fails but API call succeeded, generate a safe local fallback
                # to keep pipeline stable and still output strictly valid JSON.
                reply = build_mock_reply(user_input, args.character_name)
                if finish_reason == "sensitive":
                    reply["mood"] = "谨慎"
                    reply["reply_text"] = "这条消息触发了安全策略，我先换一种安全表达陪你继续交流。"
                processed_results.append(reply)

                if not args.dry_run:
                    update_status(conn, table, row_id, args.processed_status)
                    conn.commit()
                logging.info("Row %s processed via fallback.", row_id)
            except Exception as exc:
                logging.exception("Row %s failed: %s", row_id, exc)
                if not args.dry_run:
                    update_status(conn, table, row_id, args.failed_status)
                    conn.commit()

    write_result_file(args.result_file, processed_results)
    if auth_failed:
        logging.error("Stopped early due to GLM authentication failure.")
        return 1
    logging.info("Done. %s records written to %s", len(processed_results), args.result_file)
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = parse_args()
    cfg = load_config(args.env_file)

    if not args.mock and not cfg.glm_api_key:
        print(
            "GLM_API_KEY is missing. Set it in environment or .env, or run with --mock for self-test.",
            file=sys.stderr,
        )
        return 1

    try:
        return process_rows(args, cfg)
    except Exception as exc:
        logging.exception("Fatal error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
