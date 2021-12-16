import os


def get_project_dir() -> str:

    """
    Get the full path to the repository

    """

    dir_as_list = os.path.dirname(__file__).split("/")
    index = dir_as_list.index("crawling")
    project_directory = f"/{os.path.join(*dir_as_list[:index])}"

    return project_directory


def get_file(relative_path: str) -> str:

    """
    Given the relative path to the repository, return the full path

    Args:
        relative_path: relative path of file to the project directory

    """

    return os.path.join(get_project_dir(), relative_path)


def get_app_dirs(platform: str, project: str):

    dir_train = os.path.join(get_project_dir(), 'data', 'app', platform)
    dir_result = os.path.join(dir_train, project)
    if not os.path.isdir(dir_result):
        os.makedirs(dir_result)

    return dir_train, dir_result
