import xml.etree.ElementTree as ET
import dataclasses as dc
from dataclasses import dataclass
from pathlib import Path
import re
import itertools


@dataclass
class Tag:
    name: str
    keyword: str
    group: int
    element: int
    parents: dict[tuple[int, int], bool] = dc.field(default_factory=dict)
    alternative_tags: list[tuple[int, int]] = dc.field(default_factory=list)
    modalities: set[str] = dc.field(default_factory=set)
    written: bool = False
    modalities_set: bool = False

    @property
    def as_tuple(self) -> tuple[int, int]:
        return (self.group, self.element)

    def get(self) -> tuple[int, int]:
        return self.as_tuple

    def add_parents(self,
                    parents: tuple[int, int] | list[tuple[int, int]],
                    frame_link: bool | list[bool] = False):
        is_frame_link_list: bool = False
        if isinstance(frame_link, list):
            if isinstance(parents, list):
                if len(parents) != len(frame_link):
                    raise ValueError("lists must be same length")
            else:
                raise ValueError("parents must be list if frame_link is")
            is_frame_link_list = True

        if isinstance(parents, list):
            # pylint: disable-next=redefined-outer-name
            for i, t in enumerate(parents):
                if t != self.as_tuple:
                    if is_frame_link_list:
                        self.parents[t] = frame_link[i]  # type: ignore
                    else:
                        self.parents[t] = frame_link  # type: ignore
        elif parents != self.as_tuple:
            self.parents[parents] = frame_link  # type: ignore

    # pylint: disable-next=redefined-outer-name
    def add_modality(self, modality: str):
        self.modalities.add(modality)

    def set_parent_modalities(self, tags: dict[tuple[int, int], 'Tag'], chain: list['Tag']):
        if self not in chain:
            chain.append(self)
            for p, _ in self.parents.items():
                for m in self.modalities:
                    tags[p].modalities.add(m)
                tags[p].set_parent_modalities(tags, chain)

    def __str__(self) -> str:
        return f"({self.group:04X}, {self.element:04X})"


@dataclass
class Table:
    rows: list['Tag | Table'] = dc.field(default_factory=list)
    sub_rows: list['Tag | Table'] = dc.field(default_factory=list)

    def add_parents(self,
                    parents: tuple[int, int] | list[tuple[int, int]],
                    frame_link: bool | list[bool] = False):
        for row in self.rows:
            row.add_parents(parents, frame_link)

    # pylint: disable-next=redefined-outer-name
    def add_modality(self, modality: str):
        for row in self.rows:
            row.add_modality(modality)
        for row in self.sub_rows:
            row.add_modality(modality)


def str_to_tags(tag_str: str) -> list[tuple[int, int]]:
    tag_str = tag_str.strip()
    tag_str = tag_str.strip("()")
    tag_str_list = tag_str.split(",")
    group_str = tag_str_list[0]
    element_str = tag_str_list[1]

    groups: list[int] = []
    elements: list[int] = []

    full_hex = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]
    even_hex = ["0", "2", "4", "6", "8", "A", "C", "E"]

    if "x" in group_str:
        num_x = group_str.count("x")
        if group_str[-1] == "x":
            num_x -= 1
            if num_x == 0:
                replacements = itertools.product(even_hex)
            else:
                replacements = itertools.product(*[full_hex for _ in range(num_x)],
                                                 even_hex)
        else:
            replacements = itertools.product(*[full_hex for _ in range(num_x)])
        for values in replacements:
            new_group_str = group_str
            for value in values:
                new_group_str = new_group_str.replace("x", value, 1)
            groups.append(int("0x" + new_group_str, 0))
    else:
        groups.append(int("0x" + group_str, 0))

    if "x" in element_str:
        num_x = element_str.count("x")
        replacements = itertools.product(*[full_hex for _ in range(num_x)])
        for values in replacements:
            new_element_str = element_str
            for value in values:
                new_element_str = new_element_str.replace("x", value, 1)
            elements.append(int("0x" + new_element_str, 0))
    else:
        elements.append(int("0x" + element_str, 0))

    return [tag for tag in itertools.product(groups, elements)]


# pylint: disable-next=redefined-outer-name
def section_tables(root: ET.Element, section_name: str) -> list[str]:
    # pylint: disable-next=redefined-outer-name
    tables: list[str] = []
    for section in root.iter(f'{{{namespace}}}section'):
        # pylint: disable-next=redefined-outer-name
        label = section.get("label")
        if label == section_name:
            # pylint: disable-next=redefined-outer-name
            for table in section.iter(f'{{{namespace}}}table'):
                tab_lab = table.get("label")
                if tab_lab is not None:
                    tables.append(tab_lab)

    return tables

############################################
# STEP 1


tags_xml = Path(__file__).parent / "part06.xml"

tree = ET.parse(tags_xml)
root = tree.getroot()
namespace = root.tag[1:].split("}")[0]
COLUMNS = ["Tag", "Name", "Keyword", "VR", "VM", ""]  # for tables which define tags

tags: dict[tuple[int, int], Tag] = {}

for table in root.iter(f'{{{namespace}}}table'):
    head = table.find(f"{{{namespace}}}thead")
    column_titles = []
    if head is not None:
        for th in head.iter(f"{{{namespace}}}th"):
            text = ""
            for elem in th.findall(".//*"):
                if elem.text is not None:
                    try:
                        text = text + elem.text
                    except (AttributeError, TypeError):
                        pass
            text = re.sub(' {2,}', ' ', re.sub("\n|\u200b", " ", text).strip())
            column_titles.append(text)

    if column_titles == COLUMNS:
        body = table.find(f"{{{namespace}}}tbody")
        if body is not None:
            for tr in body.iter(f"{{{namespace}}}tr"):
                vals = []
                column = 0
                for td in tr.iter(f"{{{namespace}}}td"):
                    text = ""
                    for elem in td.findall(".//*"):
                        if elem.text is not None:
                            try:
                                text = text + elem.text
                            except (AttributeError, TypeError):
                                pass
                    text = re.sub(' {2,}', ' ', re.sub("\n|\u200b", " ", text).strip())
                    vals.append(text)
                tag = str_to_tags(vals[0])
                desc = vals[2].replace(" ", "")
                first = 0

                try:
                    while tag[first] in tags:
                        first += 1
                except IndexError:
                    first -= 1
                init_tag = tag[first]
                alt_tag = tag[first + 1:]
                tags[init_tag] = Tag(vals[1], desc, init_tag[0], init_tag[1], alternative_tags=alt_tag)

###################################################
# STEP 2

tags_xml = Path(__file__).parent / "part03.xml"
tree = ET.parse(tags_xml)
root = tree.getroot()
namespace = root.tag[1:].split("}")[0]

COLUMNS = ["Attribute Name", "Tag", "Type", "Attribute Description"]
ALT_COLUMNS = ["Attribute Name", "Tag", "Type", "Description"]

tables: dict[str, Table] = {}

for table in root.iter(f'{{{namespace}}}table'):
    label = table.get("label")

    if label is not None and label[:2] != "5.":
        head = table.find(f"{{{namespace}}}thead")
        if head is not None:
            column_titles = []
            for th in head.iter(f"{{{namespace}}}th"):
                text = ""
                for elem in th.findall(".//*"):
                    if elem.text is not None:
                        try:
                            text = text + elem.text
                        except (AttributeError, TypeError):
                            pass
                text = re.sub(' {2,}', ' ', re.sub("\n|\u200b", " ", text).strip())
                column_titles.append(text)
            if column_titles == COLUMNS or column_titles == ALT_COLUMNS:
                tables[label] = Table()

for table in root.iter(f'{{{namespace}}}table'):
    label = table.get("label")
    if label in tables:
        body = table.find(f"{{{namespace}}}tbody")
        if body is not None:
            levels: dict[int, Tag | Table] = {}
            for tr in body.iter(f"{{{namespace}}}tr"):
                vals = []
                current_row: Table | Tag | None = None
                for td in tr.iter(f"{{{namespace}}}td"):
                    text = ""
                    for elem in td.findall(".//*"):
                        if elem.text is not None:
                            try:
                                text = text + elem.text
                            except (AttributeError, TypeError):
                                pass
                    text = re.sub(' {2,}', ' ', re.sub("\n|\u200b", " ", text).strip())
                    vals.append(text)
                stripped_name = vals[0].lstrip(">")
                level = len(vals[0]) - len(stripped_name)
                stripped_name = stripped_name.strip()
                if "Include" in vals[0]:
                    for ref in tr.iter(f"{{{namespace}}}xref"):
                        tab_ref = ref.get("linkend")
                        if tab_ref is not None and tab_ref[:6] == "table_":
                            if tab_ref[6:] not in tables:
                                print(tab_ref[6:])
                            else:
                                current_row = tables[tab_ref[6:]]
                        break
                elif len(vals) == 4:
                    tag = str_to_tags(vals[1])
                    current_row = tags[tag[0]]
                    try:
                        c = 1
                        while (current_row.name.lower() != stripped_name.lower()
                               and current_row.keyword.lower() != stripped_name.replace(" ", "").lower()):
                            current_row = tags[tag[c]]
                            c += 1
                    except IndexError:
                        current_row = None
                if current_row is not None:
                    if level > 0:
                        seq = levels[level - 1]
                        if not isinstance(seq, Tag):
                            n = -1
                            new_seq = seq.rows[n]
                            while not isinstance(new_seq, Tag):
                                n -= 1
                                new_seq = seq.rows[n]
                            seq = new_seq
                        current_row.add_parents(seq.get())
                    if current_row is not tables[label]:
                        if level == 0:
                            tables[label].rows.append(current_row)
                        elif level > 0:
                            tables[label].sub_rows.append(current_row)

                    levels[level] = current_row

##########################################
# STEP 3

IOD_COLUMNS = ["IE", "Module", "Reference", "Usage"]
FUNC_GROUP_COLUMNS = ["Functional Group Macro", "Section", "Usage"]

MODALITY_TABLES = {
    "A.2-1": "XRAY",
    "A.14-1": "XRAY",
    "A.16-1": "XRAY",
    "A.26-1": "XRAY",
    "A.27-1": "XRAY",
    "A.28-1": "XRAY",
    "A.47-1": "XRAY",
    "A.47-2": "XRAY",
    "A.48-1": "XRAY",
    "A.48-2": "XRAY",


    "A.3-1": "CT",
    "A.38-1": "CT",
    "A.38-2": "CT",


    "A.5-1": "Nuclear Medicine",
    "A.21.3-1": "Nuclear Medicine",
    "A.56-1": "Nuclear Medicine",
    "A.56-2": "Nuclear Medicine",


    "A.6-1": "Ultrasound",
    "A.7-1": "Ultrasound",
    "A.59-1": "Ultrasound",
    "A.59-2": "Ultrasound",


    "A.4-1": "MRI",
    "A.36-1": "MRI",
    "A.36-2": "MRI",
    "A.36-3": "MRI",
    "A.36-4": "MRI",
    "A.36-5": "MRI", }

for table in root.iter(f'{{{namespace}}}table'):
    label = table.get("label")

    if label is not None and label[:2] != "5.":
        head = table.find(f"{{{namespace}}}thead")
        if head is not None:
            column_titles = []
            for th in head.iter(f"{{{namespace}}}th"):
                text = ""
                for elem in th.findall(".//*"):
                    if elem.text is not None:
                        try:
                            text = text + elem.text
                        except (AttributeError, TypeError):
                            pass
                text = re.sub(' {2,}', ' ', re.sub("\n|\u200b", " ", text).strip())
                column_titles.append(text)
            if column_titles == IOD_COLUMNS and label in MODALITY_TABLES:
                modality = MODALITY_TABLES[label]
                body = table.find(f"{{{namespace}}}tbody")
                if body is not None:
                    for tr in body.iter(f"{{{namespace}}}tr"):
                        for ref in tr.iter(f"{{{namespace}}}xref"):
                            sect_ref = ref.get("linkend")
                            if sect_ref is not None and sect_ref[:5] == "sect_":
                                sect_tables = section_tables(root, sect_ref[5:])
                                for t in sect_tables:
                                    if t in tables:
                                        tables[t].add_modality(modality)
                            break

            elif column_titles == FUNC_GROUP_COLUMNS:
                if label in MODALITY_TABLES:
                    modality = MODALITY_TABLES[label]
                else:
                    modality = None
                body = table.find(f"{{{namespace}}}tbody")
                if body is not None:
                    for tr in body.iter(f"{{{namespace}}}tr"):
                        for ref in tr.iter(f"{{{namespace}}}xref"):
                            sect_ref = ref.get("linkend")
                            if sect_ref is not None and sect_ref[:5] == "sect_":
                                sect_tables = section_tables(root, sect_ref[5:])
                                for t in sect_tables:
                                    if t in tables:
                                        tables[t].add_parents((0x5200, 0x9230), True)
                                        tables[t].add_parents((0x5200, 0x9229))
                                        if modality is not None:
                                            tables[t].add_modality(modality)
                            break

for _, t in tags.items():
    t.set_parent_modalities(tags, [])

##############################################
# STEP 4


current_folder = Path(__file__).resolve().parent / "dcm_tags"
current_folder.mkdir(parents=True, exist_ok=True)

git_file = open(current_folder / ".gitignore", "w+")
git_file.write("*")
git_file.close()

dcm_file = open(current_folder / "all_tags.py", "w+")
xray_file = open(current_folder / "xray_tags.py", "w+")
ct_file = open(current_folder / "ct_tags.py", "w+")
nuc_med_file = open(current_folder / "nuc_med_tags.py", "w+")
us_file = open(current_folder / "us_tags.py", "w+")
mri_file = open(current_folder / "mri_tags.py", "w+")

init_text = "from pumpia.file_handling.dicom_tags import Tag, TagLink\n\n"

dcm_file.write(init_text)
xray_file.write(init_text)
ct_file.write(init_text)
nuc_med_file.write(init_text)
us_file.write(init_text)
mri_file.write(init_text)

dcm_file.write('class DicomTags():\n    """Class containing all DICOM Tags as class attributes."""\n')
xray_file.write('class XRAYTags():\n    """Class containing X-ray DICOM Tags as class attributes."""\n')
ct_file.write('class CTTags():\n    """Class containing CT DICOM Tags as class attributes."""\n')
nuc_med_file.write('class NucMedTags():\n    """Class containing Nuclear Medicine DICOM Tags as class attributes."""\n')
us_file.write('class USTags():\n    """Class containing Ultrasound DICOM Tags as class attributes."""\n')
mri_file.write('class MRTags():\n    """Class containing MRI DICOM Tags as class attributes."""\n')


def write_to_files(tag: Tag, chain: list[Tag]):
    if tag not in chain:
        chain.append(tag)
        for p in tag.parents:
            write_to_files(tags[p], chain)

        if not tag.written and tag.keyword != "":
            name = ascii(tag.name)
            keyword = tag.keyword
            group = f"0x{tag.group:04X}"
            element = f"0x{tag.element:04X}"

            if len(tag.parents) > 0:
                parents = ", ["
                for p, l in tag.parents.items():
                    p_kw = tags[p].keyword
                    if l:
                        parents += f"TagLink({p_kw}, {l}),"
                    else:
                        parents += f"TagLink({p_kw}),"
                parents += "]"
            else:
                parents = ""

            if len(tag.alternative_tags) > 0:
                alternative_tags = ", ["
                for a in tag.alternative_tags:
                    alternative_tags += f"(0x{a[0]:04X}, 0x{a[1]:04X}),"
                alternative_tags += "]"
                if parents == "":
                    parents = ", []"
            else:
                alternative_tags = ""

            text = f'    {keyword} = Tag({name}, "{keyword}", {group}, {element}{parents}{alternative_tags})\n'
            dcm_file.write(text)
            if 'XRAY' in tag.modalities:
                xray_file.write(text)
            if 'CT' in tag.modalities:
                ct_file.write(text)
            if 'Nuclear Medicine' in tag.modalities:
                nuc_med_file.write(text)
            if 'Ultrasound' in tag.modalities:
                us_file.write(text)
            if 'MRI' in tag.modalities:
                mri_file.write(text)

            tag.written = True


for _, t in tags.items():
    write_to_files(t, [])

dcm_file.close()
xray_file.close()
ct_file.close()
nuc_med_file.close()
us_file.close()
mri_file.close()
