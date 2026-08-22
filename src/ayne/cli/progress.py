"""Shared terminal progress rendering for collection commands."""

from collections.abc import Callable
from typing import Any

from rich.progress import BarColumn, MofNCompleteColumn, Progress, Task, TaskID
from rich.text import Text


class DeterminateBarColumn(BarColumn):
    """Render a bar only after a task has a known total."""

    def render(self, task: Task) -> Any:
        if task.total is None:
            return Text()
        return super().render(task)


class DeterminateMofNCompleteColumn(MofNCompleteColumn):
    """Render counts only after a task has a known total."""

    def render(self, task: Task) -> Text:
        if task.total is None:
            return Text()
        return super().render(task)


def update_collection_progress(
    progress: Progress,
    task_id: TaskID,
    stage: str,
    completed: int | None,
    total: int | None,
) -> None:
    """Update the single visible task for a collection workflow."""
    if stage.lower().endswith("complete"):
        progress.update(
            task_id,
            total=total,
            completed=completed if completed is not None else (total or 0),
        )
        return

    progress.update(
        task_id,
        description=f"{stage}...",
        total=total,
        completed=completed if completed is not None else 0,
    )


def create_collection_progress_callback(
    progress: Progress,
    task_id: TaskID,
    retain_stages: Callable[[str], bool] | None = None,
) -> Callable[[str, int | None, int | None], None]:
    """Create a progress callback with optional persistent stage tasks."""
    retained_task_ids: dict[str, TaskID] = {}
    active_task_id: TaskID | None = task_id

    def _on_progress(stage: str, completed: int | None, total: int | None) -> None:
        nonlocal active_task_id

        if retain_stages is not None and retain_stages(stage):
            retained_task_id = retained_task_ids.get(stage)
            if retained_task_id is None:
                retained_task_id = progress.add_task(f"{stage}...", total=total)
                retained_task_ids[stage] = retained_task_id

                if active_task_id is not None:
                    progress.remove_task(active_task_id)
                    active_task_id = None

            update_collection_progress(progress, retained_task_id, stage, completed, total)
            return

        if active_task_id is None:
            active_task_id = progress.add_task("Updating collection...", total=None)

        update_collection_progress(progress, active_task_id, stage, completed, total)

    return _on_progress
