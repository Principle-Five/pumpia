The script dicom_miner.py uses parts 3 and 6 of the DICOM standard to create the Tags in PumpIA.
When it is run it creates a folder called dcm_tags in the folder it is ran in, the files in dcm_tags can then be copied to pumpia/file_handling/dicom_tags for use in PumpIA.
This script is not designed to be used by general PumpIA users, however it is included for interest and in the spirit of open source.

Step 1: Use Part 6 to create tags
-----------------------------------------------------------
Step 2: Use tables in part 3 to create links to parent tags

IGNORE SECTION 5

> used for nesting, multiple indicate more nesting
e.g.:
sequence
>item in sequence
>sub sequence
>>sub sequence item

Table layouts:
|Attribute Name|Tag|Type|Attribute Description|

To Include other table:
Include Table 8.8-1a
<emphasis role="italic">Include <xref linkend="table_8.8-1a" xrefstyle="select: label"/>
<emphasis role="italic">&gt;Include <xref linkend="table_8.8-1a" xrefstyle="select: label"/>
------------------------------------------------------------------------------------------------------
Step 3: Use IOD tables in part 3 to create modalities and link Functional Group Macros to be per frame

IOD (modality) tables:
|IE|Module|Reference|Usage|
|Functional Group Macro|Section|Usage| --- for Per-Frame Functional Groups Sequence

Reference/Section contain a table each to be included in the relevant modality
Functional Group Macros can be per frame

Key modality tables:
XRAY:
A.2-1. Computed Radiography Image IOD Modules
A.14-1. X-Ray Angiographic Image IOD Modules
A.16-1. X-Ray Radiofluoroscopic Image IOD Modules
A.26-1. Digital X-Ray Image IOD Modules
A.27-1. Digital Mammography X-Ray Image IOD Modules
A.28-1. Digital Intra-Oral X-Ray Image IOD Modules
A.47-1. Enhanced XA Image IOD Modules
A.47-2. Enhanced XA Image Functional Group Macros
A.48-1. Enhanced XRF Image IOD Modules
A.48-2. Enhanced XRF Image Functional Group Macros

CT:
A.3-1. CT Image IOD Modules
A.38-1. Enhanced CT Image IOD Modules
A.38-2. Enhanced CT Image Functional Group Macros

Nuclear Medicine:
A.5-1. Nuclear Medicine Image IOD Modules
A.21.3-1. Positron Emission Tomography Image IOD Modules
A.56-1. Enhanced PET Image IOD Modules
A.56-2. Enhanced PET Image Functional Group Macros

Ultrasound
A.6-1. Ultrasound Image IOD Modules
A.7-1. Ultrasound Multi-frame Image IOD Modules
A.59-1. Enhanced US Volume IOD Modules
A.59-2. Enhanced US Volume Functional Group Macros

MRI
A.4-1. MR Image IOD Modules
A.36-1. Enhanced MR Image IOD Modules
A.36-2. Enhanced MR Image Functional Group Macros
A.36-3. MR Spectroscopy IOD Modules
A.36-4. MR Spectroscopy Functional Group Macros
A.36-5. Enhanced MR Color Image IOD Modules
------------------------------------------------------------------------------------------------------
Step 4: write to files
