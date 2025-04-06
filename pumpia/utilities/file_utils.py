"""
Some useful file utilities

Functions:
 * get_file_tree_dict
"""
from pathlib import Path
from pumpia.image_handling.image_structures import FileImageSet

type TreeDict = dict[str, TreeDict | FileImageSet]
type TreePathDict = dict[Path, TreePathDict | FileImageSet]


def get_file_tree_dict(images: list[FileImageSet]) -> TreePathDict:
    """
    Returns a dictionary representing a file tree for the given images.

    Parameters
    ----------
    images : list[FileImageSet]

    Returns
    -------
    TreeDict
    """
    start_dict = {im.filepath.parts: im for im in images}
    tree_dict = {}

    for parts, im in start_dict.items():
        current_dict = tree_dict
        for part in parts:
            last_dict = current_dict
            try:
                current_dict = current_dict[part]
            except KeyError:
                current_dict[part] = {}
                current_dict = current_dict[part]
            last_part = part
        last_dict[last_part] = im

    def remove_first_single_input(dictionary: TreeDict) -> TreePathDict:
        new_dict: TreePathDict = {}
        for k, v in dictionary.items():
            if isinstance(v, dict):
                new_v = remove_first_single_input(v)
                if len(new_v.items()) == 1:
                    v_key: Path = list(new_v.keys())[0]
                    val = list(new_v.values())[0]
                    new_k = Path(k) / v_key
                    new_dict[new_k] = val
                else:
                    new_dict[Path(k)] = new_v
            else:
                new_dict[Path(k)] = v
        return new_dict
    return remove_first_single_input(tree_dict)
