"""Unit tests for shared collection progress rendering."""

from rich.progress import Progress

from ayne.cli.progress import create_collection_progress_callback


def test_retained_stages_keep_completed_tasks_visible() -> None:
    progress = Progress()
    initial_task = progress.add_task("Discovering movies...", total=None)
    on_progress = create_collection_progress_callback(
        progress,
        initial_task,
        retain_stages=lambda stage: stage.startswith("Fetching TMDB pages"),
    )

    on_progress("Fetching TMDB pages (2000-2006)", 0, 3)
    on_progress("Fetching TMDB pages (2000-2006)", 3, 3)
    on_progress("Fetching TMDB pages (2007-2013)", 0, 4)

    assert [task.description for task in progress.tasks] == [
        "Fetching TMDB pages (2000-2006)...",
        "Fetching TMDB pages (2007-2013)...",
    ]
    assert progress.tasks[0].completed == 3
    assert progress.tasks[1].completed == 0


def test_non_retained_stage_uses_status_task_after_retained_tasks() -> None:
    progress = Progress()
    initial_task = progress.add_task("Discovering movies...", total=None)
    on_progress = create_collection_progress_callback(
        progress,
        initial_task,
        retain_stages=lambda stage: stage.startswith("Fetching TMDB pages"),
    )

    on_progress("Fetching TMDB pages (2000-2006)", 2, 3)
    on_progress("Finding movies due for refresh", None, None)

    assert [task.description for task in progress.tasks] == [
        "Fetching TMDB pages (2000-2006)...",
        "Finding movies due for refresh...",
    ]
