from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import textwrap


@dataclass(slots=True)
class PreviewArtifact:
    file_name: str
    relative_path: str
    mime_type: str
    prompt: str


@dataclass(slots=True)
class RenderArtifact:
    file_name: str
    relative_path: str
    mime_type: str
    summary: str


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def build_preview_svg(
    output_dir: Path,
    project_id: str,
    scene_id: str,
    title: str,
    prompt: str,
    style: str,
) -> PreviewArtifact:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{project_id}_{scene_id}_{_stamp()}.svg"
    svg_path = output_dir / file_name
    wrapped_prompt = textwrap.fill(prompt, width=42)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="768" height="432" viewBox="0 0 768 432">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#132238" />
      <stop offset="100%" stop-color="#294768" />
    </linearGradient>
  </defs>
  <rect width="768" height="432" fill="url(#bg)" rx="24"/>
  <rect x="24" y="24" width="720" height="384" rx="18" fill="none" stroke="#f3efe6" stroke-opacity="0.35"/>
  <text x="48" y="76" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="28">{title}</text>
  <text x="48" y="116" fill="#f8d49d" font-family="Verdana, sans-serif" font-size="20">Scene {scene_id}</text>
  <text x="48" y="158" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="18">{style}</text>
  <text x="48" y="204" fill="#dde7f5" font-family="Verdana, sans-serif" font-size="16">{wrapped_prompt}</text>
  <circle cx="628" cy="138" r="52" fill="#f8d49d" fill-opacity="0.14" stroke="#f8d49d" stroke-opacity="0.4"/>
  <rect x="510" y="246" width="180" height="92" rx="18" fill="#f3efe6" fill-opacity="0.08"/>
  <text x="534" y="298" fill="#f3efe6" font-family="Verdana, sans-serif" font-size="18">AI Preview Mock</text>
</svg>
"""
    svg_path.write_text(svg, encoding="utf-8")
    return PreviewArtifact(
        file_name=file_name,
        relative_path=f"previews/{file_name}",
        mime_type="image/svg+xml",
        prompt=prompt,
    )


def build_render_manifest(
    output_dir: Path,
    project_id: str,
    title: str,
    script: str,
    selected_scenes: list[dict[str, str]],
) -> list[RenderArtifact]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{project_id}_{_stamp()}"
    manifest_name = f"{base_name}_render_manifest.txt"
    timeline_name = f"{base_name}_timeline.txt"

    summary_lines = [
        f"Project: {title}",
        "Render mode: mock-local",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "Selected scenes:",
    ]
    summary_lines.extend(f"- {scene['title']}: {scene['voiceover']}" for scene in selected_scenes)
    summary_lines.extend(["", "Script:", script])

    timeline_lines = ["Timeline"]
    for index, scene in enumerate(selected_scenes, start=1):
        timeline_lines.append(f"{index:02d}. {scene['title']} -> {scene['visual_prompt']}")

    manifest_path = output_dir / manifest_name
    timeline_path = output_dir / timeline_name
    manifest_path.write_text("\n".join(summary_lines), encoding="utf-8")
    timeline_path.write_text("\n".join(timeline_lines), encoding="utf-8")

    return [
        RenderArtifact(
            file_name=manifest_name,
            relative_path=f"renders/{manifest_name}",
            mime_type="text/plain",
            summary="Manifest del render finale mock",
        ),
        RenderArtifact(
            file_name=timeline_name,
            relative_path=f"renders/{timeline_name}",
            mime_type="text/plain",
            summary="Timeline delle scene selezionate",
        ),
    ]
