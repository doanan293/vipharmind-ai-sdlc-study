import pytest
from synthetic import write_study

from sdlc_analysis.load import load_runs, load_tasks


@pytest.fixture(scope="session")
def study(tmp_path_factory):
    root = tmp_path_factory.mktemp("study")
    tasks_dir, results = write_study(root)
    tasks = load_tasks(tasks_dir)
    return tasks_dir, results, tasks, load_runs(results, tasks)


@pytest.fixture(scope="session")
def jitter_study(tmp_path_factory):
    root = tmp_path_factory.mktemp("jitter")
    tasks_dir, results = write_study(root, jitter=True)
    tasks = load_tasks(tasks_dir)
    return tasks_dir, results, tasks, load_runs(results, tasks)
