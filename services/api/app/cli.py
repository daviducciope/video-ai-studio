from __future__ import annotations

import argparse
import json

from app.schemas.project import PreviewRequest, ProjectCreate, SceneSelectionRequest
from app.services.creative import generate_storyboard
from app.services.pipeline import generate_previews, run_render, select_scene_preview
from app.services.repository import ProjectRepository


def create_project_command(args: argparse.Namespace) -> None:
    repo = ProjectRepository()
    project = repo.create_project(
        ProjectCreate(
            title=args.title,
            prompt=args.prompt,
            style=args.style,
            duration_target=args.duration,
            aspect_ratio=args.aspect_ratio,
            avatar_notes=args.avatar_notes,
        )
    )
    print(json.dumps({"id": project.id, "status": project.status}, indent=2))


def storyboard_command(args: argparse.Namespace) -> None:
    repo = ProjectRepository()
    project = repo.get_project(args.project_id)
    project.storyboard = generate_storyboard(project)
    project.status = "storyboard_ready"
    repo.save_project(project)
    print(json.dumps({"id": project.id, "status": project.status}, indent=2))


def previews_command(args: argparse.Namespace) -> None:
    repo = ProjectRepository()
    project = repo.get_project(args.project_id)
    project = generate_previews(project, PreviewRequest(variants_per_scene=args.variants).variants_per_scene)
    repo.save_project(project)
    print(json.dumps({"id": project.id, "status": project.status}, indent=2))


def select_command(args: argparse.Namespace) -> None:
    repo = ProjectRepository()
    project = repo.get_project(args.project_id)
    payload = SceneSelectionRequest(preview_id=args.preview_id)
    project = select_scene_preview(project, args.scene_id, payload.preview_id)
    repo.save_project(project)
    print(json.dumps({"id": project.id, "status": project.status}, indent=2))


def render_command(args: argparse.Namespace) -> None:
    repo = ProjectRepository()
    project = repo.get_project(args.project_id)
    project = repo.start_render_job(project)
    rendered_project, logs = run_render(project)
    repo.update_outputs(rendered_project, rendered_project.outputs, logs)
    print(json.dumps({"id": project.id, "status": "ready"}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video AI Studio CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-project")
    create.add_argument("--title", required=True)
    create.add_argument("--prompt", required=True)
    create.add_argument("--style", default="cinematic")
    create.add_argument("--duration", type=int, default=45)
    create.add_argument("--aspect-ratio", default="16:9")
    create.add_argument("--avatar-notes")
    create.set_defaults(func=create_project_command)

    storyboard = subparsers.add_parser("generate-storyboard")
    storyboard.add_argument("project_id")
    storyboard.set_defaults(func=storyboard_command)

    previews = subparsers.add_parser("generate-previews")
    previews.add_argument("project_id")
    previews.add_argument("--variants", type=int, default=1)
    previews.set_defaults(func=previews_command)

    select = subparsers.add_parser("select-scene")
    select.add_argument("project_id")
    select.add_argument("scene_id")
    select.add_argument("--preview-id")
    select.set_defaults(func=select_command)

    render = subparsers.add_parser("render-project")
    render.add_argument("project_id")
    render.set_defaults(func=render_command)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
